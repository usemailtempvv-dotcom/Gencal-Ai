"""
Entity Extractor: Extract program name and level from user transcript.
Handles fuzzy matching, abbreviations, and natural language variations.
"""
import logging
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract program names and academic levels from user queries."""

    def __init__(self, programs_df):
        """
        Initialize with program dataframe.
        
        Args:
            programs_df: Pandas DataFrame with columns ['Program', 'Level', 'Faculty']
        """
        self.programs_df = programs_df
        self.all_programs = programs_df['Program'].unique().tolist()
        self.all_levels = programs_df['Level'].unique().tolist()
        self.all_faculties = programs_df['Faculty'].unique().tolist()
        self._query_stopwords = {
            'what', 'is', 'the', 'fee', 'for', 'of', 'tell', 'me', 'about', 'show',
            'program', 'programs', 'how', 'many', 'semester', 'semesters', 'admission',
            'total', 'tuition', 'please', 'kindly', 'do', 'you', 'have', 'offered',
            'offer', 'university', 'in', 'are', 'which', 'list', 'all', 'under', 'faculty'
        }
        
        # Abbreviation mappings for common program abbreviations
        # Maps abbreviations to actual program names in the CSV
        self.abbreviations = {
            'cs': 'BS Computer Science',  # Maps to actual program name
            'it': 'BS Information Technology',
            'se': 'BS Software Engineering',
            'ai': 'BS Artificial Intelligence',
            'ds': 'BS Data Science',
            'bba': 'BBA (Hons.)',
            'bs': None,  # Generic BS prefix
            'bs commerce': 'BS Commerce',
            'accounting': 'BS Accounting and Finance',
            'fintech': 'BS FinTech',
            'cyber security': 'BS Cyber Security',
            'cybersecurity': 'BS Cyber Security',
            'iiot': 'BS Internet of Things',
            'iot': 'BS Internet of Things',
            'digital marketing': 'BS Digital Marketing',
            'e-commerce': 'BS E-Commerce',
            'ecommerce': 'BS E-Commerce',
            'banking': 'BS Islamic Banking and Finance',
        }
        
        # Level mappings
        self.level_keywords = {
            'undergraduate': ['bs', 'bachelors', 'bachelor degree', 'undergraduate', 'bs hons'],
            'associate': ['associate', 'assosiate', 'assisate', 'diploma', 'ad'],
            'postgraduate': ['ms', 'masters', 'postgraduate', 'phd', 'graduate'],
        }

        self._program_index = []
        for program in self.all_programs:
            normalized = self._normalize_text(program)
            tokens = [t for t in normalized.split() if t and t not in self._query_stopwords]
            self._program_index.append({
                'original': program,
                'normalized': normalized,
                'tokens': set(tokens),
            })

        self._faculty_index = []
        for faculty in self.all_faculties:
            normalized = self._normalize_text(faculty)
            tokens = [t for t in normalized.split() if t and t not in self._query_stopwords]
            self._faculty_index.append({
                'original': faculty,
                'normalized': normalized,
                'tokens': set(tokens),
            })

    def _normalize_text(self, text):
        """Normalize text for robust matching."""
        s = (text or '').lower()
        s = s.replace('&', ' and ')
        s = re.sub(r'\bb\s*\.\s*s\b', 'bs', s)
        s = re.sub(r'\bm\s*\.\s*s\b', 'ms', s)
        s = re.sub(r'\bph\s*\.\s*d\b', 'phd', s)
        s = re.sub(r'[^a-z0-9\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _token_set(self, text):
        norm = self._normalize_text(text)
        return {t for t in norm.split() if t and t not in self._query_stopwords}

    def _normalize_faculty_query(self, text):
        q = self._normalize_text(text)
        q = re.sub(r'\bfaculty\s+of\b', '', q).strip()
        return q

    def extract_level(self, text):
        """
        Extract academic level from transcript.
        
        Args:
            text (str): User transcript
            
        Returns:
            str: 'Undergraduate', 'Associate', 'Postgraduate', or None
        """
        text_lower = self._normalize_text(text)
        
        for level, keywords in self.level_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return level.capitalize()
        
        return None

    def _fuzzy_match(self, query, candidates, threshold=0.6):
        """
        Fuzzy match query against candidates.
        
        Args:
            query (str): Search term
            candidates (list): List of candidate strings
            threshold (float): Minimum similarity ratio
            
        Returns:
            str: Best matching candidate or None
        """
        best_match = None
        best_ratio = threshold
        
        for candidate in candidates:
            ratio = SequenceMatcher(None, query.lower(), candidate.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = candidate
        
        return best_match

    def extract_program(self, text):
        """
        Extract program name from transcript using exact, fuzzy, and abbreviation matching.
        
        Args:
            text (str): User transcript
            
        Returns:
            dict: {'program': 'Program Name', 'matched_type': 'exact'|'fuzzy'|'abbreviation'}
                  or None if no match found
        """
        text_lower = self._normalize_text(text)
        query_tokens = self._token_set(text)
        
        # Try abbreviation matching first
        for abbrev, program_name in self.abbreviations.items():
            if program_name and re.search(rf'\b{re.escape(abbrev)}\b', text_lower):
                # Validate program exists in data
                if program_name in self.all_programs:
                    return {
                        'program': program_name,
                        'matched_type': 'abbreviation'
                    }
        
        # Try normalized exact/containment matching (strongest signal)
        for entry in self._program_index:
            if entry['normalized'] and entry['normalized'] in text_lower:
                return {
                    'program': entry['original'],
                    'matched_type': 'exact'
                }

        # Try strong token overlap matching before fuzzy single-word matching.
        best = None
        best_score = 0.0
        for entry in self._program_index:
            program_tokens = entry['tokens']
            if not program_tokens:
                continue

            overlap = len(query_tokens & program_tokens)
            if overlap == 0:
                continue

            token_recall = overlap / len(program_tokens)
            token_precision = overlap / max(1, len(query_tokens))
            fuzzy_ratio = SequenceMatcher(None, text_lower, entry['normalized']).ratio()
            score = (0.55 * token_recall) + (0.25 * token_precision) + (0.20 * fuzzy_ratio)

            # Penalize generic engineering collisions if software isn't present.
            if 'software' in program_tokens and 'software' in query_tokens:
                score += 0.08

            if score > best_score:
                best_score = score
                best = entry

        if best and best_score >= 0.50:
            return {
                'program': best['original'],
                'matched_type': 'token_overlap'
            }
        
        # Try fuzzy matching on program names (last resort)
        words = text_lower.split()
        for word in words:
            if len(word) > 3:  # Only match meaningful words
                match = self._fuzzy_match(word, self.all_programs, threshold=0.65)
                if match:
                    return {
                        'program': match,
                        'matched_type': 'fuzzy'
                    }
        
        # Try fuzzy matching on full text
        match = self._fuzzy_match(text_lower, self.all_programs, threshold=0.55)
        if match:
            return {
                'program': match,
                'matched_type': 'fuzzy'
            }
        
        return None

    def extract_program_and_level(self, text):
        """
        Extract both program name and level from transcript.
        
        Args:
            text (str): User transcript
            
        Returns:
            dict: {
                'program': 'Program Name' or None,
                'level': 'Undergraduate'|'Associate'|'Postgraduate' or None,
                'program_matched': True|False,
                'level_explicit': True|False
            }
        """
        program_result = self.extract_program(text)
        level = self.extract_level(text)
        
        result = {
            'program': program_result['program'] if program_result else None,
            'program_matched': program_result is not None,
            'program_match_type': program_result['matched_type'] if program_result else None,
            'level': level,
            'level_explicit': level is not None,
            'faculty': self.extract_faculty(text),
        }
        
        # If level not explicit, try to infer from program
        if not level and program_result:
            program_name = program_result['program']
            matching_rows = self.programs_df[self.programs_df['Program'] == program_name]
            if not matching_rows.empty:
                result['level'] = matching_rows.iloc[0]['Level']
                result['level_explicit'] = False
        
        return result

    def extract_faculty(self, text):
        """Extract faculty from transcript with exact/overlap/fuzzy matching."""
        query = self._normalize_faculty_query(text)
        if not query:
            return None

        # Exact contain match first.
        for entry in self._faculty_index:
            if entry['normalized'] and entry['normalized'] in query:
                return entry['original']

        q_tokens = self._token_set(query)
        best = None
        best_score = 0.0
        for entry in self._faculty_index:
            tokens = entry['tokens']
            if not tokens:
                continue
            overlap = len(tokens & q_tokens)
            if overlap == 0:
                continue
            recall = overlap / len(tokens)
            precision = overlap / max(1, len(q_tokens))
            score = 0.7 * recall + 0.3 * precision
            if score > best_score:
                best_score = score
                best = entry['original']

        if best and best_score >= 0.45:
            return best

        fuzzy = self._fuzzy_match(query, self.all_faculties, threshold=0.62)
        return fuzzy
