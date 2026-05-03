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


class AdmissionPolicyRetriever:
    """Retrieve admission policy data from CSV."""

    def __init__(self, csv_path='Data/admission.csv'):
        try:
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded admission CSV with {len(self.df)} rows")
        except Exception as e:
            logger.error(f"Failed to load admission CSV: {str(e)}")
            self.df = pd.DataFrame()

    def _read_csv_with_fallback(self, csv_path):
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                return pd.read_csv(csv_path, encoding=enc)
            except Exception as e:
                last_error = e
        raise last_error

    def get_row(self):
        if self.df.empty:
            return None
        return self.df.iloc[0].to_dict()

    def get_summary(self):
        row = self.get_row()
        if not row:
            return None
        return {
            'university': row.get('University', 'Unknown'),
            'admission_open': row.get('Admission_Open', 'Unknown'),
            'intakes': row.get('Intakes', 'Unknown'),
            'application_mode': row.get('Application_Mode', 'Unknown'),
            'entry_test': row.get('Entry_Test', 'Unknown'),
            'interview': row.get('Interview', 'Unknown'),
            'minimum_qualification': row.get('Minimum_Qualification', 'Unknown'),
            'minimum_marks': row.get('Minimum_Marks', 'Unknown'),
            'admission_confirmation': row.get('Admission_Confirmation', 'Unknown'),
            'required_documents': row.get('Required_Documents', 'Unknown'),
        }

    def get_deadlines(self):
        row = self.get_row()
        if not row:
            return None
        return {
            'spring_start': row.get('Spring_Admission_Start', 'Unknown'),
            'spring_last_date': row.get('Spring_Last_Date', 'Unknown'),
            'spring_deadline_message': row.get('Spring_Deadline_Message', 'Unknown'),
            'fall_start': row.get('Fall_Admission_Start', 'Unknown'),
            'fall_last_date': row.get('Fall_Last_Date', 'Unknown'),
            'fall_deadline_message': row.get('Fall_Deadline_Message', 'Unknown'),
        }

    def get_process(self):
        row = self.get_row()
        if not row:
            return None
        return {
            'application_mode': row.get('Application_Mode', 'Unknown'),
            'application_mode_details': row.get('Application_Mode_Details', 'Unknown'),
            'admission_process': row.get('Admission_Process', 'Unknown'),
            'admission_process_details': row.get('Admission_Process_Details', 'Unknown'),
            'admission_confirmation': row.get('Admission_Confirmation', 'Unknown'),
            'confirmation_details': row.get('Confirmation_Details', 'Unknown'),
        }

    def get_eligibility(self):
        row = self.get_row()
        if not row:
            return None
        return {
            'minimum_qualification': row.get('Minimum_Qualification', 'Unknown'),
            'minimum_marks': row.get('Minimum_Marks', 'Unknown'),
            'eligibility_details': row.get('Eligibility_Details', 'Unknown'),
            'entry_test': row.get('Entry_Test', 'Unknown'),
            'entry_test_type': row.get('Entry_Test_Type', 'Unknown'),
            'entry_test_difficulty': row.get('Entry_Test_Difficulty', 'Unknown'),
            'interview': row.get('Interview', 'Unknown'),
            'interview_details': row.get('Interview_Details', 'Unknown'),
        }

    def get_documents(self):
        row = self.get_row()
        if not row:
            return []
        docs = str(row.get('Required_Documents', '') or '')
        return [item.strip() for item in re.split(r'[;,]', docs) if item.strip()]

    def get_notes(self):
        row = self.get_row()
        if not row:
            return None
        return {
            'student_advice': row.get('Student_Advice', 'Unknown'),
            'general_notes': row.get('General_Notes', 'Unknown'),
        }


class CampusesInfoRetriever:
    """Retrieve campus information data from CSV."""

    def __init__(self, csv_path='Data/Campuses_info.csv'):
        try:
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded campuses CSV with {len(self.df)} campuses")
        except Exception as e:
            logger.error(f"Failed to load campuses CSV: {str(e)}")
            self.df = pd.DataFrame()

    def _read_csv_with_fallback(self, csv_path):
        import csv
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                # Try normal pandas read first with robustness options
                try:
                    df = pd.read_csv(csv_path, encoding=enc, on_bad_lines='skip')
                    # Check if headers were parsed correctly
                    if df.shape[1] >= 6:
                        return df
                except:
                    pass
                
                # If normal parsing fails, try custom parsing
                with open(csv_path, 'r', encoding=enc) as f:
                    reader = csv.reader(f, quotechar='"', skipinitialspace=True)
                    rows = []
                    for row in reader:
                        if row:  # Skip empty rows
                            rows.append(row)
                
                if rows:
                    # First row is headers
                    headers = [h.strip() for h in rows[0]]
                    # Remaining rows are data
                    data_rows = []
                    for row in rows[1:]:
                        if len(row) <= len(headers):
                            data_rows.append([v.strip() for v in row])
                        else:
                            # If row has more columns, merge extra into last column
                            trimmed = row[:len(headers)-1] + [','.join(row[len(headers)-1:])]
                            data_rows.append([v.strip() for v in trimmed])
                    
                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=headers)
                    return df
                    
            except Exception as e:
                last_error = e
        
        raise last_error if last_error else Exception("Could not parse CSV file")

    def get_all_campuses(self):
        """Get all campus names."""
        if self.df.empty:
            return []
        return self.df['campus_name'].unique().tolist()

    def get_campus_by_name(self, campus_name):
        """Get full campus details by name."""
        if self.df.empty:
            return None
        
        query = self.df[self.df['campus_name'].str.strip().str.lower() == campus_name.strip().lower()]
        if query.empty:
            return None
        
        row = query.iloc[0]
        return {
            'campus_name': row['campus_name'],
            'location': row['location'],
            'focus': row['focus'],
            'phone': row['phone'],
            'uan': row['uan'],
            'email': row.get('email', ''),
        }

    def get_all_campuses_summary(self):
        """Get summary of all campuses."""
        if self.df.empty:
            return []
        
        results = []
        for _, row in self.df.iterrows():
            results.append({
                'campus_name': row['campus_name'],
                'location': row['location'],
                'focus': row['focus'],
            })
        return results

    def search_campuses(self, query):
        """Search campuses by keyword (name, location, focus)."""
        if self.df.empty:
            return []
        
        query_lower = query.lower()
        results = []
        
        for _, row in self.df.iterrows():
            campus_lower = row['campus_name'].lower()
            location_lower = row['location'].lower()
            focus_lower = row['focus'].lower()
            
            if query_lower in campus_lower or query_lower in location_lower or query_lower in focus_lower:
                results.append({
                    'campus_name': row['campus_name'],
                    'location': row['location'],
                    'focus': row['focus'],
                    'phone': row['phone'],
                })
        
        return results

    def get_campus_contact(self, campus_name):
        """Get contact info for a campus."""
        campus = self.get_campus_by_name(campus_name)
        if not campus:
            return None
        
        return {
            'campus_name': campus['campus_name'],
            'phone': campus['phone'],
            'uan': campus['uan'],
            'email': campus['email'],
        }


class FacilitiesRetriever:
    """Retrieve facilities information data from CSV."""

    @staticmethod
    def _safe_text(value):
        """Convert NaN/None values to empty strings for JSON-safe responses."""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def __init__(self, csv_path='Data/Facilities.csv'):
        try:
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded facilities CSV with {len(self.df)} facilities")
        except Exception as e:
            logger.error(f"Failed to load facilities CSV: {str(e)}")
            self.df = pd.DataFrame()

    def _read_csv_with_fallback(self, csv_path):
        import csv
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                # Try normal pandas read first with robustness options
                try:
                    df = pd.read_csv(csv_path, encoding=enc, on_bad_lines='skip')
                    # Check if headers were parsed correctly (should have 4 columns)
                    if df.shape[1] >= 4:
                        return df
                except:
                    pass
                
                # If normal parsing fails, try custom parsing
                with open(csv_path, 'r', encoding=enc) as f:
                    reader = csv.reader(f, quotechar='"', skipinitialspace=True)
                    rows = []
                    for row in reader:
                        if row:  # Skip empty rows
                            rows.append(row)
                
                if rows:
                    # First row is headers
                    headers = [h.strip() for h in rows[0]]
                    # Remaining rows are data
                    data_rows = []
                    for row in rows[1:]:
                        if len(row) <= len(headers):
                            data_rows.append([v.strip() for v in row])
                        else:
                            # If row has more columns, merge extra into last column
                            trimmed = row[:len(headers)-1] + [','.join(row[len(headers)-1:])]
                            data_rows.append([v.strip() for v in trimmed])
                    
                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=headers)
                    return df
                    
            except Exception as e:
                last_error = e
        
        raise last_error if last_error else Exception("Could not parse CSV file")

    def get_all_categories(self):
        """Get all facility categories."""
        if self.df.empty:
            return []
        return self.df['category'].unique().tolist()

    def get_facilities_by_category(self, category):
        """Get all facilities in a category."""
        if self.df.empty:
            return []
        
        filtered = self.df[self.df['category'].str.strip().str.lower() == category.strip().lower()]
        
        results = []
        for _, row in filtered.iterrows():
            results.append({
                'facility_name': self._safe_text(row.get('facility_name')),
                'feature': self._safe_text(row.get('feature')),
                'details': self._safe_text(row.get('details')),
            })
        return results

    def get_all_facilities_summary(self):
        """Get summary of all facilities."""
        if self.df.empty:
            return []
        
        results = []
        for _, row in self.df.iterrows():
            results.append({
                'category': self._safe_text(row.get('category')),
                'facility_name': self._safe_text(row.get('facility_name')),
                'feature': self._safe_text(row.get('feature')),
            })
        return results

    def search_facilities(self, query):
        """Search facilities by keyword."""
        if self.df.empty:
            return []
        
        query_lower = query.lower()
        results = []
        
        for _, row in self.df.iterrows():
            facility_name = self._safe_text(row.get('facility_name'))
            feature = self._safe_text(row.get('feature'))
            details = self._safe_text(row.get('details'))
            category = self._safe_text(row.get('category'))

            facility_lower = facility_name.lower()
            feature_lower = feature.lower()
            details_lower = details.lower()
            
            if query_lower in facility_lower or query_lower in feature_lower or query_lower in details_lower:
                results.append({
                    'category': category,
                    'facility_name': facility_name,
                    'feature': feature,
                    'details': details,
                })
        
        return results

    def get_facility_by_name(self, facility_name):
        """Get full details for a specific facility."""
        if self.df.empty:
            return None
        
        query = self.df[self.df['facility_name'].str.strip().str.lower() == facility_name.strip().lower()]
        if query.empty:
            return None
        
        row = query.iloc[0]
        return {
            'category': self._safe_text(row.get('category')),
            'facility_name': self._safe_text(row.get('facility_name')),
            'feature': self._safe_text(row.get('feature')),
            'details': self._safe_text(row.get('details')),
        }


class HostalRetriever:
    """Retrieve hostel/accommodation information data from CSV."""

    def __init__(self, csv_path='Data/hostal.csv'):
        try:
            if not os.path.exists(csv_path):
                csv_path = os.path.join('backend', csv_path)
            if not os.path.exists(csv_path):
                csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)

            self.df = self._read_csv_with_fallback(csv_path)
            self.df.columns = [str(c).strip() for c in self.df.columns]
            logger.info(f"Loaded hostel CSV with {len(self.df)} hostel details")
        except Exception as e:
            logger.error(f"Failed to load hostel CSV: {str(e)}")
            self.df = pd.DataFrame()

    def _read_csv_with_fallback(self, csv_path):
        import csv
        last_error = None
        for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin1'):
            try:
                # Try normal pandas read first with robustness options
                try:
                    df = pd.read_csv(csv_path, encoding=enc, on_bad_lines='skip')
                    # Check if headers were parsed correctly (should have 4 columns)
                    if df.shape[1] >= 4:
                        return df
                except:
                    pass
                
                # If normal parsing fails, try custom parsing
                with open(csv_path, 'r', encoding=enc) as f:
                    reader = csv.reader(f, quotechar='"', skipinitialspace=True)
                    rows = []
                    for row in reader:
                        if row:  # Skip empty rows
                            rows.append(row)
                
                if rows:
                    # First row is headers
                    headers = [h.strip() for h in rows[0]]
                    # Remaining rows are data
                    data_rows = []
                    for row in rows[1:]:
                        if len(row) <= len(headers):
                            data_rows.append([v.strip() for v in row])
                        else:
                            # If row has more columns, merge extra into last column
                            trimmed = row[:len(headers)-1] + [','.join(row[len(headers)-1:])]
                            data_rows.append([v.strip() for v in trimmed])
                    
                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=headers)
                    return df
                    
            except Exception as e:
                last_error = e
        
        raise last_error if last_error else Exception("Could not parse CSV file")

    def get_all_categories(self):
        """Get all hostel categories."""
        if self.df.empty:
            return []
        return self.df['category'].unique().tolist()

    def get_details_by_category(self, category):
        """Get all details in a category."""
        if self.df.empty:
            return []
        
        filtered = self.df[self.df['category'].str.strip().str.lower() == category.strip().lower()]
        
        results = []
        for _, row in filtered.iterrows():
            results.append({
                'sub_category': row.get('sub_category', ''),
                'feature': row['feature'],
                'details': row['details'],
            })
        return results

    def get_all_hostel_details(self):
        """Get all hostel information."""
        if self.df.empty:
            return []
        
        results = []
        for _, row in self.df.iterrows():
            results.append({
                'category': row['category'],
                'sub_category': row.get('sub_category', ''),
                'feature': row['feature'],
                'details': row['details'],
            })
        return results

    def search_hostel_info(self, query):
        """Search hostel information by keyword."""
        if self.df.empty:
            return []
        
        query_lower = str(query or '').lower()
        query_tokens = set(re.findall(r'[a-z0-9]+', query_lower))
        results = []
        
        for _, row in self.df.iterrows():
            category_lower = row['category'].lower()
            sub_category_lower = row.get('sub_category', '').lower()
            feature_lower = str(row['feature']).lower()
            details_lower = str(row['details']).lower()
            haystack = f"{category_lower} {sub_category_lower} {feature_lower} {details_lower}"
            haystack_tokens = set(re.findall(r'[a-z0-9]+', haystack))
            
            if (
                query_lower in haystack
                or bool(query_tokens & haystack_tokens)
                or any(token in haystack for token in query_tokens if len(token) > 2)
            ):
                results.append({
                    'category': row['category'],
                    'sub_category': row.get('sub_category', ''),
                    'feature': row['feature'],
                    'details': row['details'],
                })
        
        return results

    def get_accommodation_overview(self):
        """Get overview of accommodation features."""
        if self.df.empty:
            return {}
        
        overview = {}
        for _, row in self.df.iterrows():
            category = row['category']
            if category not in overview:
                overview[category] = []
            
            overview[category].append({
                'feature': row['feature'],
                'details': row['details'],
            })
        
        return overview
