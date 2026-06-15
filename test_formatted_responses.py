"""
Test formatted responses from the API for all question types.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gencall_backend.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from calls.views import (
    _process_program_query, _process_admission_query, _process_scholarship_query,
    _process_campus_query, _process_facilities_query, _process_hostel_query,
    _get_program_services, _get_admission_services, _get_scholarship_services,
    _get_campuses_retriever, _get_facilities_retriever, _get_hostal_retriever,
    _get_university_info_retriever
)

print("=" * 100)
print("TESTING FORMATTED RESPONSES FOR ALL QUESTION TYPES")
print("=" * 100)

# Test 1: Program Query - Duration
print("\n1. PROGRAM QUERY - Duration")
print("-" * 100)
result = _process_program_query("What is the duration of BS Computer Science?", "ask_duration")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 2: Program Query - Fee
print("\n2. PROGRAM QUERY - Fee")
print("-" * 100)
result = _process_program_query("How much fee for BS Computer Science?", "ask_fee")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 3: Admission Query - Deadlines
print("\n3. ADMISSION QUERY - Deadlines")
print("-" * 100)
result = _process_admission_query("When is the admission deadline?", "ask_admission_deadline")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 4: Admission Query - Documents
print("\n4. ADMISSION QUERY - Documents")
print("-" * 100)
result = _process_admission_query("What documents are required?", "ask_admission_documents")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 5: Scholarship Query
print("\n5. SCHOLARSHIP QUERY")
print("-" * 100)
result = _process_scholarship_query("Are scholarships available?", "ask_scholarship_summary")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 6: Campus Query
print("\n6. CAMPUS QUERY")
print("-" * 100)
result = _process_campus_query("How can I contact the university?")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 7: Facilities Query
print("\n7. FACILITIES QUERY")
print("-" * 100)
result = _process_facilities_query("Is WiFi available?")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 8: Hostel Query
print("\n8. HOSTEL QUERY")
print("-" * 100)
result = _process_hostel_query("Is there a hostel available?")
print(f"Natural Response:\n{result.get('natural_response')}")
print()

# Test 9: University Info
print("\n9. UNIVERSITY INFO QUERY")
print("-" * 100)
retriever, formatter = _get_university_info_retriever()
if retriever and formatter:
    info = retriever.get_all_info()
    if info:
        response = formatter.format_university_info(info)
        print(f"Natural Response:\n{response}")
    else:
        print("No university info found")
else:
    print("Retriever or formatter not available")
print()

print("=" * 100)
print("✓ ALL FORMATTED RESPONSES TESTED")
print("=" * 100)
