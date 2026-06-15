"""
Views for handling Twilio webhooks and API endpoints.
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import parser_classes
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from django.conf import settings
from .models import CallLog, LearnedWebAnswer, get_active_twilio_config
from django.utils import timezone
import logging
import re
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import io
import httpx

logger = logging.getLogger(__name__)

# Initialize program query services lazily
_program_retriever = None
_entity_extractor = None
_response_formatter = None
_scholarship_retriever = None
_admission_retriever = None
_web_retriever = None

# Initialize new data retrievers lazily
_campuses_retriever = None
_facilities_retriever = None
_hostal_retriever = None
_local_hybrid_index = None
_retrieval_cache_path = Path(__file__).resolve().parent.parent / 'Data' / 'retrieval_cache' / 'local_vector_cache.pkl'


def _twilio_env_configured():
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_PHONE_NUMBER
        and settings.TWIML_APP_SID
        and settings.TWILIO_API_KEY_SID
        and settings.TWILIO_API_KEY_SECRET
    )

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


def _get_admission_services():
    """Get or initialize admission query services."""
    global _admission_retriever, _response_formatter

    if _admission_retriever is None:
        try:
            from services.data_retriever import AdmissionPolicyRetriever
            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'admission.csv',
                backend_dir / 'Data' / 'Admission.csv',
                Path('Data/admission.csv'),
                Path('Data/Admission.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                raise FileNotFoundError('Admission CSV not found in backend/Data.')
            _admission_retriever = AdmissionPolicyRetriever(str(csv_path))
            logger.info('Admission services initialized successfully')
        except Exception as e:
            _admission_retriever = None
            logger.warning(f'Failed to initialize admission services: {str(e)}')
            return None, None

    try:
        from services.response_formatter import ProgramResponseFormatter
        formatter = _response_formatter or ProgramResponseFormatter()
    except Exception:
        formatter = None

    return _admission_retriever, formatter


def _get_web_retriever():
    """Get or initialize real-time website retriever."""
    global _web_retriever
    if _web_retriever is None:
        try:
            from services.web_retriever import SuperiorWebRetriever
            _web_retriever = SuperiorWebRetriever(timeout=6)
        except Exception as e:
            _web_retriever = None
            logger.warning(f'Failed to initialize web retriever: {str(e)}')
    return _web_retriever


def _get_botpress_config():
    """Load Botpress Chat API configuration from Django settings."""
    return {
        'bot_id': getattr(settings, 'BOTPRESS_BOT_ID', ''),
        'client_id': getattr(settings, 'BOTPRESS_CLIENT_ID', ''),
        'api_token': getattr(settings, 'BOTPRESS_API_TOKEN', ''),
        'chat_api_url': getattr(settings, 'BOTPRESS_CHAT_API_URL', 'https://api.botpress.cloud/v1/chat'),
        'integration_alias': getattr(settings, 'BOTPRESS_INTEGRATION_ALIAS', ''),
    }


def _get_campuses_retriever():
    """Get or initialize campuses info retriever."""
    global _campuses_retriever
    
    if _campuses_retriever is None:
        try:
            from services.data_retriever import CampusesInfoRetriever
            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'Campuses_info.csv',
                backend_dir / 'Data' / 'campuses_info.csv',
                Path('Data/Campuses_info.csv'),
                Path('Data/campuses_info.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                logger.warning('Campuses CSV not found in backend/Data')
                return None
            _campuses_retriever = CampusesInfoRetriever(str(csv_path))
            logger.info('Campuses retriever initialized successfully')
        except Exception as e:
            _campuses_retriever = None
            logger.warning(f'Failed to initialize campuses retriever: {str(e)}')
    
    return _campuses_retriever


def _get_facilities_retriever():
    """Get or initialize facilities info retriever."""
    global _facilities_retriever
    
    if _facilities_retriever is None:
        try:
            from services.data_retriever import FacilitiesRetriever
            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'Facilities.csv',
                backend_dir / 'Data' / 'facilities.csv',
                Path('Data/Facilities.csv'),
                Path('Data/facilities.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                logger.warning('Facilities CSV not found in backend/Data')
                return None
            _facilities_retriever = FacilitiesRetriever(str(csv_path))
            logger.info('Facilities retriever initialized successfully')
        except Exception as e:
            _facilities_retriever = None
            logger.warning(f'Failed to initialize facilities retriever: {str(e)}')
    
    return _facilities_retriever


def _get_hostal_retriever():
    """Get or initialize hostal/accommodation info retriever."""
    global _hostal_retriever
    
    if _hostal_retriever is None:
        try:
            from services.data_retriever import HostalRetriever
            backend_dir = Path(__file__).resolve().parent.parent
            csv_candidates = [
                backend_dir / 'Data' / 'hostal.csv',
                backend_dir / 'Data' / 'hostel.csv',
                backend_dir / 'Data' / 'Hostal.csv',
                backend_dir / 'Data' / 'Hostel.csv',
                Path('Data/hostal.csv'),
                Path('Data/hostel.csv'),
                Path('Data/Hostal.csv'),
                Path('Data/Hostel.csv'),
            ]
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if not csv_path:
                logger.warning('Hostal CSV not found in backend/Data')
                return None
            _hostal_retriever = HostalRetriever(str(csv_path))
            logger.info('Hostal retriever initialized successfully')
        except Exception as e:
            _hostal_retriever = None
            logger.warning(f'Failed to initialize hostal retriever: {str(e)}')
    
    return _hostal_retriever


def _get_local_hybrid_index():
    """Build a cached hybrid index across the available local CSV sources."""
    global _local_hybrid_index

    if _local_hybrid_index is not None:
        return _local_hybrid_index

    try:
        from services.local_hybrid_retrieval import build_local_hybrid_index

        program_services = _get_program_services()
        scholarship_services = _get_scholarship_services()
        admission_services = _get_admission_services()
        campuses_retriever = _get_campuses_retriever()
        facilities_retriever = _get_facilities_retriever()
        hostal_retriever = _get_hostal_retriever()

        source_specs = []

        if program_services and program_services[0] is not None:
            source_specs.append({
                'source_name': 'programs',
                'source_label': 'programs.csv',
                'dataframe': program_services[0].df.copy(),
                'preferred_columns': ['Level', 'Faculty', 'Program', 'Admission Fee', 'Misc. (Per Semester)', 'Number of Semesters', 'Tuition Fee (1st Semester)', 'Total Fee'],
            })

        if scholarship_services and scholarship_services[0] is not None:
            source_specs.append({
                'source_name': 'scholarship_policy',
                'source_label': 'scholarship_policy.csv',
                'dataframe': scholarship_services[0].df.copy(),
            })

        if admission_services and admission_services[0] is not None:
            source_specs.append({
                'source_name': 'admission',
                'source_label': 'admission.csv',
                'dataframe': admission_services[0].df.copy(),
            })

        if campuses_retriever is not None:
            source_specs.append({
                'source_name': 'campuses_info',
                'source_label': 'campuses_info.csv',
                'dataframe': campuses_retriever.df.copy(),
            })

        if facilities_retriever is not None:
            source_specs.append({
                'source_name': 'facilities',
                'source_label': 'facilities.csv',
                'dataframe': facilities_retriever.df.copy(),
            })

        if hostal_retriever is not None:
            source_specs.append({
                'source_name': 'hostal',
                'source_label': 'hostal.csv',
                'dataframe': hostal_retriever.df.copy(),
            })

        if not source_specs:
            return None

        _local_hybrid_index = build_local_hybrid_index(source_specs)

        # Try to build an optional FAISS vector index to improve semantic recall.
        try:
            from services.vector_index import VectorIndex

            texts = [doc.text for doc in _local_hybrid_index.documents]
            if texts:
                try:
                    vec = VectorIndex(texts, cache_path=str(_retrieval_cache_path))
                    _local_hybrid_index._vector_index = vec
                    logger.info('Attached FAISS VectorIndex to local hybrid index')
                except Exception as e:
                    logger.warning(f'Failed to build VectorIndex: {str(e)}')
        except Exception:
            # Not fatal — vector index is optional
            pass

        return _local_hybrid_index
    except Exception as e:
        logger.warning(f'Failed to initialize local hybrid retrieval index: {str(e)}')
        _local_hybrid_index = None
        return None


def _extract_botpress_text(payload):
    """Extract the most useful text from a Botpress response payload."""
    if isinstance(payload, str):
        return payload.strip()

    if not isinstance(payload, dict):
        return ''

    for key in ('text', 'message', 'content', 'answer', 'response'):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    nested = payload.get('payload')
    if isinstance(nested, dict):
        for key in ('text', 'content', 'answer'):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ''


def _normalize_transcript_with_groq(text, detected_language='en'):
    """Use Groq to clean a transcript before intent detection."""
    transcript = (text or '').strip()
    if not transcript:
        return ''

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return transcript

    model = _normalize_groq_model(getattr(settings, 'GROQ_NLU_MODEL', 'llama-3.3-70b-versatile'))
    language_hint = 'Urdu' if str(detected_language).lower().startswith('ur') else 'English'
    prompt = (
        'Clean and correct this call transcript for accurate intent detection. '
        'Fix obvious speech-to-text mistakes, repeated words, and punctuation. '
        'Keep the same language as the input transcript. Preserve university names, program names, fees, and numbers exactly. '
        f'Return only the corrected transcript in {language_hint}.\n\n'
        f'Transcript:\n{transcript}'
    )

    try:
        response = httpx.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                'temperature': 0,
                'max_tokens': 256,
            },
            timeout=6.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get('choices') or []
        for choice in choices:
            message = choice.get('message') or {}
            cleaned = message.get('content', '').strip()
            cleaned = re.sub(r'^```(?:text)?\s*|\s*```$', '', cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                return cleaned

        return transcript
    except Exception as e:
        logger.warning(f'Groq transcript cleanup failed: {str(e)}')
        return transcript


def _groq_rephrase_and_detect_intent(input_text):
    """Use Groq to detect a short intent and rewrite the question in formal English, with data source mapping."""
    question = (input_text or '').strip()
    if not question:
        return {
            'intent': 'unknown',
            'clean_question': '',
            'data_source': 'unknown',
            'data_source_info': 'No question provided',
        }

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    model = _normalize_groq_model(getattr(settings, 'GROQ_NLU_MODEL', 'llama-3.3-70b-versatile'))
    if not api_key:
        return {
            'intent': 'unknown',
            'clean_question': question,
            'data_source': 'unknown',
            'data_source_info': 'API key not configured',
        }

    prompt = (
        'You are an AI system that understands student questions about a university.\n\n'
        'Your job is to:\n'
        '1. Understand what the user is asking\n'
        '2. Generate a short intent name (2–3 words, snake_case)\n'
        '3. Rewrite the question clearly in formal English\n'
        '4. Identify which data source should be queried\n\n'
        'AVAILABLE DATA SOURCES:\n'
        '- programs.csv: Bachelor programs, Masters programs, engineering, business, science programs\n'
        '- admission_policy.csv: Admission requirements, eligibility criteria, application deadlines, entry tests\n'
        '- scholarship_policy.csv: Scholarships, grants, fee waivers, financial aid\n'
        '- campuses_info.csv: Campus locations, addresses, phone numbers, facilities\n'
        '- facilities.csv: Library, lab, transport, medical, daycare, sports, parking, infrastructure\n'
        '- hostal.csv: Hostel accommodation, rooms, internet, security, meal plans\n'
        '- university_info.csv: General university information, history, mission, contact\n\n'
        'INTENT RULES:\n'
        '- Intent must be short and reusable (like hostel_fee, admission_deadline, eligibility)\n'
        '- Do NOT create long or sentence-like intents\n'
        '- Use lowercase and underscore format\n\n'
        'DATA SOURCE MAPPING:\n'
        '- If asking about "programs", "majors", "degrees" -> programs\n'
        '- If asking about "admission", "apply", "requirements", "eligibility" -> admission_policy\n'
        '- If asking about "scholarship", "fee waiver", "grant", "financial" -> scholarship_policy\n'
        '- If asking about "campus", "location", "address", "contact" -> campuses_info\n'
        '- If asking about "facilities", "library", "lab", "transport", "medical" -> facilities\n'
        '- If asking about "hostel", "accommodation", "room", "internet" -> hostal\n'
        '- Otherwise -> university_info\n\n'
        f'User Question:\n{question}\n\n'
        'Return ONLY JSON:\n'
        '{\n'
        '  "intent": "...",\n'
        '  "clean_question": "...",\n'
        '  "data_source": "programs|admission_policy|scholarship_policy|campuses_info|facilities|hostal|university_info",\n'
        '  "data_source_info": "Brief description of which data will answer this"\n'
        '}'
    )

    try:
        response = httpx.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                'temperature': 0,
                'max_tokens': 300,
            },
            timeout=8.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get('choices') or []
        for choice in choices:
            message = choice.get('message') or {}
            raw = message.get('content', '').strip()
            parsed = _safe_json_parse(raw)
            if isinstance(parsed, dict):
                intent = str(parsed.get('intent', 'unknown')).strip().lower()
                clean_question = str(parsed.get('clean_question', question)).strip()
                data_source = str(parsed.get('data_source', 'university_info')).strip().lower()
                data_source_info = str(parsed.get('data_source_info', 'General information')).strip()
                intent = re.sub(r'[^a-z0-9_]', '_', intent)
                intent = re.sub(r'_+', '_', intent).strip('_') or 'unknown'
                return {
                    'intent': intent,
                    'clean_question': clean_question or question,
                    'data_source': data_source,
                    'data_source_info': data_source_info,
                }
    except Exception as e:
        logger.warning(f'Groq intent+rewrite failed: {str(e)}')

    return {
        'intent': 'unknown',
        'clean_question': question,
        'data_source': 'unknown',
        'data_source_info': 'Could not determine data source',
    }


def _groq_answer_from_context(question, context_text, data_source=''):
    """Use Groq to answer only from provided context with source transparency."""
    q = (question or '').strip()
    ctx = (context_text or '').strip()
    if not q or not ctx:
        return None

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    model = _normalize_groq_model(getattr(settings, 'GROQ_NLU_MODEL', 'llama-3.3-70b-versatile'))
    if not api_key:
        return None

    source_hint = f"Data source: {data_source}. " if data_source else ""
    prompt = (
        'You are an AI assistant for a university admission system.\n\n'
        'Use ONLY the provided context. Never rely on outside knowledge.\n\n'
        'STRICT RULES:\n'
        '- Every factual statement must be supported by an explicit source citation from the context\n'
        '- Cite sources using the exact source label format shown in the context, for example [campuses_info], [admission], or [scholarship_policy]\n'
        '- If a sentence uses facts from multiple source blocks, include all relevant source tags at the end of that sentence\n'
        '- If the answer cannot be fully supported by the context, say exactly: "This information is not available in our database. Please contact the university."\n'
        '- Do not use any uncited factual claim\n'
        '- Do not add explanations, caveats, markdown bullets, or JSON\n'
        '- Keep the answer to one short sentence only, or two very short sentences if absolutely necessary\n'
        '- For yes/no questions, start with Yes or No and then add the shortest correct detail\n'
        '- Do not enumerate features unless the user asks for a list\n\n'
        'FORMAT:\n'
        '- One short sentence preferred\n'
        '- Put the citation tag(s) immediately after the sentence they support\n\n'
        f'{source_hint}'
        'QUESTION:\n'
        f'{q}\n\n'
        'CONTEXT:\n'
        f'{ctx}\n\n'
        'Return only the final answer.'
    )

    def _infer_source_tag(question_text, answer_text):
        q_lower = (question_text or '').lower()
        a_lower = (answer_text or '').lower()

        if any(term in q_lower for term in ('wifi', 'wi-fi', 'internet')) and any(term in q_lower for term in ('hostel', 'hostal', 'accommodation')):
            return '[hostal]'
        if any(term in q_lower for term in ('campus', 'address', 'phone', 'location', 'contact')):
            return '[campuses_info]'
        if any(term in q_lower for term in ('scholarship', 'merit', 'financial aid', 'fee waiver')):
            return '[scholarship_policy]'
        if any(term in q_lower for term in ('admission', 'deadline', 'apply', 'eligibility', 'documents')):
            return '[admission]'
        if any(term in q_lower for term in ('program', 'degree', 'bs ', 'ms ', 'bachelor', 'master')):
            return '[programs]'
        if any(term in a_lower for term in ('[hostal]', '[campuses_info]', '[scholarship_policy]', '[admission]', '[programs]')):
            match = re.search(r'\[(hostal|campuses_info|scholarship_policy|admission|programs)\]', a_lower)
            if match:
                return f'[{match.group(1)}]'
        return ''

    def _shorten_answer(question_text, answer_text):
        text = re.sub(r'^```(?:text)?\s*|\s*```$', '', (answer_text or '').strip(), flags=re.IGNORECASE).strip()
        if not text:
            return text

        source_tag = _infer_source_tag(question_text, text)

        q_lower = (question_text or '').lower()
        a_lower = text.lower()
        if any(term in q_lower for term in ('wifi', 'wi-fi', 'internet')) and any(term in q_lower for term in ('hostel', 'hostal', 'accommodation')):
            if any(term in a_lower for term in ('yes', 'available', 'high-speed internet', 'wi-fi', 'wifi')):
                return f'Yes, Wi-Fi is available in the hostel {source_tag}'.strip()
            if any(term in a_lower for term in ('no', 'not available', 'unavailable')):
                return f'No, Wi-Fi is not available in the hostel {source_tag}'.strip()

        # Keep only the first non-empty line to avoid feature dumps while preserving citations.
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            text = lines[0]

        # Collapse long list-like answers into one short sentence.
        if '•' in text or '- ' in text or '**' in text or 'our accommodation features' in text.lower():
            text = re.split(r'[\.;]', text, maxsplit=1)[0].strip()

        if source_tag and source_tag not in text:
            if text.endswith('.'):
                text = f"{text[:-1]} {source_tag}."
            else:
                text = f"{text} {source_tag}"

        text = re.sub(r'\s+', ' ', text).strip()
        return text

    try:
        response = httpx.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 300,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get('choices') or []
        for choice in choices:
            message = choice.get('message') or {}
            answer = _shorten_answer(q, message.get('content', ''))
            if answer:
                return answer
    except Exception as e:
        logger.warning(f'Groq context answer failed: {str(e)}')

    return None


def _extract_botpress_message_text(messages):
    """Pick the newest non-user Botpress message text from a message list."""
    if not isinstance(messages, list):
        return ''

    for message in messages:
        if not isinstance(message, dict):
            continue
        direction = str(message.get('direction', '')).lower()
        if direction == 'incoming':
            continue
        payload_text = _extract_botpress_text(message.get('payload'))
        if payload_text:
            return payload_text

    for message in messages:
        payload_text = _extract_botpress_text((message or {}).get('payload'))
        if payload_text:
            return payload_text

    return ''


def _process_botpress_runtime_query(query_text, transcript_text=None, intent_label=None, emotion_label='neutral'):
    """Send question to Botpress Chat API when local knowledge base has no answer."""
    config = _get_botpress_config()
    
    if not config.get('bot_id') or not config.get('api_token') or not config.get('integration_alias'):
        return {
            'intent_used': 'botpress_runtime_unavailable',
            'natural_response': (
                'Botpress fallback is not configured. '
                'Please set BOTPRESS_BOT_ID, BOTPRESS_API_TOKEN, and BOTPRESS_INTEGRATION_ALIAS in backend/.env.'
            ),
            'realtime_data': {
                'source': 'botpress_chat_api',
                'configured': False,
            },
            'answer_source': 'botpress_unavailable',
            'answer_source_confidence': 0.0,
            'admin_verified': False,
            'follow_up': None,
        }

    question_text = (transcript_text or query_text or '').strip()
    if not question_text:
        return None

    # Build headers for Chat API authentication
    headers = {
        'Authorization': f'Bearer {config["api_token"]}',
        'Content-Type': 'application/json',
        'x-bot-id': config['bot_id'],
    }
    
    if config.get('client_id'):
        headers['x-client-id'] = config['client_id']

    # Generate conversation and user IDs
    user_id = uuid.uuid4().hex
    conversation_id = uuid.uuid4().hex

    try:
        with httpx.Client(timeout=8.0) as client:
            # Step 1: Create a conversation
            conv_response = client.post(
                f"{config['chat_api_url']}/conversations",
                json={
                    'integrationAlias': config['integration_alias'],
                    'channel': 'web',
                    'tags': {'source': 'gencall'},
                },
                headers=headers,
            )
            
            if conv_response.status_code != 201:
                logger.error(f'Botpress conversation creation failed: {conv_response.status_code} - {conv_response.text}')
                return {
                    'intent_used': 'botpress_runtime_unavailable',
                    'natural_response': 'Botpress fallback is temporarily unavailable.',
                    'realtime_data': {
                        'source': 'botpress_chat_api',
                        'http_status': conv_response.status_code,
                        'error': conv_response.text[:500],
                    },
                    'answer_source': 'botpress_unavailable',
                    'answer_source_confidence': 0.0,
                    'admin_verified': False,
                    'follow_up': None,
                }
            
            conv_data = conv_response.json()
            created_conversation_id = (conv_data.get('conversation') or {}).get('id')
            
            if not created_conversation_id:
                return None

            # Step 2: Send message to the bot
            msg_response = client.post(
                f"{config['chat_api_url']}/messages",
                json={
                    'conversationId': created_conversation_id,
                    'userId': user_id,
                    'payload': {
                        'type': 'text',
                        'text': question_text,
                    },
                },
                headers=headers,
            )
            
            if msg_response.status_code != 201:
                logger.error(f'Botpress message send failed: {msg_response.status_code} - {msg_response.text}')
                return None

            # Step 3: Wait briefly and fetch bot's response
            import time
            time.sleep(0.5)
            
            messages_response = client.get(
                f"{config['chat_api_url']}/conversations/{created_conversation_id}/messages",
                headers=headers,
            )
            
            if messages_response.status_code != 200:
                return None
            
            messages_data = messages_response.json()
            all_messages = messages_data.get('messages') or []
            
            # Extract bot's text response from messages
            bot_text = _extract_botpress_message_text(all_messages)

            if not bot_text:
                return None

            return {
                'intent_used': 'botpress_chat_api',
                'natural_response': bot_text,
                'realtime_data': {
                    'source': 'botpress_chat_api',
                    'conversation_id': created_conversation_id,
                    'messages_count': len(all_messages),
                },
                'answer_source': 'botpress_chat_api',
                'answer_source_confidence': 0.80,
                'admin_verified': False,
                'follow_up': None,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f'Botpress Chat API error: {e.response.status_code} - {e.response.text}')
        return None
    except Exception as e:
        logger.error(f'Botpress Chat API exception: {str(e)}')
        return None


def _is_unresolved_answer(answer_text):
    text = (answer_text or '').strip().lower()
    if not text:
        return True
    unresolved_markers = [
        "sorry, i couldn't find",
        'sorry, no',
        'services unavailable',
        'not found',
    ]
    return any(marker in text for marker in unresolved_markers)


def _normalize_learning_question(text):
    q = _normalize_query_for_understanding(text)
    q = re.sub(r'[^a-z0-9\s]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q[:380]


def _get_learned_web_answer(query_text):
    """Fetch cached learned answer for a normalized question."""
    normalized = _normalize_learning_question(query_text)
    if not normalized:
        return None

    learned = LearnedWebAnswer.objects.filter(normalized_question=normalized).first()
    if not learned:
        return None

    learned.times_used = (learned.times_used or 0) + 1
    learned.last_used_at = timezone.now()
    learned.save(update_fields=['times_used', 'last_used_at', 'updated_at'])

    return {
        'question_text': learned.question_text,
        'normalized_question': learned.normalized_question,
        'answer_text': learned.answer_text,
        'source_url': learned.source_url,
        'source_snippets': learned.source_snippets or [],
        'admin_verified': bool(learned.admin_verified),
    }


def _save_learned_web_answer(query_text, answer_text, source_url, snippets):
    """Create or update learned answer so future same question can be answered instantly."""
    normalized = _normalize_learning_question(query_text)
    if not normalized or not answer_text:
        return None

    defaults = {
        'question_text': (query_text or '').strip(),
        'answer_text': answer_text,
        'source_url': source_url or 'https://www.superior.edu.pk/',
        'source_snippets': snippets or [],
        # New/updated crawl answers should be reviewed by admin.
        'admin_verified': False,
    }
    learned, created = LearnedWebAnswer.objects.get_or_create(
        normalized_question=normalized,
        defaults=defaults,
    )

    if not created:
        learned.question_text = defaults['question_text']
        learned.answer_text = defaults['answer_text']
        learned.source_url = defaults['source_url']
        learned.source_snippets = defaults['source_snippets']
        learned.admin_verified = False
        learned.save(update_fields=['question_text', 'answer_text', 'source_url', 'source_snippets', 'admin_verified', 'updated_at'])

    return learned


def _process_realtime_web_query(query_text):
    """Fallback to Superior website retrieval and Gemini context-grounded answer."""
    generic_line = 'The exact information is not available in the provided data. Please check the official website or contact the university.'
    learned = _get_learned_web_answer(query_text)
    if learned:
        learned_source = learned.get('source_url', 'https://www.superior.edu.pk/')
        learned_answer = learned.get('answer_text') or ''
        learned_snippets = learned.get('source_snippets', []) or []
        if learned_snippets and learned_answer.strip().lower() == generic_line.lower():
            preview = ' '.join(learned_snippets[:2]).strip()
            learned_answer = (
                f'Based on the latest information on Superior University\'s website: {preview} '
                f'For more details, please visit {learned_source}.'
            )
            _save_learned_web_answer(
                query_text=query_text,
                answer_text=learned_answer,
                source_url=learned_source,
                snippets=learned_snippets,
            )
        if learned_answer:
            return {
                'intent_used': 'learned_web_answer',
                'natural_response': learned_answer,
                'realtime_data': {
                    'source': learned_source,
                    'snippets': learned_snippets,
                    'from_cache': True,
                    'admin_verified': bool(learned.get('admin_verified')),
                },
                'answer_source': 'learned_web_cache',
                'answer_source_confidence': 0.97 if learned.get('admin_verified') else 0.90,
                'admin_verified': bool(learned.get('admin_verified')),
                'follow_up': None,
            }

    retriever = _get_web_retriever()
    if not retriever:
        return {
            'intent_used': 'realtime_web_fallback',
            'natural_response': 'The exact information is not available in the provided data. Please check the official website or contact the university.',
            'realtime_data': {
                'source': 'https://www.superior.edu.pk/',
                'snippets': [],
                'from_cache': False,
                'admin_verified': False,
            },
            'answer_source': 'realtime_superior_web_gemini',
            'answer_source_confidence': 0.45,
            'admin_verified': False,
            'follow_up': None,
        }

    result = retriever.search(query_text)
    if not result or not result.get('found'):
        return {
            'intent_used': 'realtime_web_fallback',
            'natural_response': 'The exact information is not available in the provided data. Please check the official website or contact the university.',
            'realtime_data': {
                'source': 'https://www.superior.edu.pk/',
                'snippets': [],
                'from_cache': False,
                'admin_verified': False,
            },
            'answer_source': 'realtime_superior_web_gemini',
            'answer_source_confidence': 0.45,
            'admin_verified': False,
            'follow_up': None,
        }

    snippets = result.get('snippets', [])
    # Remove duplicates while preserving order.
    seen_snippets = set()
    unique_snippets = []
    for snippet in snippets:
        key = (snippet or '').strip()
        if not key or key in seen_snippets:
            continue
        seen_snippets.add(key)
        unique_snippets.append(key)
    snippets = unique_snippets

    source = result.get('source', 'https://www.superior.edu.pk/')
    context_text = '\n'.join([f'- {s}' for s in snippets])

    answer = _groq_answer_from_context(query_text, context_text, 'Superior University Website')
    if not answer:
        answer = 'The exact information is not available in the provided data. Please check the official website or contact the university.'

    # If Gemini falls back to the generic line but snippets exist, provide closest helpful info.
    if snippets and answer.strip().lower() == generic_line.lower():
        preview = ' '.join(snippets[:2]).strip()
        answer = (
            f'Based on the latest information on Superior University\'s website: {preview} '
            f'For more details, please visit {source}.'
        )

    _save_learned_web_answer(
        query_text=query_text,
        answer_text=answer,
        source_url=source,
        snippets=snippets,
    )

    return {
        'intent_used': 'realtime_web_fallback',
        'natural_response': answer,
        'realtime_data': {
            'source': source,
            'snippets': snippets,
            'context': context_text,
            'from_cache': False,
            'admin_verified': False,
        },
        'answer_source': 'realtime_superior_web_gemini',
        'answer_source_confidence': 0.78,
        'admin_verified': False,
        'follow_up': None,
    }


def _process_external_fallback(query_text, transcript_text=None, intent_label=None, emotion_label='neutral'):
    """Fallback: assemble relevant local CSV data and ask Groq for a concise answer.

    The previous implementation routed to Botpress. This replacement collects
    matching rows from available local retrievers (programs, admission,
    scholarship, campuses, facilities, hostel), builds a compact context with
    explicit SOURCE labels, and asks Groq to answer only from that context.
    """
    question = (transcript_text or query_text or '').strip()
    if not question:
        return None

    hybrid_index = _get_local_hybrid_index()
    context = hybrid_index.build_context(question, top_k=8, max_chars=3500) if hybrid_index else ''
    if not context:
        return {
            'intent_used': 'local_data_empty',
            'natural_response': 'I could not find relevant information in the local data.',
            'realtime_data': {'source': 'local_csvs', 'context': ''},
            'answer_source': 'none',
            'answer_source_confidence': 0.0,
            'admin_verified': False,
            'follow_up': None,
        }

    # Ask Groq to answer concisely from the assembled local context
    answer = _groq_answer_from_context(question, context, data_source='local_csvs')
    if not answer:
        return {
            'intent_used': 'groq_local_no_answer',
            'natural_response': 'This information is not available in our database. Please contact the university.',
            'realtime_data': {'source': 'local_csvs', 'context': context},
            'answer_source': 'groq_local',
            'answer_source_confidence': 0.45,
            'admin_verified': False,
            'follow_up': None,
        }

    return {
        'intent_used': 'groq_local',
        'natural_response': answer,
        'realtime_data': {'source': 'local_csvs', 'context': context},
        'answer_source': 'groq_local',
        'answer_source_confidence': 0.92,
        'admin_verified': False,
        'follow_up': None,
    }


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


def _normalize_query_for_understanding(text):
    """Normalize common query typos/variants for better intent detection."""
    q = (text or '').lower().strip()
    replacements = {
        'hostal': 'hostel',
        'hostle': 'hostel',
        'feee': 'fee',
        'assosiate': 'associate',
        'assisate': 'associate',
        'faculity': 'faculty',
        'fucuilty': 'faculty',
        'scholarsip': 'scholarship',
        'scolarsip': 'scholarship',
        'progarm': 'program',
        'programs offered': 'offered programs',
        'entry test': 'entry_test',
        'merit list': 'merit_list',
        'last date': 'deadline',
        'closing date': 'deadline',
        'admission open': 'admission_open',
        'admission closes': 'admission_close',
    }
    for wrong, right in replacements.items():
        q = q.replace(wrong, right)

    q = re.sub(r'\s+', ' ', q).strip()
    return q


def _classify_primary_domain(text):
    """Classify question into primary domain: programs, scholarship, admission, campus, facilities, or hostel."""
    q = _normalize_query_for_understanding(text)

    admission_keywords = [
        'admission', 'apply', 'application', 'enrollment', 'entry_test',
        'merit_list', 'deadline', 'admission_open', 'eligibility', 'interview',
    ]
    scholarship_keywords = [
        'scholarship', 'financial aid', 'need based', 'need-based',
        'sports scholarship', 'kinship', 'hafiz', 'employee scholarship',
    ]
    program_keywords = [
        'program', 'course', 'degree', 'major', 'bachelor', 'master',
        'offered', 'faculty', 'department',
    ]
    campus_keywords = [
        'campus', 'location', 'address', 'where', 'situated', 'city',
    ]
    facilities_keywords = [
        'facility', 'facilities', 'transport', 'medical', 'healthcare', 'daycare', 'environment',
        'infrastructure', 'parking', 'library', 'lab', 'laboratory',
    ]
    hostel_keywords = [
        'hostel', 'accommodation', 'hostal', 'hostle', 'room', 'security',
        'facilities', 'internet', 'wifi', 'lodging', 'residence',
    ]

    admission_count = sum(1 for k in admission_keywords if k in q)
    scholarship_count = sum(1 for k in scholarship_keywords if k in q)
    program_count = sum(1 for k in program_keywords if k in q)
    campus_count = sum(1 for k in campus_keywords if k in q)
    facilities_count = sum(1 for k in facilities_keywords if k in q)
    hostel_count = sum(1 for k in hostel_keywords if k in q)

    # Explicit scholarship keyword detection - prioritize if present
    if 'scholarship' in q or 'financial aid' in q:
        return 'scholarship'
    
    # Campus domain
    if campus_count > 0 and campus_count >= admission_count and campus_count >= scholarship_count and campus_count >= program_count:
        return 'campus'
    
    # Hostel domain
    if hostel_count > 0 and hostel_count >= admission_count and hostel_count >= scholarship_count and hostel_count >= program_count and hostel_count >= campus_count:
        return 'hostel'
    
    # Facilities domain
    if facilities_count > 0 and facilities_count >= admission_count and facilities_count >= scholarship_count and facilities_count >= program_count and facilities_count >= campus_count and facilities_count >= hostel_count:
        return 'facilities'

    if scholarship_count > 0 and scholarship_count >= admission_count and scholarship_count >= program_count:
        return 'scholarship'
    if admission_count > 0 and admission_count >= program_count:
        return 'admission'
    return 'programs'


def _classify_admission_subtype(text):
    """Classify admission question into specific subtypes."""
    q = (text or '').lower()
    normalized = _normalize_query_for_understanding(q)
    
    # apply_admission: how to apply, application process
    if any(k in normalized for k in ['apply', 'application', 'how to apply', 'apply for', 'apply kaise', 'application process', 'application mode', 'enroll', 'registration']):
        return 'apply_admission'
    
    # admission_last_date: deadline, last date, closing date
    if any(k in normalized for k in ['deadline', 'close hoga', 'last day', 'kab tak', 'final date', 'closing']):
        return 'admission_last_date'
    
    # admission_merit: merit criteria, merit list, merit percentage
    if any(k in normalized for k in ['merit', 'merit list', 'merit percentage', 'merit score', 'merit criteria', 'merit required']):
        return 'admission_merit'
    
    # entry_test: entry test details, syllabus, preparation
    if any(k in normalized for k in ['entry test', 'entry_test', 'test', 'preparation', 'syllabus', 'questions', 'test pattern', 'how to prepare']):
        return 'entry_test'
    
    # admission_documents: required documents, papers
    if any(k in normalized for k in ['document', 'documents', 'required', 'papers', 'form', 'upload', 'submit doc']):
        return 'admission_documents'
    
    # admission_process: step by step process, how
    if any(k in normalized for k in ['process', 'step', 'how', 'procedure', 'guide', 'batao']):
        return 'apply_admission'
    
    # admission_open: is admission open, when does admission open
    if any(k in normalized for k in ['admission_open', 'when admission', 'admission status']):
        return 'admission_open'
    
    # Default to general admission summary
    return 'apply_admission'


def _classify_scholarship_subtype(text):
    """Classify scholarship question into specific subtypes."""
    q = (text or '').lower()
    
    # merit_scholarship
    if 'merit' in q or 'merit scholarship' in q or 'merit based' in q:
        return 'merit_scholarship'
    
    # need_based_Scholarships
    if any(k in q for k in ['need', 'need based', 'financial aid', 'need-based']):
        return 'need_based_Scholarships'
    
    # kinship_scholarship
    if 'kinship' in q or 'sibling' in q or 'brother' in q or 'sister' in q:
        return 'kinship_scholarship'
    
    # sports_scholarship
    if 'sports' in q or 'athletic' in q:
        return 'sports_scholarship'
    
    # hafiz_scholarship
    if 'hafiz' in q or 'quran' in q:
        return 'hafiz_scholarship'
    
    # employee_scholarship
    if 'employee' in q or 'employee kids' in q:
        return 'employee_scholarship'
    
    # Default to general scholarship
    return 'Scholarship_general'


def _build_question_profile(text):
    """Create comprehensive structured understanding of question for routing accuracy."""
    q = _normalize_query_for_understanding(text)
    fee_type = _extract_fee_query_type(q)
    primary_domain = _classify_primary_domain(text)
    
    # Classify specific subtypes for admission and scholarship
    admission_subtype = _classify_admission_subtype(text) if primary_domain == 'admission' else None
    scholarship_subtype = _classify_scholarship_subtype(text) if primary_domain == 'scholarship' else None

    # Program-related intent flags
    asks_program_count = any(k in q for k in ['how many programs', 'number of programs', 'program count', 'how many courses'])
    asks_degree_count = any(k in q for k in ['how many degree', 'how many degrees', 'number of degree', 'number of degrees', 'how many program', 'how many bachelors'])
    asks_offered = (
        q.startswith('is ') or
        q.startswith('do you offer') or
        q.startswith('is there') or
        ' offered' in q or
        'offered by the university' in q or
        'offer by the university' in q
    ) and not any(k in q for k in ['fee', 'tuition', 'misc', 'hostel', 'admission fee'])
    asks_faculty_list = 'faculty' in q or 'department' in q
    asks_programs_in_faculty = any(k in q for k in ['program in', 'programs in', 'which programs', 'what programs', 'list programs', 'courses in'])
    asks_fee = any(k in q for k in ['fee', 'tuition', 'charges', 'cost', 'price'])
    asks_hostel_fee = fee_type == 'hostel'

    # Admission-related intent flags
    asks_admission_apply = any(k in q for k in ['apply', 'application', 'how to apply', 'application process', 'application mode', 'register', 'enroll'])
    asks_admission_deadline = any(k in q for k in ['deadline', 'last date', 'closing', 'when', 'kab tak'])
    asks_admission_merit = any(k in q for k in ['merit', 'merit list', 'merit percentage', 'merit score'])
    asks_entry_test = any(k in q for k in ['entry test', 'entry_test', 'test', 'preparation', 'syllabus'])
    asks_admission_documents = any(k in q for k in ['document', 'documents', 'required', 'papers'])
    asks_admission_process = any(k in q for k in ['process', 'step', 'procedure', 'guide'])
    asks_admission_open = any(k in q for k in ['admission open', 'when', 'is admission', 'admission status'])

    # Scholarship-related intent flags
    asks_scholarship = any(k in q for k in ['scholarship', 'financial aid'])
    asks_merit_scholarship = 'merit' in q and 'scholarship' in q
    asks_need_based = any(k in q for k in ['need', 'need based', 'financial aid', 'need-based'])
    asks_kinship = 'kinship' in q or 'sibling' in q
    asks_sports = 'sports' in q
    asks_hafiz = 'hafiz' in q

    # Campus-related intent flags
    asks_campus_info = any(k in q for k in ['campus', 'location', 'address', 'where', 'situated', 'city'])
    asks_campus_contact = any(k in q for k in ['phone', 'contact', 'email', 'uan', 'call'])

    # Facilities-related intent flags
    asks_facilities = any(k in q for k in ['facility', 'facilities', 'transport', 'medical', 'healthcare', 'daycare', 'environment', 'infrastructure', 'parking', 'library', 'lab'])

    # Hostel-related intent flags
    asks_hostel_info = any(k in q for k in ['hostel', 'accommodation', 'hostal', 'hostle', 'room', 'security', 'internet', 'wifi', 'lodging', 'residence'])

    profile = {
        'normalized_text': q,
        'primary_domain': primary_domain,
        'admission_subtype': admission_subtype,
        'scholarship_subtype': scholarship_subtype,
        
        # Program flags
        'asks_program_count': asks_program_count,
        'asks_degree_count': asks_degree_count,
        'asks_offered': asks_offered,
        'asks_faculty_list': asks_faculty_list,
        'asks_programs_in_faculty': asks_programs_in_faculty,
        'asks_fee': asks_fee,
        'asks_hostel_fee': asks_hostel_fee,
        'fee_type': fee_type,
        
        # Admission flags
        'asks_admission_apply': asks_admission_apply,
        'asks_admission_deadline': asks_admission_deadline,
        'asks_admission_merit': asks_admission_merit,
        'asks_entry_test': asks_entry_test,
        'asks_admission_documents': asks_admission_documents,
        'asks_admission_process': asks_admission_process,
        'asks_admission_open': asks_admission_open,
        
        # Scholarship flags
        'asks_scholarship': asks_scholarship,
        'asks_merit_scholarship': asks_merit_scholarship,
        'asks_need_based': asks_need_based,
        'asks_kinship': asks_kinship,
        'asks_sports': asks_sports,
        'asks_hafiz': asks_hafiz,
        
        # Campus flags
        'asks_campus_info': asks_campus_info,
        'asks_campus_contact': asks_campus_contact,
        
        # Facilities flags
        'asks_facilities': asks_facilities,
        
        # Hostel flags
        'asks_hostel_info': asks_hostel_info,
    }
    return profile


def _has_structured_signal(profile):
    """Return True when query clearly matches structured local-data intents."""
    if not profile:
        return False

    signals = [
        'asks_program_count',
        'asks_degree_count',
        'asks_offered',
        'asks_faculty_list',
        'asks_programs_in_faculty',
        'asks_fee',
        'asks_hostel_fee',
        'asks_admission_apply',
        'asks_admission_deadline',
        'asks_admission_merit',
        'asks_entry_test',
        'asks_admission_documents',
        'asks_admission_process',
        'asks_admission_open',
        'asks_scholarship',
        'asks_merit_scholarship',
        'asks_need_based',
        'asks_kinship',
        'asks_sports',
        'asks_hafiz',
        'asks_campus_info',
        'asks_campus_contact',
        'asks_facilities',
        'asks_hostel_info',
    ]
    return any(bool(profile.get(key)) for key in signals)


def _process_greeting_query(text):
    """Return a friendly greeting response for simple salutations."""
    q = _normalize_query_for_understanding(text)
    if not q:
        return None

    greeting_patterns = [
        'hello',
        'hi',
        'hey',
        'assalam',
        'salam',
        'walaikum',
        'walaikumassalam',
        'assalamualaikum',
        'good morning',
        'good afternoon',
        'good evening',
    ]

    if not any(pattern in q for pattern in greeting_patterns):
        return None

    # Do not treat a query as a pure greeting if it also contains a domain-specific question.
    domain_indicators = [
        'scholarship', 'financial aid', 'admission', 'apply', 'program', 'course',
        'degree', 'fee', 'tuition', 'deadline', 'campus', 'facility', 'hostel', 'hostal',
        'documents', 'eligibility', 'salary', 'entry_test', 'merit', 'facility', 'library',
        'transport', 'accommodation'
    ]
    if any(k in q for k in domain_indicators):
        return None

    if any(pattern in q for pattern in ['walaikum', 'assalamualaikum', 'assalam', 'salam']):
        response_text = 'Walaikumassalam! How can I help you today with admissions, programs, scholarships, or fees?'
    else:
        response_text = 'Hello! How can I help you today with admissions, programs, scholarships, or fees?'

    return {
        'intent_used': 'greeting_message',
        'natural_response': response_text,
        'answer_source': 'greeting_message',
        'answer_source_confidence': 1.0,
        'admin_verified': True,
        'follow_up': None,
        'program_data': None,
    }


def _infer_program_intent_from_profile(profile):
    """Infer program intent for text endpoint using profile features."""
    if profile.get('asks_fee'):
        if profile.get('fee_type') == 'admission':
            return 'ask_admission_fee'
        return 'ask_fee'
    if profile.get('asks_program_count') or profile.get('asks_degree_count'):
        return 'list_programs'
    if profile.get('asks_programs_in_faculty') or profile.get('asks_faculty_list'):
        return 'list_programs'
    if profile.get('asks_offered'):
        return 'full_info'
    return 'full_info'


def _extract_fee_query_type(text):
    """Detect which fee component user is asking for."""
    q = _normalize_query_for_understanding(text)

    if any(k in q for k in ['hostel fee', 'hostel fees', 'hostel', 'accommodation fee', 'accommodation charges']):
        return 'hostel'
    if any(k in q for k in ['admission fee', 'admission charges', 'entry fee']):
        return 'admission'
    if any(k in q for k in ['tuition fee', 'semester fee', 'first semester fee']):
        return 'tuition'
    if any(k in q for k in ['misc fee', 'miscellaneous fee', 'misc charges', 'other charges']):
        return 'misc'
    if any(k in q for k in ['total fee', 'overall fee', 'complete fee', 'full fee']):
        return 'total'

    # Default generic fee question maps to total fee.
    return 'total'


def _format_fee_answer_by_type(program_data, fee_type):
    """Return accurate fee answer according to requested fee component."""
    if not program_data:
        return "Sorry, I couldn't find that program."

    program = program_data.get('program', 'this program')
    if fee_type == 'admission':
        return f"The admission fee for {program} is {program_data.get('admission_fee', 'N/A')}."
    if fee_type == 'tuition':
        return f"The tuition fee for the 1st semester of {program} is {program_data.get('tuition_fee_first', 'N/A')}."
    if fee_type == 'misc':
        return f"The miscellaneous fee per semester for {program} is {program_data.get('misc_fee', 'N/A')}."
    return f"The total fee for {program} is {program_data.get('total_fee', 'N/A')}."


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


def _normalize_admission_intent(intent_label):
    """Map model intents to admission-query intent names."""
    if not intent_label:
        return ''

    label = str(intent_label).strip()
    mapping = {
        'apply_admission': 'ask_admission_process',  # How to apply
        'admission_last_date': 'ask_admission_deadline',  # Deadline
        'admission_merit': 'ask_admission_merit',  # Merit criteria
        'entry_test': 'ask_entry_test',  # Entry test details
        'admission_open': 'ask_admission_summary',  # Is admission open
        'admission_documents': 'ask_admission_documents',  # Required docs
        'documents_inquiry': 'ask_admission_documents',
        'timing_info': 'ask_admission_deadline',
        'University_Info': 'ask_admission_summary',
        'general_info': 'ask_admission_summary',
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
        profile = _build_question_profile(text)
        q = profile['normalized_text']

        # Conversation-intent helpers for program exploration.
        asks_program_count = profile['asks_program_count']
        asks_degree_count = profile['asks_degree_count']
        asks_offered = program_name is not None and profile['asks_offered']
        asks_faculty_list = profile['asks_faculty_list'] and level is not None and faculty is None
        asks_programs_in_faculty = (
            faculty is not None and (
                profile['asks_programs_in_faculty'] or 'what are in' in q or 'which are in' in q or 'list' in q or normalized_intent == 'list_programs'
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
                if normalized_intent == 'ask_fee':
                    fee_type = profile['fee_type']
                    if fee_type == 'hostel':
                        # Hostel fee is not part of current program CSV, so route to realtime source.
                        natural_response = (
                            "Sorry, I couldn't find hostel fee in the current CSV data. "
                            "Please hold while I check the latest university data."
                        )
                    else:
                        natural_response = _format_fee_answer_by_type(program_data, fee_type)
                elif normalized_intent == 'ask_admission_fee':
                    natural_response = _format_fee_answer_by_type(program_data, 'admission')
                else:
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
    """Process scholarship-related queries with specific type routing."""
    try:
        retriever, formatter = _get_scholarship_services()
        if not retriever or not formatter:
            return {'scholarship_data': None, 'natural_response': None}

        q = (text or '').lower()
        profile = _build_question_profile(text)
        scholarship_subtype = profile.get('scholarship_subtype') or _classify_scholarship_subtype(text)
        level = retriever.extract_level(text)
        category = retriever.extract_category(text)
        normalized_intent = _normalize_scholarship_intent(intent_label)

        asks_count = any(k in q for k in ['how many scholarship', 'how many scholarships', 'number of scholarship', 'number of scholarships', 'scholarship count'])
        asks_documents = any(k in q for k in ['document', 'documents', 'papers required', 'required docs', 'requirements'])
        asks_list = any(k in q for k in ['list', 'show', 'available', 'what scholarships', 'which scholarships'])

        # Route based on specific scholarship type first
        if scholarship_subtype in ['merit_scholarship', 'need_based_Scholarships', 'kinship_scholarship', 'sports_scholarship', 'hafiz_scholarship', 'employee_scholarship']:
            # Map subtype to category
            subtype_to_category = {
                'merit_scholarship': 'Merit',
                'need_based_Scholarships': 'Need Based',
                'kinship_scholarship': 'Kinship',
                'sports_scholarship': 'Sports',
                'hafiz_scholarship': 'Hafiz',
                'employee_scholarship': 'Employee',
            }
            category = subtype_to_category.get(scholarship_subtype, category)
            
            if category:
                policies = retriever.get_category_details(category, level)
                if asks_documents or 'document' in q or 'required' in q:
                    natural_response = formatter.format_scholarship_documents(policies, category, level)
                    intent_used = 'ask_scholarship_documents'
                else:
                    natural_response = formatter.format_scholarship_details(policies, category, level)
                    intent_used = 'ask_scholarship_details'
                return {
                    'scholarship_data': policies,
                    'scholarship_category': category,
                    'scholarship_type': scholarship_subtype,
                    'level': level,
                    'intent_used': intent_used,
                    'natural_response': natural_response,
                    'follow_up': None,
                }

        # Fallback to standard routing
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


def _process_admission_query(text, intent_label):
    """Process admission-related queries with comprehensive subtype routing."""
    try:
        retriever, formatter = _get_admission_services()
        if not retriever or not formatter:
            return {'admission_data': None, 'natural_response': None}

        q = (text or '').lower()
        profile = _build_question_profile(text)
        admission_subtype = profile.get('admission_subtype') or _classify_admission_subtype(text)
        normalized_intent = _normalize_admission_intent(intent_label)
        
        # Retrieve all admission data components
        summary = retriever.get_summary()
        deadlines = retriever.get_deadlines()
        process = retriever.get_process()
        eligibility = retriever.get_eligibility()
        documents = retriever.get_documents()
        notes = retriever.get_notes()

        # Specific subtype routing
        if admission_subtype == 'admission_last_date' or profile['asks_admission_deadline']:
            return {
                'admission_data': {'deadlines': deadlines},
                'admission_subtype': 'admission_last_date',
                'intent_used': 'ask_admission_deadline',
                'natural_response': formatter.format_admission_deadlines(deadlines),
                'follow_up': None,
            }

        if admission_subtype == 'admission_merit' or profile['asks_admission_merit']:
            # Merit info is part of eligibility
            return {
                'admission_data': {'eligibility': eligibility, 'merit_focused': True},
                'admission_subtype': 'admission_merit',
                'intent_used': 'ask_admission_merit',
                'natural_response': formatter.format_admission_eligibility(eligibility),
                'follow_up': None,
            }

        if admission_subtype == 'entry_test' or profile['asks_entry_test']:
            # Entry test info is part of eligibility
            return {
                'admission_data': {'eligibility': eligibility, 'entry_test_focused': True},
                'admission_subtype': 'entry_test',
                'intent_used': 'ask_entry_test',
                'natural_response': formatter.format_admission_eligibility(eligibility),
                'follow_up': None,
            }

        if admission_subtype == 'admission_documents' or profile['asks_admission_documents']:
            return {
                'admission_data': {'documents': documents},
                'admission_subtype': 'admission_documents',
                'intent_used': 'ask_admission_documents',
                'natural_response': formatter.format_admission_documents(documents),
                'follow_up': None,
            }

        if admission_subtype == 'apply_admission' or profile['asks_admission_apply'] or profile['asks_admission_process']:
            return {
                'admission_data': {'process': process},
                'admission_subtype': 'apply_admission',
                'intent_used': 'ask_admission_process',
                'natural_response': formatter.format_admission_process(process),
                'follow_up': None,
            }

        if admission_subtype == 'admission_open' or profile['asks_admission_open']:
            return {
                'admission_data': summary,
                'admission_subtype': 'admission_open',
                'intent_used': 'ask_admission_summary',
                'natural_response': formatter.format_admission_summary(summary),
                'follow_up': None,
            }

        # Default: comprehensive admission summary with all components
        full_answer = formatter.format_full_admission_info(summary, deadlines, process, eligibility, documents, notes)
        return {
            'admission_data': {
                'summary': summary,
                'deadlines': deadlines,
                'process': process,
                'eligibility': eligibility,
                'documents': documents,
                'notes': notes,
            },
            'admission_subtype': 'general_admission',
            'intent_used': 'ask_admission_summary',
            'natural_response': full_answer,
            'follow_up': None,
        }

    except Exception as e:
        logger.error(f'Admission query processing failed: {str(e)}')
        return {'admission_data': None, 'natural_response': None}


def _process_campus_query(text):
    """Process campus information queries using CampusesInfoRetriever."""
    try:
        retriever = _get_campuses_retriever()
        if not retriever:
            return {'campus_data': None, 'natural_response': 'Campus information data not available.'}
        
        q = _normalize_query_for_understanding(text)
        
        # Extract campus name from query if possible
        campuses = retriever.get_all_campuses()
        campus_name = None
        for campus in campuses:
            if campus.lower() in q:
                campus_name = campus
                break
        
        # Try to get specific campus information if name found
        if campus_name:
            campus_info = retriever.get_campus_by_name(campus_name)
            if campus_info:
                response = (
                    f"**{campus_info['campus_name']}** is located in {campus_info['location']}. "
                    f"It focuses on {campus_info['focus']}. "
                    f"Contact: {campus_info['phone']} | Email: {campus_info['email']}"
                )
                return {
                    'campus_data': {'campus': campus_info},
                    'natural_response': response,
                }
        
        # Check for contact information request
        if any(k in q for k in ['contact', 'phone', 'email', 'uan', 'call']):
            all_campuses = retriever.get_all_campuses_summary()
            response = "Here are all our campuses:\n"
            for campus in all_campuses:
                response += f"• {campus['campus_name']} - {campus['location']}\n"
            return {
                'campus_data': {'all_campuses': all_campuses},
                'natural_response': response,
            }
        
        # Default: list all campuses
        all_campuses = retriever.get_all_campuses_summary()
        response = "We have the following campuses:\n"
        for campus in all_campuses:
            response += f"• {campus['campus_name']} - {campus['location']} (Focus: {campus['focus']})\n"
        
        return {
            'campus_data': {'all_campuses': all_campuses},
            'natural_response': response,
        }
    except Exception as e:
        logger.error(f'Campus query processing failed: {str(e)}')
        return {'campus_data': None, 'natural_response': None}


def _process_facilities_query(text):
    """Process facilities information queries using FacilitiesRetriever."""
    try:
        retriever = _get_facilities_retriever()
        if not retriever:
            return {'facilities_data': None, 'natural_response': 'Facilities information data not available.'}
        
        q = _normalize_query_for_understanding(text)
        
        # Try searching by keyword
        search_results = retriever.search_facilities(q)
        if search_results:
            response = "We provide the following facilities:\n"
            for facility in search_results:
                response += f"• **{facility['facility_name']}** ({facility['category']}): {facility['feature']} - {facility['details']}\n"
            return {
                'facilities_data': {'facilities': search_results},
                'natural_response': response,
            }
        
        # Extract category if possible
        categories = retriever.get_all_categories()
        category_found = None
        for category in categories:
            if category.lower() in q:
                category_found = category
                break
        
        if category_found:
            facilities = retriever.get_facilities_by_category(category_found)
            if facilities:
                response = f"**{category_found}** Facilities:\n"
                for facility in facilities:
                    response += f"• {facility['feature']}: {facility['details']}\n"
                return {
                    'facilities_data': {'facilities': facilities, 'category': category_found},
                    'natural_response': response,
                }
        
        # Default: list all facilities
        all_facilities = retriever.get_all_facilities_summary()
        response = "Our facilities include:\n"
        for facility in all_facilities:
            response += f"• **{facility['facility_name']}** ({facility['category']}): {facility['feature']}\n"
        
        return {
            'facilities_data': {'facilities': all_facilities},
            'natural_response': response,
        }
    except Exception as e:
        logger.error(f'Facilities query processing failed: {str(e)}')
        return {'facilities_data': None, 'natural_response': None}


def _process_hostel_query(text):
    """Process hostel/accommodation information queries using HostalRetriever."""
    try:
        retriever = _get_hostal_retriever()
        if not retriever:
            return {'hostel_data': None, 'natural_response': 'Hostel information data not available.'}
        
        q = _normalize_query_for_understanding(text)

        def _is_short_facility_question(question_text):
            terms = question_text.lower()
            return any(keyword in terms for keyword in [
                'wifi', 'wi-fi', 'internet', 'security', 'laundry', 'mess', 'food', 'room', 'rooms',
                'hostel', 'hostal', 'accommodation', 'availability', 'available', 'available in hostel',
                'atm',
            ])

        def _build_one_line_answer(question_text, details):
            q_lower = question_text.lower()
            details_text = ' '.join(
                f"{item.get('category', '')} {item.get('sub_category', '')} {item.get('feature', '')} {item.get('details', '')}"
                for item in details
            ).lower()

            if any(term in q_lower for term in ['wifi', 'wi-fi', 'internet']):
                if any(term in details_text for term in ['wifi', 'wi-fi', 'internet']):
                    return 'Yes, Wi-Fi is available in the hostel'
                return 'No, Wi-Fi is not available in the hostel'

            if 'security' in q_lower:
                if any(term in details_text for term in ['security', 'surveillance']):
                    return 'Yes, hostel security is available'
                return 'No, hostel security is not listed'

            if 'laundry' in q_lower:
                if 'laundry' in details_text:
                    return 'Yes, laundry is available in the hostel'
                return 'No, laundry is not listed for the hostel'

            if any(term in q_lower for term in ['mess', 'food', 'meal']):
                if any(term in details_text for term in ['mess', 'food', 'meal', 'meal plan']):
                    return 'Yes, mess/food service is available in the hostel'
                return 'No, mess/food service is not listed for the hostel'

            if 'atm' in q_lower:
                if 'atm' in details_text:
                    return 'Yes, ATM facility is available in the hostel'
                return 'No, ATM is not listed for the hostel'

            if any(term in q_lower for term in ['room', 'rooms', 'accommodation']):
                if any(term in details_text for term in ['separate hostel', 'room', 'accommodation']):
                    return 'Yes, hostel rooms are available in the hostel'
                return 'No, hostel rooms are not listed'

            return ''
        
        # Detect "which facilities" / "what facilities" questions and return concise facilities summary EARLY
        q_lower = q.lower()
        if any(term in q_lower for term in ['which facilit', 'what facilit', 'list facilit']):
            facilities_summary = 'Our hostels feature fully furnished rooms, 24/7 security, high-speed Wi-Fi, housekeeping and laundry services, on-site dining with mess and tuck shop, healthcare clinic, ATM, and recreational common areas [hostal]'
            return {
                'hostel_data': None,
                'natural_response': facilities_summary,
            }
        
        # Try searching by keyword
        search_results = retriever.search_hostel_info(q)
        if search_results and _is_short_facility_question(q):
            short_answer = _build_one_line_answer(q, search_results)
            if short_answer:
                return {
                    'hostel_data': {'hostel_info': search_results},
                    'natural_response': short_answer,
                }

        if search_results:
            response = "Hostel Information:\n"
            for detail in search_results:
                response += f"• **{detail['category']}** - {detail['feature']}: {detail['details']}\n"
            return {
                'hostel_data': {'hostel_info': search_results},
                'natural_response': response,
            }
        
        # Extract category if possible
        categories = retriever.get_all_categories()
        category_found = None
        for category in categories:
            if category.lower() in q:
                category_found = category
                break
        
        if category_found:
            details = retriever.get_details_by_category(category_found)
            if details:
                if _is_short_facility_question(q):
                    short_answer = _build_one_line_answer(q, details)
                    if short_answer:
                        return {
                            'hostel_data': {'hostel_info': details, 'category': category_found},
                            'natural_response': short_answer,
                        }

                response = f"**{category_found}**:\n"
                for detail in details:
                    response += f"• {detail['feature']}: {detail['details']}\n"
                return {
                    'hostel_data': {'hostel_info': details, 'category': category_found},
                    'natural_response': response,
                }
        
        # Default: keep the response short so narrow hostel questions do not expand into an overview.
        if _is_short_facility_question(q):
            return {
                'hostel_data': None,
                'natural_response': 'This hostel feature is not clearly listed in our database [hostal]',
            }

        overview = retriever.get_accommodation_overview()
        response = "Our Accommodation Features:\n"
        for category, features in overview.items():
            response += f"**{category}:**\n"
            for feature in features:
                response += f"  • {feature['feature']}: {feature['details']}\n"
        
        return {
            'hostel_data': {'accommodation_overview': overview},
            'natural_response': response,
        }
    except Exception as e:
        logger.error(f'Hostel query processing failed: {str(e)}')
        return {'hostel_data': None, 'natural_response': None}


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
    t = _normalize_query_for_understanding(text)
    if not t:
        return None

    if any(k in t for k in ['entry_test', 'test pattern', 'test syllabus', 'test preparation']):
        return {'label': 'entry_test', 'confidence': 0.95}
    if any(k in t for k in ['merit_list', 'merit score', 'merit criteria', 'merit percentage']) and 'scholarship' not in t:
        return {'label': 'admission_merit', 'confidence': 0.94}
    if any(k in t for k in ['deadline', 'last day', 'final date']) and 'scholarship' not in t:
        return {'label': 'admission_last_date', 'confidence': 0.94}
    if any(k in t for k in ['apply', 'application', 'enroll', 'registration']) and 'scholarship' not in t:
        return {'label': 'apply_admission', 'confidence': 0.92}
    if any(k in t for k in ['documents', 'document', 'required docs']) and 'scholarship' not in t:
        return {'label': 'documents_inquiry', 'confidence': 0.92}
    if any(k in t for k in ['admission fee', 'entry fee']):
        return {'label': 'admission_fee', 'confidence': 0.93}
    if any(k in t for k in ['tuition fee', 'semester fee', 'misc fee', 'hostel fee', 'total fee', 'fee', 'charges']):
        return {'label': 'fee_inquiry', 'confidence': 0.91}

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


def _primary_domain_from_groq_data_source(data_source):
    """Map Groq NLU data_source values to local primary domain names."""
    if not data_source:
        return None

    source = str(data_source).strip().lower()
    mapping = {
        'programs': 'programs',
        'admission_policy': 'admission',
        'scholarship_policy': 'scholarship',
        'campuses_info': 'campus',
        'facilities': 'facilities',
        'hostal': 'hostel',
        'university_info': 'programs',
    }
    return mapping.get(source)


def _primary_domain_from_groq_intent(intent_label):
    """Map Groq intent labels to local primary domain hints."""
    if not intent_label:
        return None

    normalized = str(intent_label).strip().lower()
    if 'scholarship' in normalized or 'financial aid' in normalized:
        return 'scholarship'
    if normalized.startswith('ask_admission') or 'admission' in normalized or 'apply_' in normalized or 'entry_test' in normalized or 'documents' in normalized:
        return 'admission'
    if 'campus' in normalized:
        return 'campus'
    if 'facility' in normalized or 'hostel' in normalized or 'hostal' in normalized:
        return 'hostel' if 'hostel' in normalized or 'hostal' in normalized else 'facilities'
    if 'program' in normalized or 'degree' in normalized or 'course' in normalized:
        return 'programs'
    return None


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

    if any(w in t for w in ['last date', 'deadline', 'closing date']):
        return {'label': 'admission_last_date', 'confidence': 0.62}
    if any(w in t for w in ['entry test', 'entry_test', 'test syllabus', 'test pattern']):
        return {'label': 'entry_test', 'confidence': 0.62}
    if any(w in t for w in ['admission', 'apply', 'application', 'enroll']):
        return {'label': 'apply_admission', 'confidence': 0.62}
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

    # Preserve short hostel answers exactly; these should stay to-the-point.
    if '[hostal]' in text.lower() and len(text) <= 140:
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

    # Load Twilio config from DB (admin-controlled)
    tw_cfg = get_active_twilio_config()
    twilio_enabled = bool(tw_cfg.get('enabled')) or _twilio_env_configured()
    if not twilio_enabled:
        # If Twilio handling is disabled in admin, respond with a minimal TwiML and do not proceed.
        resp_disabled = VoiceResponse()
        resp_disabled.say(
            "The phone system is currently disabled. Please try again later.",
            voice='alice',
            language='en-US'
        )
        return HttpResponse(str(resp_disabled), content_type='text/xml')
    
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
    
    # Say greeting message using configured greeting text (admin editable)
    greeting = tw_cfg.get('greeting_text') or (
        "Hello! This is GenCall AI speaking. Thank you for calling us. We are excited to assist you today."
    )
    response.say(greeting, voice='alice', language='en-US')
    
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
        
        # Prefer DB-configured Twilio credentials, fall back to environment settings
        tw_cfg = get_active_twilio_config()
        account_sid = tw_cfg.get('account_sid') or settings.TWILIO_ACCOUNT_SID
        api_key_sid = tw_cfg.get('api_key_sid') or settings.TWILIO_API_KEY_SID
        api_key_secret = tw_cfg.get('api_key_secret') or settings.TWILIO_API_KEY_SECRET

        # Create access token with actual current time
        token = AccessToken(
            account_sid,
            api_key_sid,
            api_key_secret,
            identity=identity,
            ttl=3600,  # 1 hour
            nbf=actual_time  # Use actual current time
        )
        
        # Create a Voice grant and add to token
        twiml_app_sid = tw_cfg.get('twiml_app_sid') or settings.TWIML_APP_SID
        voice_grant = VoiceGrant(
            outgoing_application_sid=twiml_app_sid,
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
    tw_cfg = get_active_twilio_config()
    from_number = tw_cfg.get('phone_number') or settings.TWILIO_PHONE_NUMBER
    
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
    tw_cfg = get_active_twilio_config()
    env_configured = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
    db_enabled = bool(tw_cfg.get('enabled') and tw_cfg.get('account_sid') and tw_cfg.get('auth_token'))
    return Response({
        'message': 'GenCall AI Backend is running!',
        'status': 'ok',
        'twilio_configured': db_enabled or env_configured,
        'twilio_db_enabled': db_enabled,
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
        raw_transcript = text
        normalized_transcript = _normalize_transcript_with_groq(raw_transcript, detected_language)
        text = normalized_transcript or raw_transcript

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
        configured_nlu_model = _normalize_groq_model(getattr(settings, 'GROQ_NLU_MODEL', 'llama-3.3-70b-versatile'))
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

        # Process program/admission/scholarship queries.
        program_query = None
        scholarship_query = None
        admission_query = None
        fallback_query = None
        query_text = english_transcript or text
        groq_understanding = _groq_rephrase_and_detect_intent(query_text)
        clean_question = groq_understanding.get('clean_question') or query_text
        groq_intent = groq_understanding.get('intent') or 'unknown'
        data_source = groq_understanding.get('data_source', 'university_info')
        data_source_info = groq_understanding.get('data_source_info', '')
        if groq_intent:
            intent = {'label': groq_intent, 'confidence': 0.92}
        query_text = clean_question

        greeting_result = _process_greeting_query(query_text)
        if greeting_result:
            natural_response = greeting_result.get('natural_response')
            return Response({
                'text': text,
                'raw_transcript': raw_transcript,
                'normalized_transcript': normalized_transcript,
                'clean_question': clean_question,
                'groq_intent': greeting_result.get('intent_used', groq_intent),
                'data_source': data_source,
                'data_source_info': data_source_info,
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
                'intent': greeting_result.get('intent_used', groq_intent),
                'intent_normalized': greeting_result.get('intent_used', groq_intent),
                'emotion': emotion,
                'voice_features': voice_features,
                'nlu_model': nlu_model,
                'nlu_parallel': True,
                'program_query': None,
                'scholarship_query': None,
                'admission_query': None,
                'natural_response': natural_response,
                'natural_response_raw': natural_response,
                'program_data': None,
                'scholarship_data': None,
                'admission_data': None,
                'realtime_data': None,
                'botpress_data': None,
                'program_faculty': None,
                'scholarship_category': None,
                'follow_up': None,
                'answer_source': greeting_result.get('answer_source', 'greeting_message'),
                'answer_source_confidence': greeting_result.get('answer_source_confidence', 1.0),
                'admin_verified': greeting_result.get('admin_verified', True),
            })
        profile = _build_question_profile(query_text)
        primary_domain = profile.get('primary_domain')

        intent_label = (intent or {}).get('label', 'unknown')
        intent_conf = float((intent or {}).get('confidence', 0.0) or 0.0)
        normalized_intent = _normalize_program_intent(intent_label)
        normalized_admission_intent = _normalize_admission_intent(intent_label)
        normalized_scholarship_intent = _normalize_scholarship_intent(intent_label)

        # If model confidence is weak and question doesn't map to known local intents,
        # use the local Groq fallback.
        weak_understanding = (intent_label == 'unknown' or intent_conf < 0.35) and not _has_structured_signal(profile)

        if not weak_understanding:
            if primary_domain == 'admission':
                admission_intent = profile.get('admission_subtype') or normalized_admission_intent
                admission_query = _process_admission_query(query_text, admission_intent)
            elif primary_domain == 'scholarship':
                scholarship_intent = profile.get('scholarship_subtype') or normalized_scholarship_intent
                scholarship_query = _process_scholarship_query(query_text, scholarship_intent)
            else:
                inferred_program_intent = _infer_program_intent_from_profile(profile)
                if normalized_intent in ['ask_fee', 'ask_admission_fee', 'ask_duration', 'ask_semesters', 'full_info', 'list_programs'] and intent_conf >= 0.35:
                    inferred_program_intent = normalized_intent
                program_query = _process_program_query(query_text, inferred_program_intent)

        # Use Groq NLU domain hints when local routing has not created a program/admission/scholarship query.
        if not program_query and not scholarship_query and not admission_query:
            groq_primary_domain = _primary_domain_from_groq_data_source(data_source) or _primary_domain_from_groq_intent(groq_intent)
            if groq_primary_domain == 'scholarship':
                scholarship_intent = normalized_scholarship_intent or 'ask_scholarship_summary'
                scholarship_query = _process_scholarship_query(query_text, scholarship_intent)
            elif groq_primary_domain == 'admission':
                admission_intent = normalized_admission_intent or 'ask_admission_summary'
                admission_query = _process_admission_query(query_text, admission_intent)
            elif groq_primary_domain == 'programs':
                inferred_program_intent = normalized_intent or _infer_program_intent_from_profile(profile)
                program_query = _process_program_query(query_text, inferred_program_intent)

        # Fallback routing when model intent is not in program intents but transcript is clearly a program query.
        if not program_query and not scholarship_query and not admission_query and text:
            fallback_text = (english_transcript or text).lower()
            fallback_intent = None
            fallback_admission_intent = None
            if any(k in fallback_text for k in ['admission', 'deadline', 'documents', 'eligibility', 'entry test', 'interview', 'application mode']):
                fallback_admission_intent = 'ask_admission_summary'
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
            elif fallback_admission_intent:
                admission_query = _process_admission_query(english_transcript or text, fallback_admission_intent)

            if fallback_intent:
                program_query = _process_program_query(english_transcript or text, fallback_intent)

        natural_response = None
        natural_response_raw = None
        response_data = None
        follow_up = None
        program_faculty = None
        scholarship_category = None
        botpress_query = None
        if program_query:
            natural_response_raw = program_query.get('natural_response')
            response_data = program_query.get('program_data')
            follow_up = program_query.get('follow_up')
            program_faculty = program_query.get('faculty')
        elif admission_query:
            natural_response_raw = admission_query.get('natural_response')
            response_data = admission_query.get('admission_data')
            follow_up = admission_query.get('follow_up')
        elif scholarship_query:
            natural_response_raw = scholarship_query.get('natural_response')
            response_data = scholarship_query.get('scholarship_data')
            follow_up = scholarship_query.get('follow_up')
            scholarship_category = scholarship_query.get('scholarship_category')

        answer_source = 'local_dataset'
        answer_source_confidence = 0.88
        admin_verified = None
        if not natural_response_raw:
            fallback_query = _process_external_fallback(
                query_text=english_transcript or text,
                transcript_text=english_transcript or text,
                intent_label=intent_label,
                emotion_label=(emotion or {}).get('label', 'neutral'),
            )
            if fallback_query:
                natural_response_raw = fallback_query.get('natural_response')
                response_data = fallback_query.get('realtime_data')
                follow_up = fallback_query.get('follow_up')
                answer_source = fallback_query.get('answer_source', 'groq_local')
                answer_source_confidence = float(fallback_query.get('answer_source_confidence', 0.92))
                admin_verified = fallback_query.get('admin_verified', False)
            else:
                answer_source = 'none'
                answer_source_confidence = 0.0

        if answer_source == 'groq_local' and natural_response_raw:
            natural_response = natural_response_raw
        elif answer_source != 'botpress_runtime_api' and natural_response_raw:
            natural_response = _humanize_response_fast(
                natural_response_raw,
                emotion_label=(emotion or {}).get('label', 'neutral'),
                language=detected_language,
            )
        else:
            natural_response = natural_response_raw

        return Response({
            'text': text,
            'raw_transcript': raw_transcript,
            'normalized_transcript': normalized_transcript,
            'clean_question': clean_question,
            'groq_intent': groq_intent,
            'data_source': data_source,
            'data_source_info': data_source_info,
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
            'admission_query': admission_query,
            'natural_response': natural_response,
            'natural_response_raw': natural_response_raw,
            'program_data': program_query['program_data'] if program_query else None,
            'scholarship_data': scholarship_query['scholarship_data'] if scholarship_query else None,
            'admission_data': admission_query['admission_data'] if admission_query else None,
            'realtime_data': None,
            'botpress_data': fallback_query.get('realtime_data') if fallback_query else None,
            'program_faculty': program_faculty,
            'scholarship_category': scholarship_category,
            'follow_up': follow_up,
            'answer_source': answer_source,
            'answer_source_confidence': answer_source_confidence,
            'admin_verified': admin_verified,
        })
    except Exception as e:
        logger.error(f"Speech-to-text failed: {str(e)}")
        return Response({'error': f'Speech-to-text failed: {str(e)}'}, status=500)


@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def program_query(request):
    """
    Query programs by name, level, or get fee/duration info.
    Standalone endpoint for program queries (without STT).
    Intelligently routes to programs, scholarships, or admission based on intent.
    
    Request:
    - POST /api/program_query/
    - query: text query (required)
    - level: 'Undergraduate', 'Associate', 'Postgraduate' (optional)
    - emotion: emotion label for humanization (optional)
    """
    query = request.data.get('query', '').strip()
    level = request.data.get('level', '').strip()
    emotion_label = request.data.get('emotion', 'neutral')
    
    if not query:
        return Response({'error': 'Query parameter is required.'}, status=400)
    
    try:
        groq_understanding = _groq_rephrase_and_detect_intent(query)
        clean_question = groq_understanding.get('clean_question') or query
        detected_intent = groq_understanding.get('intent') or 'unknown'
        data_source = groq_understanding.get('data_source', 'university_info')
        data_source_info = groq_understanding.get('data_source_info', '')

        greeting_result = _process_greeting_query(clean_question)
        if greeting_result:
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'greeting',
                'intent': greeting_result.get('intent_used', detected_intent),
                'data_source': 'system_greeting',
                'data_source_info': 'This is a greeting message',
                'program_name': None,
                'level': level or None,
                'faculty': None,
                'program_data': None,
                'scholarship_data': None,
                'admission_data': None,
                'realtime_data': None,
                'natural_response': greeting_result.get('natural_response'),
                'natural_response_raw': greeting_result.get('natural_response'),
                'follow_up': None,
                'answer_source': greeting_result.get('answer_source', 'greeting_message'),
                'answer_source_confidence': greeting_result.get('answer_source_confidence', 1.0),
                'admin_verified': greeting_result.get('admin_verified', True),
                'found': True,
            })

        # Comprehensive question understanding
        profile = _build_question_profile(clean_question)
        primary_domain = profile['primary_domain']

        groq_primary_domain = _primary_domain_from_groq_data_source(data_source) or _primary_domain_from_groq_intent(detected_intent)
        if groq_primary_domain and groq_primary_domain != primary_domain:
            if not _has_structured_signal(profile) or primary_domain == 'programs':
                primary_domain = groq_primary_domain

        fallback_query = None

        # Unknown/unstructured questions should use the local Groq fallback.
        if not _has_structured_signal(profile):
            fallback_query = _process_external_fallback(clean_question, transcript_text=clean_question, emotion_label=emotion_label)
            if fallback_query:
                raw_answer = fallback_query.get('natural_response')
                human_answer = raw_answer
                return Response({
                    'query': query,
                    'clean_question': clean_question,
                    'primary_domain': 'unknown',
                    'intent': detected_intent,
                    'program_name': None,
                    'level': level or None,
                    'faculty': None,
                    'program_data': fallback_query.get('realtime_data'),
                    'scholarship_data': None,
                    'admission_data': None,
                    'realtime_data': fallback_query.get('realtime_data'),
                    'natural_response': human_answer,
                    'natural_response_raw': raw_answer,
                    'follow_up': fallback_query.get('follow_up'),
                    'answer_source': fallback_query.get('answer_source', 'groq_local'),
                    'answer_source_confidence': fallback_query.get('answer_source_confidence', 0.92),
                    'admin_verified': fallback_query.get('admin_verified', False),
                    'found': bool(human_answer),
                })
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'unknown',
                'intent': detected_intent,
                'program_name': None,
                'level': level or None,
                'faculty': None,
                'program_data': None,
                'scholarship_data': None,
                'admission_data': None,
                'realtime_data': None,
                'natural_response': 'Thank you for your question. I could not find a specific answer in the current university dataset. Please ask about programs, admission, scholarships, campus, facilities, or hostel details.',
                'natural_response_raw': 'Thank you for your question. I could not find a specific answer in the current university dataset. Please ask about programs, admission, scholarships, campus, facilities, or hostel details.',
                'follow_up': None,
                'answer_source': 'none',
                'answer_source_confidence': 0.0,
                'admin_verified': False,
                'found': False,
            })
        
        # Route based on primary domain and specific subtypes
        scholarship_result = None
        admission_result = None
        campus_result = None
        facilities_result = None
        hostel_result = None
        query_result = None
        
        if primary_domain == 'admission':
            admission_subtype = profile.get('admission_subtype') or _classify_admission_subtype(clean_question)
            admission_result = _process_admission_query(clean_question, admission_subtype)
        elif primary_domain == 'scholarship':
            scholarship_subtype = profile.get('scholarship_subtype') or _classify_scholarship_subtype(clean_question)
            scholarship_result = _process_scholarship_query(clean_question, scholarship_subtype)
        elif primary_domain == 'campus':
            campus_result = _process_campus_query(clean_question)
        elif primary_domain == 'facilities':
            facilities_result = _process_facilities_query(clean_question)
        elif primary_domain == 'hostel':
            hostel_result = _process_hostel_query(clean_question)
        else:  # programs
            inferred_program_intent = _infer_program_intent_from_profile(profile)
            query_result = _process_program_query(clean_question, inferred_program_intent)
        
        # Extract program/level info for response
        retriever, extractor, formatter = _get_program_services()
        extraction = extractor.extract_program_and_level(clean_question) if extractor else {}
        detected_level = level or extraction.get('level')
        
        # Return admission query response
        if admission_result:
            raw_answer = admission_result.get('natural_response')
            if _is_unresolved_answer(raw_answer):
                fallback_query = _process_external_fallback(clean_question, transcript_text=clean_question, intent_label=admission_result.get('intent_used'), emotion_label=emotion_label)
                if fallback_query:
                    raw_answer = fallback_query.get('natural_response')
                    human_answer = raw_answer
                    return Response({
                        'query': query,
                        'clean_question': clean_question,
                        'primary_domain': 'admission',
                        'admission_subtype': admission_result.get('admission_subtype'),
                        'intent': detected_intent,
                        'program_name': None,
                        'level': detected_level,
                        'faculty': None,
                        'admission_data': fallback_query.get('realtime_data'),
                        'program_data': None,
                        'scholarship_data': None,
                        'natural_response': human_answer,
                        'natural_response_raw': raw_answer,
                        'follow_up': fallback_query.get('follow_up'),
                        'answer_source': fallback_query.get('answer_source', 'groq_local'),
                        'answer_source_confidence': fallback_query.get('answer_source_confidence', 0.92),
                        'admin_verified': fallback_query.get('admin_verified', False),
                        'found': bool(raw_answer),
                    })
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'admission',
                'data_source': data_source,
                'data_source_info': data_source_info,
                'admission_subtype': admission_result.get('admission_subtype'),
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'admission_data': admission_result.get('admission_data'),
                'program_data': None,
                'scholarship_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': admission_result.get('follow_up'),
                'answer_source': 'local_dataset',
                'answer_source_confidence': 0.90,
                'admin_verified': None,
                'found': bool(admission_result.get('admission_data') or human_answer),
            })
        
        # Return scholarship query response
        if scholarship_result:
            detected_scholarship_category = scholarship_result.get('scholarship_category')
            raw_answer = scholarship_result.get('natural_response')
            if _is_unresolved_answer(raw_answer):
                fallback_query = _process_external_fallback(clean_question, transcript_text=clean_question, intent_label=scholarship_result.get('intent_used'), emotion_label=emotion_label)
                if fallback_query:
                    raw_answer = fallback_query.get('natural_response')
                    human_answer = raw_answer
                    return Response({
                        'query': query,
                        'clean_question': clean_question,
                        'primary_domain': 'scholarship',
                        'scholarship_type': scholarship_result.get('scholarship_type'),
                        'intent': detected_intent,
                        'program_name': None,
                        'level': detected_level,
                        'faculty': None,
                        'scholarship_category': detected_scholarship_category,
                        'scholarship_data': fallback_query.get('realtime_data'),
                        'program_data': None,
                        'natural_response': human_answer,
                        'natural_response_raw': raw_answer,
                        'follow_up': fallback_query.get('follow_up'),
                        'answer_source': fallback_query.get('answer_source', 'groq_local'),
                        'answer_source_confidence': fallback_query.get('answer_source_confidence', 0.92),
                        'admin_verified': fallback_query.get('admin_verified', False),
                        'found': bool(raw_answer),
                    })
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'scholarship',
                'data_source': data_source,
                'data_source_info': data_source_info,
                'scholarship_type': scholarship_result.get('scholarship_type'),
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'scholarship_category': detected_scholarship_category,
                'scholarship_data': scholarship_result.get('scholarship_data'),
                'program_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': scholarship_result.get('follow_up'),
                'answer_source': 'local_dataset',
                'answer_source_confidence': 0.90,
                'admin_verified': None,
                'found': bool(scholarship_result.get('scholarship_data') or human_answer),
            })
        
        # Return campus query response
        if campus_result:
            raw_answer = campus_result.get('natural_response')
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'campus',
                'data_source': data_source,
                'data_source_info': data_source_info,
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'campus_data': campus_result.get('campus_data'),
                'program_data': None,
                'scholarship_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': None,
                'answer_source': 'local_dataset',
                'answer_source_confidence': 0.92,
                'admin_verified': None,
                'found': bool(campus_result.get('campus_data') or human_answer),
            })
        
        # Return facilities query response
        if facilities_result:
            raw_answer = facilities_result.get('natural_response')
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'facilities',
                'data_source': data_source,
                'data_source_info': data_source_info,
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'facilities_data': facilities_result.get('facilities_data'),
                'program_data': None,
                'scholarship_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': None,
                'answer_source': 'local_dataset',
                'answer_source_confidence': 0.92,
                'admin_verified': None,
                'found': bool(facilities_result.get('facilities_data') or human_answer),
            })
        
        # Return hostel query response
        if hostel_result:
            raw_answer = hostel_result.get('natural_response')
            human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'hostel',
                'data_source': data_source,
                'data_source_info': data_source_info,
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'hostel_data': hostel_result.get('hostel_data'),
                'program_data': None,
                'scholarship_data': None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': None,
                'answer_source': 'local_dataset',
                'answer_source_confidence': 0.92,
                'admin_verified': None,
                'found': bool(hostel_result.get('hostel_data') or human_answer),
            })

        # Defensive fallback: if no routed handler produced a result, keep response JSON and professional.
        if not query_result:
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': primary_domain,
                'intent': detected_intent,
                'program_name': None,
                'level': detected_level,
                'faculty': None,
                'program_data': None,
                'scholarship_data': None,
                'admission_data': None,
                'realtime_data': None,
                'natural_response': 'Thank you for your question. I could not find a specific answer in the current university dataset. Please ask about programs, admission, scholarship, campus, facilities, or hostel details.',
                'natural_response_raw': 'Thank you for your question. I could not find a specific answer in the current university dataset. Please ask about programs, admission, scholarship, campus, facilities, or hostel details.',
                'follow_up': None,
                'answer_source': 'none',
                'answer_source_confidence': 0.0,
                'admin_verified': False,
                'found': False,
            })

        # Return program query response
        raw_answer = query_result.get('natural_response')
        if _is_unresolved_answer(raw_answer):
            fallback_query = _process_external_fallback(
                clean_question,
                transcript_text=clean_question,
                intent_label=query_result.get('intent_used'),
                emotion_label=emotion_label,
            )
            if fallback_query:
                raw_answer = fallback_query.get('natural_response')
                query_result['program_data'] = fallback_query.get('realtime_data')
                query_result['follow_up'] = fallback_query.get('follow_up')
            human_answer = raw_answer
            return Response({
                'query': query,
                'clean_question': clean_question,
                'primary_domain': 'programs',
                'intent': detected_intent,
                'program_name': query_result.get('program_name'),
                'level': detected_level or query_result.get('level'),
                'faculty': query_result.get('faculty'),
                'program_data': query_result.get('program_data'),
                'scholarship_data': None,
                'admission_data': None,
                'realtime_data': fallback_query.get('realtime_data') if fallback_query else None,
                'natural_response': human_answer,
                'natural_response_raw': raw_answer,
                'follow_up': query_result.get('follow_up'),
                'answer_source': fallback_query.get('answer_source', 'groq_local') if fallback_query else 'none',
                'answer_source_confidence': fallback_query.get('answer_source_confidence', 0.92) if fallback_query else 0.0,
                'admin_verified': fallback_query.get('admin_verified', False) if fallback_query else False,
                'found': bool(raw_answer),
            })

        human_answer = _humanize_response_fast(raw_answer, emotion_label=emotion_label, language='en') if raw_answer else None
        return Response({
            'query': query,
            'clean_question': clean_question,
            'primary_domain': 'programs',
            'intent': detected_intent,
            'program_name': query_result.get('program_name'),
            'level': detected_level or query_result.get('level'),
            'faculty': query_result.get('faculty'),
            'program_data': query_result.get('program_data'),
            'scholarship_data': None,
            'admission_data': None,
            'realtime_data': None,
            'natural_response': human_answer,
            'natural_response_raw': raw_answer,
            'follow_up': query_result.get('follow_up'),
            'answer_source': 'local_dataset',
            'answer_source_confidence': 0.88,
            'admin_verified': None,
            'found': bool(query_result.get('program_data') or human_answer),
        })

    except Exception as e:
        logger.error(f'Program query failed: {str(e)}')
        return Response({'error': f'Query processing failed: {str(e)}'}, status=500)


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
