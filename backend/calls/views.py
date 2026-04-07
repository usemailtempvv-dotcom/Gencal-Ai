"""
Views for handling Twilio webhooks and API endpoints.
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from django.conf import settings
from .models import CallLog
import logging
import re
import json
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Initialize program query services lazily
_program_retriever = None
_entity_extractor = None
_response_formatter = None
_scholarship_retriever = None

def _get_program_services():
    """Get or initialize program query services."""
    global _program_retriever, _entity_extractor, _response_formatter

    # If any service is missing, re-initialize all services atomically.
    if _program_retriever is None or _entity_extractor is None or _response_formatter is None:
        try:
            from services.data_retriever import ProgramDataRetriever
            from services.entity_extractor import EntityExtractor
            from services.response_formatter import ProgramResponseFormatter

            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'Programs.csv',
                backend_dir / 'Data' / 'programs.csv',
                Path('Data/Programs.csv'),
                Path('Data/programs.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                raise FileNotFoundError('Programs CSV not found in backend/Data (checked Programs.csv and programs.csv).')

            retriever = ProgramDataRetriever(str(csv_path))

            # Reuse already-loaded dataframe (with encoding fallback).
            extractor = EntityExtractor(retriever.df.copy())
            formatter = ProgramResponseFormatter()

            # Commit all initialized services together.
            _program_retriever = retriever
            _entity_extractor = extractor
            _response_formatter = formatter
            
            logger.info('Program query services initialized successfully')
        except Exception as e:
            _program_retriever = None
            _entity_extractor = None
            _response_formatter = None
            logger.warning(f'Failed to initialize program services: {str(e)}')
            return None, None, None
    
    return _program_retriever, _entity_extractor, _response_formatter


def _get_scholarship_services():
    """Get or initialize scholarship query services."""
    global _scholarship_retriever

    if _scholarship_retriever is None:
        try:
            from services.data_retriever import ScholarshipPolicyRetriever
            from services.response_formatter import ProgramResponseFormatter

            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'Scholarship_policy.csv',
                backend_dir / 'Data' / 'scholarship_policy.csv',
                Path('Data/Scholarship_policy.csv'),
                Path('Data/scholarship_policy.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                raise FileNotFoundError('Scholarship policy CSV not found in backend/Data.')

            _scholarship_retriever = ScholarshipPolicyRetriever(str(csv_path))
            logger.info('Scholarship services initialized successfully')
        except Exception as e:
            _scholarship_retriever = None
            logger.warning(f'Failed to initialize scholarship services: {str(e)}')
            return None, None

    try:
        from services.response_formatter import ProgramResponseFormatter
        formatter = _response_formatter or ProgramResponseFormatter()
    except Exception:
        formatter = None

    return _scholarship_retriever, formatter


def _normalize_program_intent(intent_label):
    """Map model intents to program-query intent names used by response pipeline."""
    if not intent_label:
        return ''

    label = str(intent_label).strip()
    mapping = {
        'fee_inquiry': 'ask_fee',
        'admission_fee': 'ask_admission_fee',
        'admission_last_date': 'ask_admission_fee',
        'timing_info': 'ask_duration',
        'programs': 'list_programs',
        'general_info': 'full_info',
    }
    return mapping.get(label, label)


def _normalize_scholarship_intent(intent_label):
    """Map model intents to scholarship-query intent names."""
    if not intent_label:
        return ''

    label = str(intent_label).strip()
    mapping = {
        'scholarship': 'ask_scholarship_summary',
        'Scholarship_general': 'ask_scholarship_summary',
        'merit_scholarship': 'ask_scholarship_details',
        'need_based_Scholarships': 'ask_scholarship_details',
        'kinship_scholarship': 'ask_scholarship_details',
        'sports_scholarship': 'ask_scholarship_details',
        'hafiz_scholarship': 'ask_scholarship_details',
        'employee_scholarship': 'ask_scholarship_details',
        'percentage_based_scholarship': 'ask_scholarship_details',
        'city_based_scholarship': 'ask_scholarship_details',
        'ask_scholarship': 'ask_scholarship_summary',
    }
    return mapping.get(label, label)


def _process_program_query(text, intent_label):
    """Process program-related queries and generate responses."""
    try:
        retriever, extractor, formatter = _get_program_services()
        if not retriever or not extractor or not formatter:
            return {'program_data': None, 'natural_response': None}
        
        # Extract entities from transcript
        extraction = extractor.extract_program_and_level(text)
        program_name = extraction['program']
        level = extraction['level']
        faculty = extraction.get('faculty')
        program_match_type = extraction.get('program_match_type')
        
        program_data = None
        natural_response = None
        
        normalized_intent = _normalize_program_intent(intent_label)
        q = (text or '').lower()

        # Conversation-intent helpers for program exploration.
        asks_program_count = any(k in q for k in ['how many programs', 'number of programs', 'program count'])
        asks_degree_count = any(k in q for k in [
            'how many degree',
            'how many degrees',
            'number of degree',
            'number of degrees',
            'how many program',
        ])
        asks_offered = any(k in q for k in ['is ', 'do you offer', 'offered', 'available']) and program_name is not None
        asks_faculty_list = 'faculty' in q and level is not None and faculty is None
        asks_programs_in_faculty = (
            faculty is not None and (
                'program' in q or 'what are in' in q or 'which are in' in q or 'list' in q or normalized_intent == 'list_programs'
            )
        )

        if asks_program_count:
            levels = retriever.get_all_levels()
            natural_response = formatter.format_ask_level_first(levels)
            return {
                'program_name': None,
                'level': None,
                'faculty': None,
                'intent_used': 'ask_program_count',
                'program_data': None,
                'natural_response': natural_response,
                'follow_up': {'type': 'choose_level', 'levels': levels},
            }

        if asks_offered:
            strong_match = program_match_type in {'exact', 'abbreviation', 'token_overlap'}
            offered = retriever.is_program_offered(program_name, level) if (program_name and strong_match) else False
            natural_response = formatter.format_program_offered(program_name, offered)
            offered_data = retriever.get_program_by_name(program_name, level) if offered else None
            return {
                'program_name': program_name,
                'level': level,
                'faculty': faculty,
                'intent_used': 'check_program_offered',
                'program_data': offered_data,
                'natural_response': natural_response,
                'follow_up': None,
            }

        if asks_degree_count and level and faculty:
            programs = retriever.get_programs_by_level_and_faculty(level, faculty)
            natural_response = formatter.format_program_count_for_level_faculty(level, faculty, programs)
            return {
                'program_name': None,
                'level': level,
                'faculty': faculty,
                'intent_used': 'count_programs_by_faculty',
                'program_data': {'level': level, 'faculty': faculty, 'program_count': len(programs), 'programs': programs},
                'natural_response': natural_response,
                'follow_up': None,
            }

        if asks_faculty_list:
            faculties = retriever.get_faculties_by_level(level)
            natural_response = formatter.format_faculties_for_level(level, faculties)
            return {
                'program_name': None,
                'level': level,
                'faculty': None,
                'intent_used': 'list_faculties',
                'program_data': {'level': level, 'faculties': faculties},
                'natural_response': natural_response,
                'follow_up': {'type': 'choose_faculty', 'level': level, 'faculties': faculties},
            }

        if asks_programs_in_faculty and level:
            programs = retriever.get_programs_by_level_and_faculty(level, faculty)
            natural_response = formatter.format_programs_for_level_faculty(level, faculty, programs)
            return {
                'program_name': None,
                'level': level,
                'faculty': faculty,
                'intent_used': 'list_programs_by_faculty',
                'program_data': {'level': level, 'faculty': faculty, 'programs': programs},
                'natural_response': natural_response,
                'follow_up': None,
            }

        # Route based on intent
        if normalized_intent in ['ask_fee', 'ask_admission_fee', 'ask_duration', 'ask_semesters', 'full_info']:
            if program_name:
                program_data = retriever.get_program_by_name(program_name, level)
                natural_response = formatter.format_response(normalized_intent, program_data, level)
            else:
                natural_response = formatter.format_unable_to_find_program(program_name or 'unknown program')

        elif normalized_intent == 'list_programs':
            if level:
                if faculty:
                    programs_list = retriever.get_programs_by_level_and_faculty(level, faculty)
                    natural_response = formatter.format_programs_for_level_faculty(level, faculty, programs_list)
                    program_data = {'level': level, 'faculty': faculty, 'programs': programs_list}
                else:
                    faculties = retriever.get_faculties_by_level(level)
                    natural_response = formatter.format_faculties_for_level(level, faculties)
                    program_data = {'level': level, 'faculties': faculties}
            else:
                levels = retriever.get_all_levels()
                natural_response = formatter.format_ask_level_first(levels)
                program_data = {'levels': levels}
        
        return {
            'program_name': program_name,
            'level': level,
            'faculty': faculty,
            'intent_used': normalized_intent,
            'program_data': program_data,
            'natural_response': natural_response,
        }
    
    except Exception as e:
        logger.error(f'Program query processing failed: {str(e)}')
        return {'program_data': None, 'natural_response': None}


def _process_scholarship_query(text, intent_label):
    """Process scholarship-related queries and generate responses."""
    try:
        retriever, formatter = _get_scholarship_services()
        if not retriever or not formatter:
            return {'scholarship_data': None, 'natural_response': None}

        q = (text or '').lower()
        level = retriever.extract_level(text)

        category = retriever.extract_category(text)
        normalized_intent = _normalize_scholarship_intent(intent_label)

        asks_count = any(k in q for k in ['how many scholarship', 'how many scholarships', 'number of scholarship', 'number of scholarships', 'scholarship count'])
        asks_documents = any(k in q for k in ['document', 'documents', 'papers required', 'required docs', 'requirements'])
        asks_list = any(k in q for k in ['list', 'show', 'available', 'what scholarships', 'which scholarships'])

        if asks_documents and category:
            policies = retriever.get_category_details(category, level)
            natural_response = formatter.format_scholarship_documents(policies, category, level)
            return {
                'scholarship_data': policies,
                'scholarship_category': category,
                'level': level,
                'intent_used': 'ask_scholarship_documents',
                'natural_response': natural_response,
                'follow_up': None,
            }

        if category:
            policies = retriever.get_category_details(category, level)
            if asks_documents:
                natural_response = formatter.format_scholarship_documents(policies, category, level)
                intent_used = 'ask_scholarship_documents'
            else:
                natural_response = formatter.format_scholarship_details(policies, category, level)
                intent_used = 'ask_scholarship_details'
            return {
                'scholarship_data': policies,
                'scholarship_category': category,
                'level': level,
                'intent_used': intent_used,
                'natural_response': natural_response,
                'follow_up': None,
            }

        if asks_list:
            policies = retriever.get_policies(level=level)
            natural_response = formatter.format_scholarship_list(policies, level=level)
            return {
                'scholarship_data': policies,
                'scholarship_category': None,
                'level': level,
                'intent_used': 'ask_scholarship_list',
                'natural_response': natural_response,
                'follow_up': {'type': 'choose_scholarship_category', 'level': level, 'categories': retriever.get_summary(level=level).get('categories', [])},
            }

        if asks_count or normalized_intent == 'ask_scholarship_summary':
            summary = retriever.get_summary(level=level)
            natural_response = formatter.format_scholarship_summary(summary, level=level)
            return {
                'scholarship_data': summary,
                'scholarship_category': None,
                'level': level,
                'intent_used': 'ask_scholarship_summary',
                'natural_response': natural_response,
                'follow_up': {'type': 'choose_scholarship_category', 'level': level, 'categories': summary.get('categories', [])},
            }

        summary = retriever.get_summary(level=level)
        natural_response = formatter.format_scholarship_summary(summary, level=level)
        return {
            'scholarship_data': summary,
            'scholarship_category': category,
            'level': level,
            'intent_used': normalized_intent or 'ask_scholarship_summary',
            'natural_response': natural_response,
            'follow_up': {'type': 'choose_scholarship_category', 'level': level, 'categories': summary.get('categories', [])},
        }

    except Exception as e:
        logger.error(f'Scholarship query processing failed: {str(e)}')
        return {'scholarship_data': None, 'natural_response': None}

# Global variable to cache the custom intent model
_custom_intent_model = None
_custom_intent_tokenizer = None
_custom_intent_model_labels = None
INTENT_CONFIDENCE_THRESHOLD = 0.25


def _resolve_intent_model_path():
    """Find the newest available trained intent model directory."""
    # Optional manual override for production deployments.
    override = os.getenv('INTENT_MODEL_DIR')
    candidates = []
    if override:
        candidates.append(Path(override))

    backend_dir = Path(__file__).resolve().parent.parent
    repo_root = backend_dir.parent

    candidates.extend([
        repo_root / 'Models' / 'trained_intent_model',
        repo_root / 'Models traning' / 'intend_detection' / 'trained_intent_model',
        Path.cwd() / 'Models' / 'trained_intent_model',
        Path.cwd() / 'Models traning' / 'intend_detection' / 'trained_intent_model',
        Path(os.path.expanduser('~/OneDrive/Desktop/Gencall ai/Models/trained_intent_model')),
        Path(os.path.expanduser('~/OneDrive/Desktop/Gencall ai/Models traning/intend_detection/trained_intent_model')),
    ])

    available = []
    for path in candidates:
        model_file = path / 'model.safetensors'
        if model_file.exists():
            try:
                available.append((model_file.stat().st_mtime, path))
            except Exception:
                available.append((0, path))

    if not available:
        return None

    available.sort(key=lambda item: item[0], reverse=True)
    return str(available[0][1])


def _keyword_intent_override(text):
    """Route obvious domain phrases to stable intents before model inference."""
    t = (text or '').lower()
    if not t:
        return None

    if 'merit' in t and 'scholarship' in t:
        return {'label': 'merit_scholarship', 'confidence': 0.95}
    if ('need' in t and 'scholarship' in t) or 'need-based' in t or 'financial aid' in t:
        return {'label': 'need_based_Scholarships', 'confidence': 0.93}
    if 'kinship' in t or 'sibling scholarship' in t:
        return {'label': 'kinship_scholarship', 'confidence': 0.93}
    if 'sports scholarship' in t or ('sports' in t and 'scholarship' in t):
        return {'label': 'sports_scholarship', 'confidence': 0.93}
    if 'hafiz scholarship' in t or ('hafiz' in t and 'scholarship' in t):
        return {'label': 'hafiz_scholarship', 'confidence': 0.93}
    if 'scholarship' in t:
        return {'label': 'Scholarship_general', 'confidence': 0.9}

    return None

def _load_custom_intent_model():
    """Load the custom DistilBERT intent detection model."""
    global _custom_intent_model, _custom_intent_tokenizer, _custom_intent_model_labels
    
    if _custom_intent_model is not None:
        return _custom_intent_model, _custom_intent_tokenizer, _custom_intent_model_labels
    
    try:
        # Lazy imports to avoid loading transformers if custom model not available
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        model_path = _resolve_intent_model_path()
        
        if not model_path:
            logger.warning('Custom intent model not found, will use heuristics')
            return None, None, None
        
        logger.info(f'Loading custom intent model from {model_path}')
        _custom_intent_tokenizer = AutoTokenizer.from_pretrained(model_path)
        _custom_intent_model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            dtype=torch.float32,
            device_map='cpu'
        )
        _custom_intent_model.eval()
        
        # Load label mapping
        label_path = os.path.join(model_path, 'id2label.json')
        if os.path.exists(label_path):
            with open(label_path, 'r', encoding='utf-8') as f:
                id2label = json.load(f)
                _custom_intent_model_labels = {int(k): v for k, v in id2label.items()}
        
        logger.info('Custom intent model loaded successfully')
        return _custom_intent_model, _custom_intent_tokenizer, _custom_intent_model_labels
    except Exception as e:
        logger.error(f'Failed to load custom intent model: {str(e)}')
        return None, None, None


def _safe_json_parse(text):
    """Parse JSON content from model output with fallback extraction."""
    if not text:
        return None

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _normalize_groq_model(model_name):
    """Map friendly/alias model names to valid Groq model IDs."""
    if not model_name:
        return 'llama-3.3-70b-versatile'

    normalized = model_name.strip().lower()
    if normalized in ('llama-3.3-70b', 'llama3.3-70b', 'llama-3.3-70b-versatile'):
        return 'llama-3.3-70b-versatile'
    return model_name


def _clamp_confidence(value):
    """Convert confidence to float in [0,1]."""
    try:
        if isinstance(value, str):
            value = value.strip().replace('%', '')
            value = float(value)
            if value > 1:
                value = value / 100.0
        value = float(value)
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value
    except Exception:
        return 0.0


def _heuristic_intent(text):
    t = (text or '').lower()
    override = _keyword_intent_override(t)
    if override:
        return override

    if any(w in t for w in ['admission', 'apply', 'application', 'enroll']):
        return {'label': 'apply_admission', 'confidence': 0.62}
    if any(w in t for w in ['last date', 'deadline', 'closing date']):
        return {'label': 'admission_last_date', 'confidence': 0.62}
    if any(w in t for w in ['fee', 'tuition', 'charges', 'cost', 'kitna']):
        return {'label': 'fee_inquiry', 'confidence': 0.62}
    if any(w in t for w in ['document', 'documents', 'required docs', 'certificate']):
        return {'label': 'documents_inquiry', 'confidence': 0.62}
    if any(w in t for w in ['timing', 'time', 'schedule', 'open', 'close', 'office hours']):
        return {'label': 'timing_info', 'confidence': 0.62}
    if any(w in t for w in ['campus', 'location', 'address', 'where are you']):
        return {'label': 'campus_info', 'confidence': 0.62}
    if any(w in t for w in ['university', 'about university', 'about your university']):
        return {'label': 'University_Info', 'confidence': 0.6}
    if any(w in t for w in ['agent', 'human', 'representative', 'person']):
        return {'label': 'human_transfer', 'confidence': 0.64}
    return {'label': 'unknown', 'confidence': 0.35}


def _heuristic_emotion(text):
    t = (text or '').lower()
    if any(w in t for w in ['angry', 'ghussa', 'frustrated', 'annoyed']):
        return {'label': 'frustrated', 'confidence': 0.65}
    if any(w in t for w in ['happy', 'great', 'awesome', 'khush']):
        return {'label': 'happy', 'confidence': 0.65}
    if any(w in t for w in ['sad', 'upset', 'dukhi']):
        return {'label': 'sad', 'confidence': 0.6}
    if any(w in t for w in ['urgent', 'worried', 'anxious', 'tension']):
        return {'label': 'anxious', 'confidence': 0.6}
    return {'label': 'neutral', 'confidence': 0.55}


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _voice_emotion_heuristic(voice_features):
    """Estimate emotion using voice intensity/pattern cues from microphone signal."""
    if not isinstance(voice_features, dict):
        return {'label': 'unknown', 'confidence': 0.0}

    rms_avg = _safe_float(voice_features.get('rms_avg'))
    rms_max = _safe_float(voice_features.get('rms_max'))
    peak_max = _safe_float(voice_features.get('peak_max'))
    zcr_avg = _safe_float(voice_features.get('zcr_avg'))
    sample_count = int(_safe_float(voice_features.get('samples', 0), 0))

    if sample_count < 3:
        return {'label': 'unknown', 'confidence': 0.0}

    # Louder and more unstable speech often maps to stress/frustration.
    if (rms_avg >= 0.12 and peak_max >= 0.7) or (rms_max >= 0.2 and zcr_avg >= 0.13):
        return {'label': 'frustrated', 'confidence': 0.74}

    # High energy with moderate variation often sounds excited.
    if rms_avg >= 0.09 and zcr_avg >= 0.1:
        return {'label': 'excited', 'confidence': 0.69}

    # Very low energy often sounds sad/tired.
    if rms_avg <= 0.028 and peak_max <= 0.2:
        return {'label': 'sad', 'confidence': 0.64}

    # Calm and stable speech is neutral/polite.
    if 0.03 <= rms_avg <= 0.075 and zcr_avg <= 0.09:
        return {'label': 'neutral', 'confidence': 0.61}

    return {'label': 'unknown', 'confidence': 0.0}


def _merge_emotion_signals(text_emotion, voice_emotion):
    """Merge text and voice emotion predictions, preferring stronger non-neutral signal."""
    text_label = (text_emotion or {}).get('label', 'unknown')
    text_conf = _clamp_confidence((text_emotion or {}).get('confidence', 0.0))
    voice_label = (voice_emotion or {}).get('label', 'unknown')
    voice_conf = _clamp_confidence((voice_emotion or {}).get('confidence', 0.0))

    if voice_label not in ('unknown', 'neutral') and voice_conf >= max(0.6, text_conf + 0.08):
        return {'label': voice_label, 'confidence': voice_conf, 'source': 'voice'}

    if text_label not in ('unknown',) and text_conf > 0:
        source = 'text+voice' if voice_conf > 0 else 'text'
        return {'label': text_label, 'confidence': text_conf, 'source': source}

    if voice_label not in ('unknown',):
        return {'label': voice_label, 'confidence': voice_conf, 'source': 'voice'}

    return {'label': 'neutral', 'confidence': 0.5, 'source': 'fallback'}


def _normalize_supported_stt_language(detected_language, text):
    """Return only supported STT languages: en or ur."""
    raw = (detected_language or '').strip().lower()
    lang = raw.split('-')[0] if raw else ''
    transcript = text or ''

    # Urdu in Arabic script.
    if re.search(r'[\u0600-\u06FF]', transcript):
        return 'ur'

    # Hindi and Devanagari-script outputs are forced to Urdu for this app.
    if lang in {'hi', 'mr', 'ne'} or re.search(r'[\u0900-\u097F]', transcript):
        return 'ur'

    if lang == 'ur':
        return 'ur'
    if lang == 'en':
        return 'en'

    # Roman Urdu hints.
    roman_urdu_markers = (
        'mera', 'meri', 'mujhe', 'aap', 'ap', 'hum', 'hain', 'nahi', 'nahin',
        'kiya', 'kya', 'kaise', 'kyun', 'masla', 'madad', 'admission', 'scholarship'
    )
    lower_text = transcript.lower()
    if any(marker in lower_text for marker in roman_urdu_markers):
        return 'ur'

    # Default only to supported set.
    return 'en'


def _translate_urdu_to_english(client, provider, nlu_model, text):
    """Translate Urdu transcript to English text."""
    if not text:
        return ''

    try:
        if provider == 'groq':
            result = client.chat.completions.create(
                model=nlu_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a translator. Translate Urdu to natural English. Return only translated text.',
                    },
                    {
                        'role': 'user',
                        'content': f'Translate this Urdu text to English:\n{text}',
                    },
                ],
                temperature=0,
            )
            return (result.choices[0].message.content or '').strip() if result.choices else ''

        result = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a translator. Translate Urdu to natural English. Return only translated text.',
                },
                {
                    'role': 'user',
                    'content': f'Translate this Urdu text to English:\n{text}',
                },
            ],
            temperature=0,
        )
        return (result.choices[0].message.content or '').strip() if result.choices else ''
    except Exception as e:
        logger.warning(f'Urdu to English translation failed: {str(e)}')
        return ''


def _stt_domain_prompt():
    """Short domain hint for better transcription of university terms."""
    return (
        'This audio is from university calls. Common terms include: '
        'BS Computer Science, BS Software Engineering, Data Science, Cyber Security, '
        'admission, semester, fee, scholarship, merit, kinship, alumni, postgraduate, undergraduate.'
    )


def _transcript_quality_score(text, expected_language='auto'):
    """Lightweight quality score for choosing best transcript candidate."""
    t = (text or '').strip()
    if not t:
        return 0.0

    score = min(len(t), 180) / 180.0
    words = [w for w in re.split(r'\s+', t) if w]
    score += 0.2 if len(words) >= 4 else 0.05

    latin_tokens = len(re.findall(r'[A-Za-z]{2,}', t))
    urdu_tokens = len(re.findall(r'[\u0600-\u06FF]+', t))
    repeated_noise = len(re.findall(r'(.)\1{4,}', t))
    junk_chars = len(re.findall(r'[\uFFFD]', t))

    if expected_language == 'en':
        score += min(0.2, latin_tokens * 0.02)
        if urdu_tokens > latin_tokens * 2:
            score -= 0.12
    elif expected_language == 'ur':
        score += min(0.2, urdu_tokens * 0.03)
        if latin_tokens > urdu_tokens * 3 and urdu_tokens == 0:
            score -= 0.08
    else:
        # Mixed/call center speech often includes both English and Urdu terms.
        score += min(0.1, (latin_tokens + urdu_tokens) * 0.01)

    score -= min(0.2, repeated_noise * 0.06)
    score -= min(0.2, junk_chars * 0.03)
    return max(0.0, min(1.0, score))


def _run_robust_transcription(client, model, file_name, audio_bytes, content_type, requested_language='auto'):
    """Transcribe with fallback candidates and pick the best quality output."""

    def _transcribe_candidate(lang_code=None):
        args = {
            'model': model,
            'file': (file_name, audio_bytes, content_type or 'application/octet-stream'),
            'response_format': 'verbose_json',
            'temperature': 0,
            'prompt': _stt_domain_prompt(),
        }
        if lang_code:
            args['language'] = lang_code
        transcript_obj = client.audio.transcriptions.create(**args)
        candidate_text = (getattr(transcript_obj, 'text', '') or '').strip()
        candidate_raw_lang = (getattr(transcript_obj, 'language', '') or '').strip().lower()
        normalized_lang = _normalize_supported_stt_language(candidate_raw_lang, candidate_text)
        expected = lang_code if lang_code in ('en', 'ur') else 'auto'
        quality = _transcript_quality_score(candidate_text, expected_language=expected)
        return {
            'language_requested': lang_code or 'auto',
            'raw_language': candidate_raw_lang,
            'detected_language': normalized_lang,
            'text': candidate_text,
            'quality': quality,
        }

    req = (requested_language or 'auto').strip().lower()
    req = req.split('-')[0] if req else 'auto'
    candidates = []

    # Respect explicit request first.
    if req in ('en', 'ur'):
        candidates.append(_transcribe_candidate(req))
    else:
        candidates.append(_transcribe_candidate(None))

    best = max(candidates, key=lambda c: c['quality'])
    low_quality = best['quality'] < 0.55 or len(best['text'].split()) < 3

    # Only do extra passes when needed to keep average latency low.
    if req == 'auto' and low_quality:
        for forced_lang in ('en', 'ur'):
            try:
                candidates.append(_transcribe_candidate(forced_lang))
            except Exception as e:
                logger.warning(f'STT fallback pass failed for {forced_lang}: {str(e)}')
        best = max(candidates, key=lambda c: c['quality'])

    return best, candidates


def _emotion_style_hint(emotion_label):
    """Map emotion label to conversational tone instruction."""
    label = (emotion_label or '').strip().lower()
    if label in {'angry', 'frustrated'}:
        return 'empathetic, calm, and reassuring'
    if label in {'anxious', 'sad'}:
        return 'supportive, gentle, and confidence-building'
    if label in {'happy', 'excited'}:
        return 'warm, upbeat, and friendly'
    if label in {'polite'}:
        return 'professional, polite, and concise'
    return 'professional, warm, and clear'


def _humanize_response_fast(base_answer, emotion_label='neutral', language='en'):
    """Rewrite answer in a human style while preserving all facts and values."""
    text = (base_answer or '').strip()
    if not text:
        return text

    # Keep large list responses untouched to avoid latency and formatting loss.
    if text.count('\n') > 12 or len(text) > 1400:
        return text

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return text

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url='https://api.groq.com/openai/v1', timeout=2.5)
        model = getattr(settings, 'GROQ_RESPONSE_MODEL', 'llama-3.1-8b-instant')
        style = _emotion_style_hint(emotion_label)
        target_language = 'Urdu' if str(language).lower().startswith('ur') else 'English'

        prompt = (
            'Rewrite the answer to sound human and conversational. '
            'Do not change any facts, numbers, fees, percentages, levels, categories, or documents. '
            'Do not add new information. Keep it concise. '
            f'Use {style} tone. Respond in {target_language}.\n\n'
            f'Original answer:\n{text}'
        )

        result = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a response polishing assistant. Preserve all facts exactly.',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0.25,
            max_tokens=220,
        )

        polished = (result.choices[0].message.content or '').strip() if result.choices else ''
        return polished or text
    except Exception as e:
        logger.warning(f'Humanized response fallback to base answer: {str(e)}')
        return text


@csrf_exempt
@require_http_methods(["POST"])
def incoming_call(request):
    """
    Twilio webhook endpoint for incoming calls.
    This endpoint receives POST requests from Twilio when a call comes in.
    
    Twilio sends the following parameters:
    - CallSid: Unique identifier for the call
    - From: Caller's phone number
    - To: Your Twilio phone number
    - CallStatus: Current status of the call
    """
    # Get call information from Twilio request
    call_sid = request.POST.get('CallSid', '')
    from_number = request.POST.get('From', '')
    to_number = request.POST.get('To', '')
    call_status = request.POST.get('CallStatus', '')
    
    logger.info(f"Incoming call from {from_number} to {to_number}, SID: {call_sid}")
    
    # Save call log to database
    try:
        CallLog.objects.create(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            call_status=call_status,
            direction='inbound'
        )
    except Exception as e:
        logger.error(f"Error saving call log: {str(e)}")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Say greeting message using text-to-speech
    response.say(
        "Hello! This is GenCall AI speaking. Thank you for calling us. We are excited to assist you today.",
        voice='alice',  # Use Alice voice (female, US English)
        language='en-US'
    )
    
    # You can add more actions here:
    # - response.gather() to collect DTMF input
    # - response.record() to record the caller's message
    # - response.dial() to forward the call
    
    # Optional: Play a short pause
    response.pause(length=1)
    
    # Additional message
    response.say(
        "This is a demonstration of our AI-powered call system. Have a great day!",
        voice='alice',
        language='en-US'
    )
    
    # Return TwiML XML response
    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
@require_http_methods(["POST"])
def call_status(request):
    """
    Twilio webhook endpoint for call status updates.
    Twilio can send status updates during the call lifecycle.
    """
    call_sid = request.POST.get('CallSid', '')
    call_status = request.POST.get('CallStatus', '')
    call_duration = request.POST.get('CallDuration', None)
    
    logger.info(f"Call status update for {call_sid}: {call_status}")
    
    # Update call log with status
    try:
        call_log = CallLog.objects.get(call_sid=call_sid)
        call_log.call_status = call_status
        if call_duration:
            call_log.duration = int(call_duration)
        call_log.save()
    except CallLog.DoesNotExist:
        logger.warning(f"Call log not found for SID: {call_sid}")
    except Exception as e:
        logger.error(f"Error updating call log: {str(e)}")
    
    return HttpResponse(status=200)


@api_view(['GET'])
def get_call_logs(request):
    """
    API endpoint to retrieve call logs.
    Returns the latest call logs in JSON format.
    """
    logs = CallLog.objects.all()[:20]  # Get last 20 calls
    
    logs_data = [
        {
            'call_sid': log.call_sid,
            'from_number': log.from_number,
            'to_number': log.to_number,
            'call_status': log.call_status,
            'direction': log.direction,
            'timestamp': log.timestamp.isoformat(),
            'duration': log.duration
        }
        for log in logs
    ]
    
    return Response({'calls': logs_data})


@api_view(['POST'])
def generate_token(request):
    """
    Generate Twilio access token for frontend client.
    This allows the React app to make calls through Twilio.
    """
    try:
        from twilio.jwt.access_token import AccessToken
        from twilio.jwt.access_token.grants import VoiceGrant
        import requests
        from datetime import datetime
        import time
        
        # Get identity from request or use default
        identity = request.data.get('identity', 'user')
        
        # Try multiple time sources to get actual current time (not system time)
        actual_time = None
        time_sources = [
            'http://worldtimeapi.org/api/timezone/Etc/UTC',
            'https://timeapi.io/api/Time/current/zone?timeZone=UTC',
            'http://worldclockapi.com/api/json/utc/now'
        ]
        
        for source in time_sources:
            try:
                response = requests.get(source, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    # Different APIs have different response formats
                    if 'unixtime' in data:
                        actual_time = data['unixtime']
                    elif 'unixTime' in data:
                        actual_time = data['unixTime']
                    elif 'currentFileTime' in data:
                        # WorldClockAPI uses Windows file time
                        actual_time = int(time.time())  # Fallback
                    
                    if actual_time:
                        print(f"[Time Source] Using {source}: {actual_time}")
                        break
            except Exception as e:
                print(f"[Time Source] {source} failed: {e}")
                continue
        
        # If all APIs fail, calculate offset based on known difference
        # System shows Mar 2026, real time is ~Jan 2025 = ~14 months = ~36720000 seconds
        if not actual_time:
            system_time = int(time.time())
            # Apply correction: subtract approximately 14 months
            actual_time = system_time - 36720000
            print(f"[Time Source] All APIs failed. Using corrected time: {actual_time} (system: {system_time})")
        
        # Create access token with actual current time
        token = AccessToken(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_API_KEY_SID,
            settings.TWILIO_API_KEY_SECRET,
            identity=identity,
            ttl=3600,  # 1 hour
            nbf=actual_time  # Use actual current time
        )
        
        # Create a Voice grant and add to token
        voice_grant = VoiceGrant(
            outgoing_application_sid=settings.TWIML_APP_SID,
            incoming_allow=True
        )
        token.add_grant(voice_grant)
        
        jwt_token = token.to_jwt()
        
        # Log token generation
        print(f"[Token Generated] Identity: {identity}, Timestamp: {actual_time}, Length: {len(jwt_token)}")
        
        # Return token to frontend
        return Response({
            'token': jwt_token,
            'identity': identity
        })
    except Exception as e:
        print(f"[Token Error] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def outgoing_call(request):
    """
    TwiML App endpoint for handling outgoing calls from browser.
    This is called when a user makes a call from the frontend using Twilio Client.
    
    The TwiML App forwards the call parameters here, and we return TwiML
    that tells Twilio how to handle the call.
    """
    # Get the phone number to call from the request
    to_number = request.POST.get('To', '')
    from_number = settings.TWILIO_PHONE_NUMBER
    
    logger.info(f"Outgoing browser call to {to_number}")
    
    # Create TwiML response for outgoing call
    response = VoiceResponse()
    
    # Dial the destination number
    if to_number:
        # Use your Twilio number as caller ID
        dial = response.dial(
            caller_id=from_number,
            answer_on_bridge=True
        )
        dial.number(to_number)
    else:
        # No number provided
        response.say(
            "Please specify a phone number to call.",
            voice='alice',
            language='en-US'
        )
    
    logger.info(f"Generated outgoing call TwiML for {to_number}")
    return HttpResponse(str(response), content_type='text/xml')


@api_view(['GET'])
def test_endpoint(request):
    """
    Simple test endpoint to verify the API is working.
    """
    return Response({
        'message': 'GenCall AI Backend is running!',
        'status': 'ok',
        'twilio_configured': bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def speech_to_text(request):
    """
    Transcribe uploaded audio using speech-to-text provider.

    Request:
    - multipart/form-data
    - file: audio file (required)
    - language: language code (optional, default 'auto')
    - model: OpenAI transcription model (optional, default from settings)
    """
    audio_file = request.FILES.get('file')
    if not audio_file:
        return Response({'error': 'Audio file is required in field "file".'}, status=400)

    requested_language = request.data.get('language', 'auto')
    provider = getattr(settings, 'STT_PROVIDER', 'openai').lower()
    voice_features_raw = request.data.get('voice_features')
    voice_features = None
    if voice_features_raw:
        try:
            voice_features = json.loads(voice_features_raw)
        except Exception:
            voice_features = None

    if provider == 'groq':
        default_model = getattr(settings, 'GROQ_STT_MODEL', 'whisper-large-v3-turbo')
        api_key = getattr(settings, 'GROQ_API_KEY', '')
    else:
        default_model = getattr(settings, 'OPENAI_STT_MODEL', 'whisper-1')
        api_key = getattr(settings, 'OPENAI_API_KEY', '')

    model = request.data.get('model', default_model)

    if not api_key:
        missing = 'GROQ_API_KEY' if provider == 'groq' else 'OPENAI_API_KEY'
        return Response({'error': f'{missing} is not configured on the server.'}, status=500)

    try:
        from openai import OpenAI

        # Groq uses OpenAI-compatible API endpoints.
        if provider == 'groq':
            client = OpenAI(api_key=api_key, base_url='https://api.groq.com/openai/v1')
        else:
            client = OpenAI(api_key=api_key)

        audio_bytes = audio_file.read()
        best_transcript, transcript_candidates = _run_robust_transcription(
            client=client,
            model=model,
            file_name=audio_file.name,
            audio_bytes=audio_bytes,
            content_type=audio_file.content_type,
            requested_language=requested_language,
        )

        text = best_transcript.get('text', '')
        raw_detected_language = best_transcript.get('raw_language', '')
        detected_language = best_transcript.get('detected_language', 'en')

        roman_urdu = None
        urdu_transcript = ''
        english_transcript = ''
        if detected_language.startswith('ur'):
            urdu_transcript = text
            try:
                from unidecode import unidecode
                roman_urdu = unidecode(text).strip()
            except Exception:
                roman_urdu = None
        else:
            english_transcript = text

        intent = {'label': 'unknown', 'confidence': 0.0}
        emotion = {'label': 'unknown', 'confidence': 0.0}
        configured_nlu_model = getattr(settings, 'GROQ_NLU_MODEL', 'llama-3.3-70b')
        nlu_model = _normalize_groq_model(configured_nlu_model)

        if detected_language.startswith('ur') and text:
            english_transcript = _translate_urdu_to_english(client, provider, nlu_model, text)

        # Run intent and emotion in parallel for faster response.
        if text:
            def _detect_intent():
                inference_text = english_transcript or text

                # Early deterministic routing for high-signal intents.
                override = _keyword_intent_override(inference_text)
                if override:
                    return override

                # Try custom model first
                model, tokenizer, labels = _load_custom_intent_model()
                if model is not None and tokenizer is not None:
                    try:
                        import torch
                        with torch.no_grad():
                            inputs = tokenizer(inference_text, return_tensors='pt', truncation=True, max_length=128)
                            outputs = model(**inputs)
                            logits = outputs.logits[0]
                            probabilities = torch.nn.functional.softmax(logits, dim=-1)
                            predicted_class = torch.argmax(probabilities, dim=-1).item()
                            confidence = probabilities[predicted_class].item()
                            
                            intent_label = labels.get(predicted_class, 'unknown') if labels else 'unknown'
                            if confidence < INTENT_CONFIDENCE_THRESHOLD:
                                # Avoid returning random low-confidence labels.
                                return _heuristic_intent(inference_text)
                            return {
                                'label': intent_label,
                                'confidence': float(confidence),
                            }
                    except Exception as e:
                        logger.warning(f'Custom intent model inference failed: {str(e)}')
                
                # Fallback to Groq if provider is groq and model inference failed
                if provider == 'groq':
                    try:
                        prompt = (
                            'Classify user intent from the transcript. '
                            'Return JSON only with keys: label, confidence. '
                            'confidence must be between 0 and 1. '
                            'Possible labels: apply_admission, admission_last_date, scholarship, fee_inquiry, '
                            'documents_inquiry, campus_info, general_info, human_transfer, unknown.\n\n'
                            f'Transcript:\n{text}'
                        )
                        result = client.chat.completions.create(
                            model=nlu_model,
                            messages=[
                                {'role': 'system', 'content': 'You are a strict JSON classifier.'},
                                {'role': 'user', 'content': prompt},
                            ],
                            temperature=0,
                            response_format={'type': 'json_object'},
                        )
                        content = result.choices[0].message.content if result.choices else ''
                        parsed = _safe_json_parse(content)
                        if isinstance(parsed, dict):
                            return {
                                'label': str(parsed.get('label', 'unknown')),
                                'confidence': _clamp_confidence(parsed.get('confidence', 0.0)),
                            }
                    except Exception as e:
                        logger.warning(f'Groq intent detection failed: {str(e)}')
                
                # Final fallback to heuristics
                return _heuristic_intent(text)

            def _detect_emotion():
                voice_hint = ''
                voice_emotion_guess = _voice_emotion_heuristic(voice_features)
                if voice_features:
                    voice_hint = (
                        f"\\n\\nVoice metrics: {json.dumps(voice_features)}"
                        f"\\nHeuristic voice emotion: {voice_emotion_guess.get('label')}"
                        f" (confidence {voice_emotion_guess.get('confidence')})"
                    )
                prompt = (
                    'Classify primary emotion using transcript and voice cues. '
                    'Return JSON only with keys: label, confidence. '
                    'confidence must be between 0 and 1. '
                    'Possible labels: neutral, happy, sad, angry, frustrated, anxious, excited, polite, unknown.\n\n'
                    f'Transcript:\n{text}'
                    f'{voice_hint}'
                )
                result = client.chat.completions.create(
                    model=nlu_model,
                    messages=[
                        {'role': 'system', 'content': 'You are a strict JSON classifier.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    temperature=0,
                    response_format={'type': 'json_object'},
                )
                content = result.choices[0].message.content if result.choices else ''
                parsed = _safe_json_parse(content)
                if isinstance(parsed, dict):
                    llm_emotion = {
                        'label': str(parsed.get('label', 'unknown')),
                        'confidence': _clamp_confidence(parsed.get('confidence', 0.0)),
                    }
                    merged = _merge_emotion_signals(llm_emotion, voice_emotion_guess)
                    return {
                        'label': merged['label'],
                        'confidence': merged['confidence'],
                        'source': merged.get('source', 'text+voice'),
                    }

                fallback_text_emotion = _heuristic_emotion(text)
                merged = _merge_emotion_signals(fallback_text_emotion, voice_emotion_guess)
                return {
                    'label': merged['label'],
                    'confidence': merged['confidence'],
                    'source': merged.get('source', 'heuristic'),
                }

            with ThreadPoolExecutor(max_workers=2) as executor:
                future_intent = executor.submit(_detect_intent)
                future_emotion = executor.submit(_detect_emotion)
                try:
                    intent = future_intent.result()
                except Exception as e:
                    logger.warning(f'Intent detection failed: {str(e)}')
                    intent = _heuristic_intent(text)
                try:
                    emotion = future_emotion.result()
                except Exception as e:
                    logger.warning(f'Emotion detection failed: {str(e)}')
                    merged = _merge_emotion_signals(_heuristic_emotion(text), _voice_emotion_heuristic(voice_features))
                    emotion = {
                        'label': merged['label'],
                        'confidence': merged['confidence'],
                        'source': merged.get('source', 'fallback'),
                    }

        # Process program queries if intent is program-related
        program_query = None
        scholarship_query = None
        normalized_intent = _normalize_program_intent(intent.get('label'))
        if normalized_intent in ['ask_fee', 'ask_admission_fee', 'ask_duration', 'ask_semesters', 'full_info', 'list_programs']:
            query_text = english_transcript or text
            program_query = _process_program_query(query_text, normalized_intent)

        normalized_scholarship_intent = _normalize_scholarship_intent(intent.get('label'))
        if not program_query and (normalized_scholarship_intent.startswith('ask_scholarship') or 'scholarship' in (english_transcript or text).lower()):
            query_text = english_transcript or text
            scholarship_query = _process_scholarship_query(query_text, normalized_scholarship_intent)

        # Fallback routing when model intent is not in program intents but transcript is clearly a program query.
        if not program_query and not scholarship_query and text:
            fallback_text = (english_transcript or text).lower()
            fallback_intent = None
            if any(k in fallback_text for k in ['admission fee']):
                fallback_intent = 'ask_admission_fee'
            elif any(k in fallback_text for k in ['duration', 'semester', 'semesters', 'how many']):
                fallback_intent = 'ask_duration'
            elif any(k in fallback_text for k in ['fee', 'fees', 'tuition', 'cost', 'charges', 'feee']):
                fallback_intent = 'ask_fee'
            elif any(k in fallback_text for k in ['list', 'show', 'programs', 'program']):
                fallback_intent = 'list_programs'
            elif 'scholarship' in fallback_text:
                scholarship_query = _process_scholarship_query(english_transcript or text, 'ask_scholarship_summary')

            if fallback_intent:
                program_query = _process_program_query(english_transcript or text, fallback_intent)

        natural_response = None
        natural_response_raw = None
        response_data = None
        follow_up = None
        program_faculty = None
        scholarship_category = None
        if program_query:
            natural_response_raw = program_query.get('natural_response')
            response_data = program_query.get('program_data')
            follow_up = program_query.get('follow_up')
            program_faculty = program_query.get('faculty')
        elif scholarship_query:
            natural_response_raw = scholarship_query.get('natural_response')
            response_data = scholarship_query.get('scholarship_data')
            follow_up = scholarship_query.get('follow_up')
            scholarship_category = scholarship_query.get('scholarship_category')

        if natural_response_raw:
            natural_response = _humanize_response_fast(
                natural_response_raw,
                emotion_label=(emotion or {}).get('label', 'neutral'),
                language=detected_language,
            )
        else:
            natural_response = None
        
        return Response({
            'text': text,
            'language': requested_language,
            'detected_language': detected_language,
            'raw_detected_language': raw_detected_language,
            'supported_languages': ['en', 'ur'],
            'urdu_transcript': urdu_transcript,
            'english_transcript': english_transcript,
            'stt_quality': best_transcript.get('quality', 0.0),
            'stt_candidates': [
                {
                    'language_requested': c.get('language_requested'),
                    'raw_language': c.get('raw_language'),
                    'detected_language': c.get('detected_language'),
                    'quality': c.get('quality'),
                }
                for c in transcript_candidates
            ],
            'roman_urdu': roman_urdu,
            'model': model,
            'provider': provider,
            'intent': intent,
            'intent_normalized': normalized_intent,
            'emotion': emotion,
            'voice_features': voice_features,
            'nlu_model': nlu_model,
            'nlu_parallel': True,
            'program_query': program_query,
            'scholarship_query': scholarship_query,
            'natural_response': natural_response,
            'natural_response_raw': natural_response_raw,
            'program_data': program_query['program_data'] if program_query else None,
            'scholarship_data': scholarship_query['scholarship_data'] if scholarship_query else None,
            'program_faculty': program_faculty,
            'scholarship_category': scholarship_category,
            'follow_up': follow_up,
        })
    except Exception as e:
        logger.error(f"Speech-to-text failed: {str(e)}")
        return Response({'error': f'Speech-to-text failed: {str(e)}'}, status=500)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def program_query(request):
    """
    Query programs by name, level, or get fee/duration info.
    Standalone endpoint for program queries (without STT).
    
    Request:
    - POST /api/program_query/
    - query: text query (required)
    - level: 'Undergraduate', 'Associate', 'Postgraduate' (optional)
    """
    query = request.data.get('query', '').strip()
    level = request.data.get('level', '').strip()
    emotion_label = request.data.get('emotion', 'neutral')
    
    if not query:
        return Response({'error': 'Query parameter is required.'}, status=400)
    
    try:
        retriever, extractor, formatter = _get_program_services()
        if not retriever or not extractor or not formatter:
            return Response({'error': 'Program services unavailable.'}, status=500)

        # Infer intent from query text for standalone text flow.
        query_l = query.lower()
        if 'scholarship' in query_l:
            inferred_intent = 'ask_scholarship_summary'
        elif any(k in query_l for k in ['list', 'show', 'programs', 'program']):
            inferred_intent = 'list_programs'
        elif any(k in query_l for k in ['duration', 'semester', 'semesters', 'how many']):
            inferred_intent = 'ask_duration'
        elif 'admission fee' in query_l:
            inferred_intent = 'ask_admission_fee'
        elif any(k in query_l for k in ['fee', 'fees', 'tuition', 'cost', 'charges', 'feee']):
            inferred_intent = 'ask_fee'
        else:
            inferred_intent = 'full_info'

        scholarship_result = None
        query_result = None
        if inferred_intent.startswith('ask_scholarship') or 'scholarship' in query_l:
            scholarship_result = _process_scholarship_query(query, inferred_intent)
        else:
            query_result = _process_program_query(query, inferred_intent)
        extraction = extractor.extract_program_and_level(query)
        detected_level = level or extraction.get('level')
        if scholarship_result:
            detected_scholarship_category = _get_scholarship_services()[0].extract_category(query) if _get_scholarship_services()[0] else None
            raw_answer = scholarship_result.get('natural_response')
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'intent': inferred_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'scholarship_category': detected_scholarship_category,
                'scholarship_data': scholarship_result.get('scholarship_data'),
                'program_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': scholarship_result.get('follow_up'),
                'found': bool(scholarship_result.get('scholarship_data') or human_answer),
            })

        # If user explicitly requested level list and pipeline has no response, fallback to listing.
        if inferred_intent == 'list_programs' and not query_result.get('natural_response'):
            if detected_level:
                programs_list = retriever.get_programs_by_level(detected_level)
                natural_response = formatter.format_list_programs(programs_list, detected_level)
            else:
                all_levels = ['Associate', 'Undergraduate', 'Postgraduate']
                blocks = []
                for lvl in all_levels:
                    programs_list = retriever.get_programs_by_level(lvl)
                    if programs_list:
                        blocks.append(formatter.format_list_programs(programs_list, lvl))
                natural_response = '\n\n'.join(blocks) if blocks else 'Sorry, no programs were found.'
            query_result['natural_response'] = natural_response

        raw_answer = query_result.get('natural_response')
        human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None

        return Response({
            'query': query,
            'intent': inferred_intent,
            'program_name': query_result.get('program_name') or extraction.get('program'),
            'level': query_result.get('level') or detected_level,
            'faculty': query_result.get('faculty') or extraction.get('faculty'),
            'program_data': query_result.get('program_data'),
            'natural_response': human_answer,
            'natural_response_raw': raw_answer,
            'follow_up': query_result.get('follow_up'),
            'found': bool(query_result.get('program_data') or human_answer),
        })
    
    except Exception as e:
        logger.error(f'Program query failed: {str(e)}')
        return Response({'error': f'Program query failed: {str(e)}'}, status=500)


@api_view(['GET'])
def list_all_programs(request):
    """
    Get list of all programs by level.
    
    GET /api/programs/list/
    - level: 'Undergraduate', 'Associate', 'Postgraduate' (optional - returns all if not specified)
    """
    level = request.query_params.get('level', '').strip()
    
    try:
        retriever, _, _ = _get_program_services()
        if not retriever:
            return Response({'error': 'Program services unavailable.'}, status=500)
        
        if level:
            programs = retriever.get_programs_by_level(level)
            return Response({
                'level': level,
                'programs': programs,
                'count': len(programs),
            })
        else:
            # Return programs grouped by level
            undergrad = retriever.get_programs_by_level('Undergraduate')
            associate = retriever.get_programs_by_level('Associate')
            postgrad = retriever.get_programs_by_level('Postgraduate')
            
            return Response({
                'undergraduate': undergrad,
                'associate': associate,
                'postgraduate': postgrad,
                'total': len(undergrad) + len(associate) + len(postgrad),
            })
    
    except Exception as e:
        logger.error(f'List programs failed: {str(e)}')
        return Response({'error': f'Failed to list programs: {str(e)}'}, status=500)


@api_view(['POST'])
def text_to_speech(request):
    """Convert answer text to speech using gTTS and return MP3 audio."""
    text = (request.data.get('text', '') or '').strip()
    language = (request.data.get('language', 'en') or 'en').strip().lower()

    if not text:
        return Response({'error': 'Text is required.'}, status=400)

    # gTTS language support in this app: English and Urdu.
    tts_lang = 'ur' if language.startswith('ur') else 'en'

    try:
        import importlib
        gtts_module = importlib.import_module('gtts')
        gTTS = gtts_module.gTTS

        mp3_buffer = io.BytesIO()
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)

        response = HttpResponse(mp3_buffer.read(), content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="answer.mp3"'
        return response
    except Exception as e:
        logger.error(f'Text-to-speech failed: {str(e)}')
        return Response({'error': f'Text-to-speech failed: {str(e)}'}, status=500)
