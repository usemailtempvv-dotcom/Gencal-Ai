"""
Data Retriever: Query CSV data for program information.
Supports filtering by level, program name, and field lookups.
"""
import logging
import pandas as pd
import os
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ProgramDataRetriever:
    """Retrieve program data from CSV."""

    def __init__(self, csv_path='Data/programs.csv'):
        """
        Initialize data retriever with CSV file.
        
        Args:
            csv_path (str): Path to programs.csv relative to Django project root
        """
        try:
            # Try multiple paths
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded programs CSV with {len(self.df)} programs")
        except Exception as e:
            logger.error(f"Failed to load programs CSV: {str(e)}")
            self.df = pd.DataFrame()

    def _read_csv_with_fallback(self, csv_path):
        """Read CSV with encoding fallback for Windows-exported files."""
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                return pd.read_csv(csv_path, encoding=enc)
            except Exception as e:
                last_error = e
        raise last_error

    def get_all_programs(self, level=None):
        """
        Get all programs, optionally filtered by level.
        
        Args:
            level (str): 'Undergraduate', 'Associate', or 'Postgraduate' (optional)
            
        Returns:
            list: List of program names
        """
        if level:
            filtered = self.df[self.df['Level'].str.strip() == level.strip()]
        else:
            filtered = self.df
        
        return filtered['Program'].unique().tolist()

    def get_all_levels(self):
        """Return available academic levels in stable presentation order."""
        ordered = ['Associate', 'Undergraduate', 'Postgraduate']
        present = {str(v).strip() for v in self.df['Level'].dropna().unique().tolist()}
        return [lvl for lvl in ordered if lvl in present]

    def get_faculties_by_level(self, level):
        """Return faculties available for a given level."""
        filtered = self.df[self.df['Level'].str.strip().str.lower() == level.strip().lower()]
        faculties = sorted({str(v).strip() for v in filtered['Faculty'].dropna().tolist()})
        return faculties

    def _normalize_faculty_name(self, faculty_name):
        """Normalize faculty names to improve matching across variants."""
        text = str(faculty_name or '').strip().lower()
        text = text.replace('&', ' and ')
        text = re.sub(r'\bfaculty\s+of\b', '', text)
        text = re.sub(r'\bit\b', 'information technology', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _resolve_faculty_for_level(self, level, faculty):
        """Resolve user-provided faculty to best matching faculty within level."""
        level_filtered = self.df[self.df['Level'].str.strip().str.lower() == level.strip().lower()]
        available = sorted({str(v).strip() for v in level_filtered['Faculty'].dropna().tolist()})
        if not available:
            return faculty

        query_norm = self._normalize_faculty_name(faculty)

        # Exact normalized match first.
        for candidate in available:
            if self._normalize_faculty_name(candidate) == query_norm:
                return candidate

        # Token overlap fallback for close variants.
        q_tokens = set(query_norm.split())
        best = None
        best_score = 0.0
        for candidate in available:
            c_norm = self._normalize_faculty_name(candidate)
            c_tokens = set(c_norm.split())
            if not c_tokens:
                continue
            overlap = len(q_tokens & c_tokens)
            if overlap == 0:
                continue
            recall = overlap / len(c_tokens)
            precision = overlap / max(1, len(q_tokens))
            score = (0.7 * recall) + (0.3 * precision)
            if score > best_score:
                best_score = score
                best = candidate

        return best if best_score >= 0.45 else faculty

    def get_programs_by_level_and_faculty(self, level, faculty):
        """Return programs for a specific level and faculty."""
        resolved_faculty = self._resolve_faculty_for_level(level, faculty)
        filtered = self.df[
            (self.df['Level'].str.strip().str.lower() == level.strip().lower()) &
            (self.df['Faculty'].str.strip().str.lower() == resolved_faculty.strip().lower())
        ]
        result = []
        for _, row in filtered.iterrows():
            result.append({
                'level': row['Level'],
                'faculty': row['Faculty'],
                'program': row['Program'],
                'total_fee': row['Total Fee'],
                'semesters': row['Number of Semesters'],
            })
        return result

    def count_programs_by_level_and_faculty(self, level, faculty):
        """Return number of programs for a specific level and faculty."""
        return len(self.get_programs_by_level_and_faculty(level, faculty))

    def get_program_by_name(self, program_name, level=None):
        """
        Get full program details by name.
        
        Args:
            program_name (str): Program name
            level (str): Optional level to narrow search
            
        Returns:
            dict: Program details or None if not found
        """
        query = self.df[self.df['Program'].str.strip() == program_name.strip()]
        
        if level:
            query = query[query['Level'].str.strip() == level.strip()]
        
        if query.empty:
            return None
        
        row = query.iloc[0]
        return {
            'level': row['Level'],
            'faculty': row['Faculty'],
            'program': row['Program'],
            'admission_fee': row['Admission Fee'],
            'misc_fee': row['Misc. (Per Semester)'],
            'semesters': row['Number of Semesters'],
            'tuition_fee_first': row['Tuition Fee (1st Semester)'],
            'total_fee': row['Total Fee'],
        }

    def is_program_offered(self, program_name, level=None):
        """Check if a program is offered, optionally in a specific level."""
        query = self.df[self.df['Program'].str.strip().str.lower() == program_name.strip().lower()]
        if level:
            query = query[query['Level'].str.strip().str.lower() == level.strip().lower()]
        return not query.empty

    def get_programs_by_level(self, level):
        """
        Get all programs for a specific level.
        
        Args:
            level (str): 'Undergraduate', 'Associate', or 'Postgraduate'
            
        Returns:
            list: List of dicts with program details
        """
        filtered = self.df[self.df['Level'].str.strip() == level.strip()]
        
        result = []
        for _, row in filtered.iterrows():
            result.append({
                'level': row['Level'],
                'faculty': row['Faculty'],
                'program': row['Program'],
                'admission_fee': row['Admission Fee'],
                'tuition_fee_first': row['Tuition Fee (1st Semester)'],
                'total_fee': row['Total Fee'],
                'semesters': row['Number of Semesters'],
            })
        
        return result

    def get_fee_info(self, program_name, level=None):
        """
        Get fee information for a program.
        
        Args:
            program_name (str): Program name
            level (str): Optional level
            
        Returns:
            dict: Fee breakdown or None
        """
        program = self.get_program_by_name(program_name, level)
        if not program:
            return None
        
        return {
            'program': program['program'],
            'admission_fee': program['admission_fee'],
            'misc_fee': program['misc_fee'],
            'tuition_fee_first': program['tuition_fee_first'],
            'total_fee': program['total_fee'],
        }

    def get_duration(self, program_name, level=None):
        """
        Get duration (semesters) for a program.
        
        Args:
            program_name (str): Program name
            level (str): Optional level
            
        Returns:
            dict: Duration info or None
        """
        program = self.get_program_by_name(program_name, level)
        if not program:
            return None
        
        return {
            'program': program['program'],
            'semesters': program['semesters'],
        }

    def search_programs(self, query, level=None):
        """
        Search programs by keyword.
        
        Args:
            query (str): Search term
            level (str): Optional level filter
            
        Returns:
            list: Matching programs
        """
        filtered = self.df
        
        if level:
            filtered = filtered[filtered['Level'].str.strip() == level.strip()]
        
        query_lower = query.lower()
        results = []
        
        for _, row in filtered.iterrows():
            program_lower = row['Program'].lower()
            faculty_lower = row['Faculty'].lower()
            
            if query_lower in program_lower or query_lower in faculty_lower:
                results.append({
                    'level': row['Level'],
                    'faculty': row['Faculty'],
                    'program': row['Program'],
                    'total_fee': row['Total Fee'],
                })
        
        return results


class ScholarshipPolicyRetriever:
    """Retrieve scholarship policy data from CSV."""

    def __init__(self, csv_path='Data/Scholarship_policy.csv'):
        try:
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df = self._normalize_dataframe(self.df)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded scholarship CSV with {len(self.df)} rows")
        except Exception as e:
            logger.error(f"Failed to load scholarship CSV: {str(e)}")
            self.df = pd.DataFrame()

        self.category_keywords = {
            'Merit': ['merit'],
            'Alumni (SGC)': ['sgc', 'alumni sgc', 'sgc alumni'],
            'Alumni (SU)': ['su', 'alumni su', 'su alumni'],
            'Kinship': ['kinship', 'sibling', 'parent', 'spouse'],
            'Women Empowerment': ['women empowerment', 'widow', 'single mother', 'female'],
            'Sports': ['sports'],
            'Talent': ['talent', 'music', 'dramatics', 'naat', 'qirat'],
            'Corporate': ['corporate', 'partner organization', 'employee', 'working professional'],
            'Disability': ['disability'],
            'Martyrs': ['martyr', 'shaheed'],
            'Remote Area': ['remote area', 'gilgit', 'baltistan', 'ajk', 'baluchistan', 'sindh', 'kpk'],
            'Govt/Forces': ['govt', 'government', 'forces', 'armed forces', 'teacher'],
            'Referral': ['referral', 'referred'],
            'PhD': ['phd', 'research'],
            'Loan': ['loan', 'qarz'],
        }

    def _read_csv_with_fallback(self, csv_path):
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                return pd.read_csv(csv_path, encoding=enc)
            except Exception as e:
                last_error = e
        raise last_error

    def _normalize_dataframe(self, df):
        if df.empty:
            return df

        columns = [str(c).strip() for c in df.columns]
        lower_columns = [c.lower() for c in columns]
        if lower_columns == ['column1', 'column2', 'column3', 'column4', 'column5'] and len(df) > 0:
            first_row = [str(v).strip() for v in df.iloc[0].tolist()]
            first_row_lower = [v.lower() for v in first_row]
            if first_row_lower[:5] == ['category', 'for', 'based on', 'criteria', 'documents required']:
                df = df.iloc[1:].copy()
                df.columns = first_row
        return df.reset_index(drop=True)

    def _normalize_text(self, text):
        value = (text or '').lower().replace('&', ' and ')
        value = re.sub(r'[^a-z0-9\s/()-]', ' ', value)
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    def _normalize_level(self, text):
        value = self._normalize_text(text)
        if any(token in value for token in ['associate', 'adp', 'diploma']):
            return 'Associate'
        if any(token in value for token in ['undergraduate', 'ug', 'bs', 'bachelors', 'bachelor']):
            return 'Undergraduate'
        if any(token in value for token in ['postgraduate', 'post grad', 'postgrad', 'ms', 'mphil', 'phd']):
            return 'Postgraduate'
        return None

    def extract_level(self, text):
        """Extract scholarship audience level from a query."""
        return self._normalize_level(text)

    def _row_matches_level(self, level, for_value):
        if not level:
            return True

        normalized_for = self._normalize_text(for_value)
        if 'all programs' in normalized_for:
            return True

        if level == 'Associate':
            return any(token in normalized_for for token in ['ug/adp', 'adp', 'associate'])
        if level == 'Undergraduate':
            return any(token in normalized_for for token in ['ug/adp', 'ug (evening)', 'ug', 'undergraduate', 'adp'])
        if level == 'Postgraduate':
            return any(token in normalized_for for token in ['ms/mphil', 'ug/pg', 'ms', 'mphil', 'phd', 'postgraduate', 'pg'])
        return True

    def _normalize_category(self, category):
        return self._normalize_text(category)

    def extract_category(self, text):
        query = self._normalize_text(text)
        if not query:
            return None

        categories = sorted({str(v).strip() for v in self.df['Category'].dropna().tolist()})

        for category in categories:
            normalized = self._normalize_category(category)
            if normalized and normalized in query:
                return category

        for category, keywords in self.category_keywords.items():
            if any(keyword in query for keyword in keywords):
                return category

        best = None
        best_score = 0.0
        query_tokens = set(query.split())
        for category in categories:
            normalized = self._normalize_category(category)
            cat_tokens = set(normalized.split())
            if not cat_tokens:
                continue
            overlap = len(query_tokens & cat_tokens)
            if overlap == 0:
                continue
            score = (0.7 * (overlap / len(cat_tokens))) + (0.3 * (overlap / max(1, len(query_tokens))))
            score = max(score, SequenceMatcher(None, query, normalized).ratio())
            if score > best_score:
                best_score = score
                best = category

        return best if best_score >= 0.45 else None

    def get_policies(self, level=None, category=None):
        """Return scholarship policies filtered by level and/or category."""
        if self.df.empty:
            return []

        filtered = self.df.copy()
        if level:
            filtered = filtered[filtered['For'].apply(lambda value: self._row_matches_level(level, value))]
        if category:
            category_norm = self._normalize_category(category)
            filtered = filtered[
                filtered['Category'].astype(str).str.lower().str.contains(re.escape(category_norm), regex=True, na=False)
                | filtered['Category'].astype(str).str.lower().eq(category_norm)
            ]

        results = []
        for _, row in filtered.iterrows():
            results.append({
                'category': row['Category'],
                'for': row['For'],
                'based_on': row['Based On'],
                'criteria': row['Criteria'],
                'documents_required': row['Documents Required'],
            })
        return results

    def get_scholarship_levels(self):
        """Return the main scholarship audience groups present in the CSV."""
        if self.df.empty:
            return []

        ordered = ['Associate', 'Undergraduate', 'Postgraduate']
        present = set()
        for_value_series = self.df['For'].dropna().astype(str).tolist()
        for value in for_value_series:
            level = self._normalize_level(value)
            if level:
                present.add(level)
        return [lvl for lvl in ordered if lvl in present]

    def get_summary(self, level=None):
        """Return scholarship counts and available categories."""
        policies = self.get_policies(level=level)
        categories = []
        seen = set()
        for policy in policies:
            category = policy['category']
            if category not in seen:
                seen.add(category)
                categories.append(category)
        return {
            'level': level,
            'policy_count': len(policies),
            'category_count': len(categories),
            'categories': categories,
            'policies': policies,
        }

    def get_category_details(self, category, level=None):
        """Return policy rows for a specific scholarship category."""
        return self.get_policies(level=level, category=category)

    def get_documents(self, category, level=None):
        """Return documents required for a scholarship category."""
        policies = self.get_category_details(category, level)
        documents = []
        for policy in policies:
            doc = str(policy.get('documents_required', '')).strip()
            if doc and doc not in documents:
                documents.append(doc)
        return documents
