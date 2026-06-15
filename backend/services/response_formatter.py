"""
Response Formatter: Generate natural language responses for all query types.
Handles programs, admissions, scholarships, campuses, facilities, hostels, and university info.
"""
import logging

logger = logging.getLogger(__name__)


class AdmissionResponseFormatter:
    """Format admission-related query responses."""

    def format_admission_deadlines(self, deadlines):
        """Format admission deadline information."""
        if not deadlines:
            return "I don't have information about admission deadlines at the moment."
        
        spring = deadlines.get('spring', 'Not specified')
        fall = deadlines.get('fall', 'Not specified')
        
        return f"""Admission Deadlines:

Spring Intake: {spring}
Fall Intake: {fall}

Please apply as early as possible to ensure your application is processed on time."""

    def format_admission_documents(self, documents):
        """Format required documents for admission."""
        if not documents:
            return "Required documents information is not available."
        
        if isinstance(documents, str):
            return f"Required Documents:\n\n{documents}"
        
        response = "Required Documents:\n\n"
        if isinstance(documents, list):
            for i, doc in enumerate(documents, 1):
                response += f"{i}. {doc}\n"
        else:
            response += str(documents)
        
        return response

    def format_admission_process(self, process):
        """Format admission application process."""
        if not process:
            return "Application process information is not available."
        
        if isinstance(process, str):
            return f"Application Process:\n\n{process}"
        
        return f"Application Process:\n\n{process}"

    def format_admission_eligibility(self, eligibility):
        """Format admission eligibility criteria."""
        if not eligibility:
            return "Eligibility information is not available."
        
        if isinstance(eligibility, str):
            return f"Eligibility Criteria:\n\n{eligibility}"
        
        return f"Eligibility Criteria:\n\n{eligibility}"

    def format_admission_summary(self, summary):
        """Format admission status summary."""
        if not summary:
            return "Admission information is not available."
        
        status = summary.get('admission_open', 'Check website for status')
        
        return f"""Admission Status:

Current Status: {status}

For more details about admission deadlines, required documents, eligibility criteria, and application process, please feel free to ask specific questions."""

    def format_full_admission_info(self, summary, deadlines, process, eligibility, documents, notes):
        """Format comprehensive admission information."""
        response = "Complete Admission Information:\n\n"
        
        if summary:
            response += f"Status: {summary.get('admission_open', 'Check website')}\n\n"
        
        if deadlines:
            response += "Deadlines:\n"
            response += f"Spring: {deadlines.get('spring', 'Not specified')}\n"
            response += f"Fall: {deadlines.get('fall', 'Not specified')}\n\n"
        
        if process:
            response += f"Application Process:\n{process}\n\n"
        
        if eligibility:
            response += f"Eligibility: {eligibility}\n\n"
        
        if documents:
            response += f"Required Documents:\n{documents}\n\n"
        
        if notes:
            response += f"Additional Information: {notes}"
        
        return response


class ScholarshipResponseFormatter:
    """Format scholarship query responses."""

    def format_scholarship_details(self, policies, category, level):
        """Format detailed scholarship information."""
        if not policies:
            return f"Information about {category} scholarships is not available."
        
        response = f"{category} Scholarship Details"
        if level:
            response += f" for {level}"
        response += ":\n\n"
        
        if isinstance(policies, list):
            for i, policy in enumerate(policies, 1):
                response += f"Eligibility: {policy.get('for', 'N/A')}\n"
                response += f"Based On: {policy.get('based_on', 'N/A')}\n"
                response += f"Criteria: {policy.get('criteria', 'N/A')}\n"
                response += f"Documents Required: {policy.get('documents_required', 'N/A')}\n\n"
        
        return response

    def format_scholarship_documents(self, policies, category, level):
        """Format required documents for scholarship."""
        if not policies:
            return f"Document information for {category} scholarships is not available."
        
        response = f"Documents Required for {category} Scholarship"
        if level:
            response += f" ({level})"
        response += ":\n\n"
        
        documents = set()
        if isinstance(policies, list):
            for policy in policies:
                doc = policy.get('documents_required', '').strip()
                if doc:
                    documents.add(doc)
        
        if documents:
            for doc in sorted(documents):
                response += f"• {doc}\n"
        else:
            response += "No specific documents listed.\n"
        
        return response

    def format_scholarship_list(self, policies, level=None):
        """Format list of available scholarships."""
        response = "Available Scholarships"
        if level:
            response += f" for {level}"
        response += ":\n\n"
        
        if isinstance(policies, list):
            for i, scholarship in enumerate(policies, 1):
                if isinstance(scholarship, dict):
                    name = scholarship.get('name', scholarship.get('category', f'Scholarship {i}'))
                    response += f"{i}. {name}\n"
                else:
                    response += f"{i}. {scholarship}\n"
        else:
            response += str(policies)
        
        return response

    def format_scholarship_summary(self, summary, level=None):
        """Format scholarship summary."""
        response = "Scholarship Summary"
        if level:
            response += f" for {level}"
        response += ":\n\n"
        
        if isinstance(summary, dict):
            count = summary.get('count', 'Multiple')
            categories = summary.get('categories', [])
            
            response += f"Total Scholarships: {count}\n\n"
            response += "Types Available:\n"
            if isinstance(categories, list):
                for cat in categories:
                    response += f"{cat}\n"
            
            response += "\nWould you like more details about any specific scholarship?"
        
        return response


class CampusResponseFormatter:
    """Format campus and contact information responses."""

    def format_campus_info(self, campus_info):
        """Format specific campus information."""
        if not campus_info:
            return "Campus information is not available."
        
        name = campus_info.get('campus_name', 'Campus')
        location = campus_info.get('location', 'Not specified')
        focus = campus_info.get('focus', 'General programs')
        phone = campus_info.get('phone', 'N/A')
        uan = campus_info.get('uan', 'N/A')
        email = campus_info.get('email', 'N/A')
        
        # Clean up empty values
        if not phone or str(phone).lower() in ('nan', 'n/a', ''):
            phone = 'N/A'
        if not uan or str(uan).lower() in ('nan', 'n/a', ''):
            uan = 'N/A'
        if not email or str(email).lower() in ('nan', 'n/a', ''):
            email = 'N/A'
        
        response = f"""{name}

Location: {location}
Focus: {focus}
Phone: {phone}
UAN: {uan}
Email: {email}

Feel free to contact us for more information about programs, admissions, or any other inquiries."""
        
        return response

    def format_all_campuses(self, campuses):
        """Format all campuses information."""
        if not campuses:
            return "Campus information is not available."
        
        response = "Our Campuses:\n\n"
        
        if isinstance(campuses, list):
            for i, campus in enumerate(campuses, 1):
                if isinstance(campus, dict):
                    name = campus.get('campus_name', 'Campus')
                    location = campus.get('location', 'Location not specified')
                    focus = campus.get('focus', 'General programs')
                    phone = campus.get('phone', 'N/A')
                    
                    response += f"{i}. {name}\n"
                    response += f"   Location: {location}\n"
                    response += f"   Focus: {focus}\n"
                    if phone and phone != 'N/A':
                        response += f"   Phone: {phone}\n"
                    response += "\n"
        
        return response

    def format_contact_info(self, contact):
        """Format contact information."""
        if not contact:
            return "Contact information is not available."
        
        response = "Contact Information:\n\n"
        response += f"{contact}"
        
        return response


class FacilitiesResponseFormatter:
    """Format campus facilities responses."""

    def format_facility_available(self, facility_name):
        """Format response for available facility."""
        return f"{facility_name} is available on our campus. This facility is available for all enrolled students to use."

    def format_facility_details(self, facility_name, details):
        """Format detailed facility information."""
        response = f"{facility_name}:\n\n"
        
        if isinstance(details, str):
            response += details
        elif isinstance(details, dict):
            for key, value in details.items():
                response += f"{key}: {value}\n"
        else:
            response += str(details)
        
        return response

    def format_all_facilities(self, facilities):
        """Format all facilities list."""
        response = "Campus Facilities Available:\n\n"
        
        if isinstance(facilities, list):
            for i, facility in enumerate(facilities, 1):
                response += f"{i}. {facility}\n"
        elif isinstance(facilities, dict):
            for facility, available in facilities.items():
                status = "Yes" if available else "No"
                response += f"{status} - {facility}\n"
        
        return response


class HostelResponseFormatter:
    """Format hostel and accommodation responses."""

    def format_hostel_availability(self, gender):
        """Format hostel availability response."""
        return f"Yes, we have separate hostels for both boys and girls. We offer quality accommodation for {gender} students with modern amenities."

    def format_hostel_details(self, hostel_info):
        """Format detailed hostel information."""
        if not hostel_info:
            return "Hostel information is not available."
        
        response = "Hostel Information:\n\n"
        
        if isinstance(hostel_info, dict):
            rooms = hostel_info.get('rooms', 'Furnished rooms available')
            response += f"Rooms: {rooms}\n"
            
            security = hostel_info.get('security', '24/7 security')
            response += f"Security: {security}\n"
            
            internet = hostel_info.get('internet', 'WiFi available')
            response += f"Internet: {internet}\n"
            
            meals = hostel_info.get('meals', 'Meals provided')
            response += f"Meals: {meals}\n"
            
            response += "\nAll hostels feature:\n"
            response += "Fully furnished rooms with beds, desks, wardrobes\n"
            response += "24/7 security surveillance\n"
            response += "High-speed WiFi\n"
            response += "Mess services with nutritious meals\n"
            response += "Laundry services\n"
            response += "Recreation facilities\n"
            response += "ATM on campus\n"
        else:
            response += str(hostel_info)
        
        return response

    def format_hostel_features(self, features):
        """Format hostel features list."""
        response = "Hostel Features:\n\n"
        
        if isinstance(features, list):
            for feature in features:
                response += f"{feature}\n"
        
        return response


class UniversityInfoResponseFormatter:
    """Format general university information responses."""

    def format_university_name(self, name):
        """Format university name response."""
        return f"The university is {name}."

    def format_university_type(self, uni_type):
        """Format university type response."""
        return f"Superior University is a {uni_type} university in Pakistan."

    def format_mission_vision(self, mission, vision):
        """Format mission and vision."""
        response = "Mission and Vision:\n\n"
        response += f"Mission: {mission}\n\n"
        response += f"Vision: {vision}"
        return response

    def format_program_levels(self, levels):
        """Format available program levels."""
        response = "Program Levels Available:\n\n"
        
        if isinstance(levels, list):
            for level in levels:
                response += f"{level}\n"
        else:
            response += str(levels)
        
        return response

    def format_university_info(self, info_dict):
        """Format comprehensive university information."""
        response = "Superior University Information:\n\n"
        
        if isinstance(info_dict, dict):
            if 'name' in info_dict:
                response += f"Name: {info_dict['name']}\n"
            if 'type' in info_dict:
                response += f"Type: {info_dict['type']}\n"
            if 'mission' in info_dict:
                response += f"Mission: {info_dict['mission']}\n"
            if 'vision' in info_dict:
                response += f"Vision: {info_dict['vision']}\n"
            if 'levels' in info_dict:
                response += f"Program Levels: {', '.join(info_dict['levels']) if isinstance(info_dict['levels'], list) else info_dict['levels']}\n"
        
        return response


class ProgramResponseFormatter:
    """Format program query responses into natural language."""

    def __init__(self):
        """Initialize formatter."""
        pass

    def format_program_info(self, program_data):
        """Format complete program information."""
        if not program_data:
            return "Sorry, I couldn't find that program in our system."
        
        program = program_data.get('program', 'Unknown')
        level = program_data.get('level', 'Unknown')
        faculty = program_data.get('faculty', 'Unknown')
        admission = program_data.get('admission_fee', 'N/A')
        total_fee = program_data.get('total_fee', 'N/A')
        semesters = program_data.get('semesters', 'Unknown')
        
        response = f"""{program}

Level: {level}
Faculty: {faculty}
Admission Fee: {admission}
Total Fee: {total_fee}
Duration: {semesters} semesters

This is a {level.lower()} program offered under the {faculty} faculty."""
        
        return response

    def format_fee_query(self, program_data):
        """Format response for fee queries."""
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        program = program_data.get('program', 'Unknown')
        total_fee = program_data.get('total_fee', 'N/A')
        admission = program_data.get('admission_fee', 'N/A')
        
        response = f"The total fee for {program} is {total_fee}. Additionally, the admission fee is {admission}."
        return response

    def format_duration_query(self, program_data):
        """Format response for duration/semester queries."""
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        semesters = program_data.get('semesters', 'Unknown')
        
        response = f"{semesters} semesters"
        return response

    def format_admission_fee_query(self, program_data):
        """Format response for admission fee queries."""
        if not program_data:
            return "Sorry, I couldn't find that program."
        
        program = program_data.get('program', 'Unknown')
        admission = program_data.get('admission_fee', 'N/A')
        
        response = f"The admission fee for {program} is {admission}."
        return response

    def format_list_programs(self, programs_list, level):
        """Format response for listing programs by level."""
        if not programs_list:
            return f"Sorry, we don't have any {level} programs available."
        
        program_names = [p['program'] for p in programs_list]
        
        response = f"{level} Programs Available:\n\n"
        for i, name in enumerate(program_names, 1):
            response += f"{i}. {name}\n"
        
        response += f"\nTotal: {len(program_names)} {level} programs"
        return response

    def format_search_results(self, results, query):
        """Format response for search results."""
        if not results:
            return f"Sorry, I couldn't find any programs matching {query}."
        
        response = f"Programs matching {query}:\n\n"
        for i, prog in enumerate(results, 1):
            response += f"{i}. {prog['program']} ({prog['level']})\n"
            response += f"   Faculty: {prog['faculty']}\n"
            response += f"   Total Fee: {prog['total_fee']}\n\n"
        
        return response.strip()

    def format_response(self, intent_label, program_data, level=None, search_results=None):
        """Main formatter: Route to specific response based on intent."""
        # Map intent to formatting function
        intent_map = {
            'ask_fee': self.format_fee_query,
            'ask_duration': self.format_duration_query,
            'ask_admission_fee': self.format_admission_fee_query,
            'ask_semesters': self.format_duration_query,
            'full_info': self.format_program_info,
            'ask_all_details': self.format_program_info,
        }
        
        formatter = intent_map.get(intent_label, self.format_program_info)
        
        if intent_label == 'list_programs' and level:
            return self.format_list_programs(program_data or [], level)
        
        if intent_label == 'search_programs' and search_results:
            return self.format_search_results(search_results, program_data)
        
        return formatter(program_data) if program_data else "Sorry, I couldn't find the information you're looking for."

    def format_not_understood(self):
        """Format response when intent is not understood."""
        return "I'm not sure what you're looking for. You can ask me about program fees, program duration, program details, or list of programs by level."

    def format_unable_to_find_program(self, program_name):
        """Format response when program is not found."""
        return f"Sorry, I couldn't find a program called {program_name}. Could you please rephrase or provide more details?"

    def format_no_level_specified(self, program_name):
        """Format response when level is ambiguous."""
        return f"I found {program_name} but in multiple levels. Could you specify: Undergraduate, Associate, or Postgraduate?"

    def format_ask_level_first(self, levels):
        """Format response showing available levels."""
        if not levels:
            return "We offer programs at Associate, Undergraduate, and Postgraduate levels."
        joined = ", ".join(levels)
        return f"We offer programs in these levels: {joined}. You can ask about programs in any specific level."

    def format_faculties_for_level(self, level, faculties):
        """Format faculties for a level."""
        if not faculties:
            return f"I could not find faculties for {level} programs right now."
        items = '\n'.join([f"{idx}. {name}" for idx, name in enumerate(faculties, 1)])
        return f"For {level}, we offer these faculties:\n{items}\n\nPlease tell me which faculty you want, and I will list its programs."

    def format_programs_by_level(self, level, programs):
        """Format all programs for a specific level, grouped by faculty."""
        if not programs:
            return f"No programs found for {level} level."
        
        # Group programs by faculty
        faculty_groups = {}
        for program in programs:
            faculty = program.get('faculty', 'Other')
            if faculty not in faculty_groups:
                faculty_groups[faculty] = []
            faculty_groups[faculty].append(program.get('program', 'Unknown'))
        
        response = f"{level} Programs:\n\n"
        for faculty, program_list in faculty_groups.items():
            response += f"{faculty}:\n"
            for program in program_list:
                response += f"  • {program}\n"
            response += "\n"
        
        return response

    def format_program_count_for_level_faculty(self, level, faculty, programs):
        """Format response for count query within a selected level/faculty."""
        count = len(programs or [])
        if count == 0:
            return f"There are no programs in {faculty} at {level} level right now."
        items = '\n'.join([f"{idx}. {p['program']}" for idx, p in enumerate(programs, 1)])
        return f"Programs in {faculty} ({level}):\n{items}\n\nTotal: {count} programs"

    def format_program_offered(self, program_name, offered):
        """Format response for program availability check."""
        if offered:
            return f"Yes, we offer {program_name}."
        else:
            return f"No, we do not currently offer {program_name}. Would you like to know about similar programs?"

