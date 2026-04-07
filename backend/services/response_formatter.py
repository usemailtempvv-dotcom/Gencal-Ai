"""
Response Formatter: Generate natural language responses for program queries.
Handles different intents and formats answers for users.
"""
import logging

logger = logging.getLogger(__name__)


class ProgramResponseFormatter:
    """Format program query responses into natural language."""

    def __init__(self):
        """Initialize formatter."""
        pass

    def format_program_info(self, program_data):
        """
        Format complete program information.
        
        Args:
            program_data (dict): Program details from data retriever
            
        Returns:
            str: Formatted response
        """
        if not program_data:
            return "Sorry, I couldn't find that program in our system."
        
        program = program_data.get('program', 'Unknown')
        level = program_data.get('level', 'Unknown')
        faculty = program_data.get('faculty', 'Unknown')
        admission = program_data.get('admission_fee', 'N/A')
        total_fee = program_data.get('total_fee', 'N/A')
        semesters = program_data.get('semesters', 'Unknown')
        
        response = f"""
📚 **{program}**

📍 **Level:** {level}
🏫 **Faculty:** {faculty}
💰 **Admission Fee:** {admission}
💵 **Total Fee:** {total_fee}
⏱️ **Duration:** {semesters} semesters

This is a {level.lower()} program offered under the {faculty} faculty.
        """.strip()
        
        return response

    def format_fee_query(self, program_data):
        """
        Format response for fee queries.
        
        Args:
            program_data (dict): Program details
            
        Returns:
            str: Formatted fee response
        """
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        program = program_data.get('program', 'Unknown')
        total_fee = program_data.get('total_fee', 'N/A')
        admission = program_data.get('admission_fee', 'N/A')
        
        response = f"The total fee for {program} is {total_fee}. Additionally, the admission fee is {admission}."
        return response

    def format_duration_query(self, program_data):
        """
        Format response for duration/semester queries.
        
        Args:
            program_data (dict): Program details
            
        Returns:
            str: Formatted duration response
        """
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        program = program_data.get('program', 'Unknown')
        semesters = program_data.get('semesters', 'Unknown')
        
        response = f"{program} is a {semesters}-semester program."
        return response

    def format_admission_fee_query(self, program_data):
        """
        Format response for admission fee queries.
        
        Args:
            program_data (dict): Program details
            
        Returns:
            str: Formatted admission fee response
        """
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        program = program_data.get('program', 'Unknown')
        admission = program_data.get('admission_fee', 'N/A')
        
        response = f"The admission fee for {program} is {admission}."
        return response

    def format_list_programs(self, programs_list, level):
        """
        Format response for listing programs by level.
        
        Args:
            programs_list (list): List of program dicts
            level (str): Academic level
            
        Returns:
            str: Formatted list response
        """
        if not programs_list:
            return f"Sorry, we don't have any {level} programs available."
        
        program_names = [p['program'] for p in programs_list]
        
        response = f"🎓 **{level} Programs Available:**\n\n"
        for i, name in enumerate(program_names, 1):
            response += f"{i}. {name}\n"
        
        response += f"\n_Total: {len(program_names)} {level} programs_"
        return response

    def format_search_results(self, results, query):
        """
        Format response for search results.
        
        Args:
            results (list): Search results
            query (str): Search term
            
        Returns:
            str: Formatted search results
        """
        if not results:
            return f"Sorry, I couldn't find any programs matching '{query}'."
        
        response = f"🔍 **Programs matching '{query}':**\n\n"
        for i, prog in enumerate(results, 1):
            response += f"{i}. **{prog['program']}** ({prog['level']})\n"
            response += f"   Faculty: {prog['faculty']}\n"
            response += f"   Total Fee: {prog['total_fee']}\n\n"
        
        return response.strip()

    def format_response(self, intent_label, program_data, level=None, search_results=None):
        """
        Main formatter: Route to specific response based on intent.
        
        Args:
            intent_label (str): Intent from model (e.g., 'ask_fee', 'ask_duration')
            program_data (dict): Program data from retriever
            level (str): Academic level if applicable
            search_results (list): Search results if applicable
            
        Returns:
            str: Natural language response
        """
        # Map intent to formatting function
        intent_map = {
            'ask_fee': self.format_fee_query,
            'ask_duration': self.format_duration_query,
            'ask_admission_fee': self.format_admission_fee_query,
            'ask_semesters': self.format_duration_query,
            'full_info': self.format_program_info,
            'ask_all_details': self.format_program_info,
        }
        
        # Use mapped formatter or default
        formatter = intent_map.get(intent_label, self.format_program_info)
        
        if intent_label == 'list_programs' and level:
            return self.format_list_programs(program_data or [], level)
        
        if intent_label == 'search_programs' and search_results:
            return self.format_search_results(search_results, program_data)
        
        # Default: pass program_data to formatter
        return formatter(program_data) if program_data else "Sorry, I couldn't find the information you're looking for."

    def format_not_understood(self):
        """Format response when intent is not understood."""
        return "I'm not sure what you're looking for. You can ask me about:\n• Program fees\n• Program duration\n• Program details\n• List of programs by level"

    def format_unable_to_find_program(self, program_name):
        """Format response when program is not found."""
        return f"Sorry, I couldn't find a program called '{program_name}'. Could you please rephrase or provide more details?"

    def format_no_level_specified(self, program_name):
        """Format response when level is ambiguous."""
        return f"I found '{program_name}' but in multiple levels. Could you specify: Undergraduate, Associate, or Postgraduate?"

    def format_ask_level_first(self, levels):
        if not levels:
            return 'Please choose a level: Associate, Undergraduate, or Postgraduate.'
        joined = ', '.join(levels)
        return (
            f"We offer programs in these levels: {joined}. "
            'Please tell me which level you want to explore first.'
        )

    def format_faculties_for_level(self, level, faculties):
        if not faculties:
            return f"I could not find faculties for {level} programs right now."
        items = '\n'.join([f"{idx}. {name}" for idx, name in enumerate(faculties, 1)])
        return (
            f"For {level}, we offer these faculties:\n{items}\n\n"
            'Please tell me which faculty you want, and I will list its programs.'
        )

    def format_programs_for_level_faculty(self, level, faculty, programs):
        if not programs:
            return f"I could not find programs for {level} in {faculty}."
        items = '\n'.join([f"{idx}. {p['program']}" for idx, p in enumerate(programs, 1)])
        return f"Programs in {faculty} ({level}):\n{items}"

    def format_program_count_for_level_faculty(self, level, faculty, programs):
        """Format response for count query within a selected level/faculty."""
        count = len(programs or [])
        if count == 0:
            return f"There are no programs in {faculty} at {level} level right now."

        items = '\n'.join([f"{idx}. {p['program']}" for idx, p in enumerate(programs, 1)])
        return (
            f"{faculty} at {level} level offers {count} programs:\n"
            f"{items}"
        )

    def format_program_offered(self, program_name, is_offered):
        if is_offered:
            return f"Yes, we offer {program_name}."
        return f"No, currently {program_name} is not offered by the university."

    def format_scholarship_summary(self, summary, level=None):
        if not summary:
            return "Sorry, I couldn't find scholarship information right now."

        level_text = f" for {level}" if level else ''
        policy_count = summary.get('policy_count', 0)
        category_count = summary.get('category_count', 0)
        categories = summary.get('categories', []) or []

        response = (
            f"We have {policy_count} scholarship policy entries{level_text} across {category_count} categories."
        )
        if categories:
            response += "\n\nAvailable categories:\n"
            for idx, category in enumerate(categories, 1):
                response += f"{idx}. {category}\n"
        response += "\nAsk me about a category to see criteria and required documents."
        return response.strip()

    def format_scholarship_list(self, policies, level=None):
        if not policies:
            if level:
                return f"Sorry, I couldn't find scholarship policies for {level}."
            return "Sorry, I couldn't find any scholarship policies."

        grouped = {}
        for policy in policies:
            grouped.setdefault(policy['category'], []).append(policy)

        level_text = f" for {level}" if level else ''
        response = f"🎓 **Scholarships{level_text}:**\n\n"
        for idx, (category, rows) in enumerate(grouped.items(), 1):
            first = rows[0]
            response += f"{idx}. **{category}**\n"
            response += f"   Based On: {first.get('based_on', 'N/A')}\n"
            response += f"   Criteria: {first.get('criteria', 'N/A')}\n\n"
        response += f"_Total policies: {len(policies)}_"
        return response.strip()

    def format_scholarship_details(self, policies, category=None, level=None):
        if not policies:
            if category and level:
                return f"Sorry, I couldn't find {category} scholarship details for {level}."
            if category:
                return f"Sorry, I couldn't find scholarship details for {category}."
            return "Sorry, I couldn't find scholarship details."

        header = category or policies[0].get('category', 'Scholarship')
        level_text = f" ({level})" if level else ''
        response = f"🎓 **{header} Scholarship{level_text}:**\n\n"
        for idx, policy in enumerate(policies, 1):
            response += f"{idx}. For: {policy.get('for', 'N/A')}\n"
            response += f"   Based On: {policy.get('based_on', 'N/A')}\n"
            response += f"   Criteria: {policy.get('criteria', 'N/A')}\n"
            response += f"   Documents: {policy.get('documents_required', 'N/A')}\n\n"
        return response.strip()

    def format_scholarship_documents(self, policies, category=None, level=None):
        if not policies:
            if category and level:
                return f"Sorry, I couldn't find required documents for {category} scholarship at {level}."
            if category:
                return f"Sorry, I couldn't find required documents for {category} scholarship."
            return "Sorry, I couldn't find scholarship document requirements."

        docs = []
        for policy in policies:
            document = str(policy.get('documents_required', '')).strip()
            if document and document not in docs:
                docs.append(document)

        header = category or policies[0].get('category', 'Scholarship')
        level_text = f" ({level})" if level else ''
        response = f"📄 **Required Documents for {header} Scholarship{level_text}:**\n\n"
        for idx, document in enumerate(docs, 1):
            response += f"{idx}. {document}\n"
        return response.strip()

    def format_scholarship_count(self, summary, level=None):
        if not summary:
            return "Sorry, I couldn't count the scholarships right now."

        level_text = f" for {level}" if level else ''
        return (
            f"There are {summary.get('policy_count', 0)} scholarship policy entries{level_text} "
            f"across {summary.get('category_count', 0)} scholarship categories."
        )
