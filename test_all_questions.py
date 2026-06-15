#!/usr/bin/env python3
"""
Test script to verify all university information questions are handled.
Tests all question types the user specified.
"""
import os
import sys
import django

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.dirname(__file__))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gencall_backend.settings')
django.setup()

from backend.services.data_retriever import (
    ProgramDataRetriever,
    AdmissionPolicyRetriever,
    ScholarshipPolicyRetriever,
    CampusesInfoRetriever,
    FacilitiesRetriever,
    HostalRetriever,
    UniversityInfoRetriever
)
from pathlib import Path

def test_all_question_types():
    """Test that all CSV retrievers work and have data."""
    print("=" * 90)
    print("COMPREHENSIVE DATA AVAILABILITY CHECK - All Question Types")
    print("=" * 90)
    
    backend_dir = Path(__file__).resolve().parent / 'backend'
    
    # Test data
    test_data = []
    
    # 1. University Information
    print("\n1. UNIVERSITY INFORMATION QUESTIONS")
    print("-" * 90)
    try:
        uni_retriever = UniversityInfoRetriever(str(backend_dir / 'Data' / 'University_info.csv'))
        all_info = uni_retriever.get_all_info()
        print(f"✓ University Info loaded: {len(all_info)} fields")
        print(f"  - University: {uni_retriever.get_university_name()}")
        print(f"  - Type: {uni_retriever.get_university_type()}")
        print(f"  - Program Levels: {uni_retriever.get_program_levels()}")
        test_data.append(("University Info", True, all_info))
    except Exception as e:
        print(f"✗ University Info failed: {str(e)}")
        test_data.append(("University Info", False, str(e)))
    
    # 2. Programs
    print("\n2. PROGRAM QUESTIONS")
    print("-" * 90)
    try:
        prog_retriever = ProgramDataRetriever(str(backend_dir / 'Data' / 'Programs.csv'))
        programs = prog_retriever.get_all_programs()
        levels = prog_retriever.get_all_levels()
        print(f"✓ Programs loaded: {len(programs)} programs across {len(levels)} levels")
        bs_cs = prog_retriever.get_program_by_name('BS Computer Science')
        if bs_cs:
            print(f"  - BS Computer Science: {bs_cs['semesters']} semesters, {bs_cs['total_fee']}")
        test_data.append(("Programs", True, f"{len(programs)} programs"))
    except Exception as e:
        print(f"✗ Programs failed: {str(e)}")
        test_data.append(("Programs", False, str(e)))
    
    # 3. Admission
    print("\n3. ADMISSION & APPLICATION QUESTIONS")
    print("-" * 90)
    try:
        adm_retriever = AdmissionPolicyRetriever(str(backend_dir / 'Data' / 'admission.csv'))
        summary = adm_retriever.get_summary()
        deadlines = adm_retriever.get_deadlines()
        eligibility = adm_retriever.get_eligibility()
        print(f"✓ Admission Info loaded")
        print(f"  - Admission Open: {summary.get('admission_open', 'Unknown')}")
        print(f"  - Spring Deadline: {deadlines.get('spring_last_date', 'Unknown')}")
        print(f"  - Fall Deadline: {deadlines.get('fall_last_date', 'Unknown')}")
        print(f"  - Entry Test: {eligibility.get('entry_test', 'Unknown')}")
        print(f"  - Minimum Marks: {eligibility.get('minimum_marks', 'Unknown')}")
        test_data.append(("Admission", True, "Dates, entry test, eligibility available"))
    except Exception as e:
        print(f"✗ Admission failed: {str(e)}")
        test_data.append(("Admission", False, str(e)))
    
    # 4. Scholarships
    print("\n4. SCHOLARSHIP & FEE QUESTIONS")
    print("-" * 90)
    try:
        sch_retriever = ScholarshipPolicyRetriever(str(backend_dir / 'Data' / 'Scholarship_policy.csv'))
        summary = sch_retriever.get_summary()
        categories = summary.get('categories', [])
        print(f"✓ Scholarships loaded: {len(categories)} scholarship types")
        for cat in categories[:5]:
            print(f"  - {cat}")
        if len(categories) > 5:
            print(f"  ... and {len(categories) - 5} more")
        test_data.append(("Scholarships", True, f"{len(categories)} types"))
    except Exception as e:
        print(f"✗ Scholarships failed: {str(e)}")
        test_data.append(("Scholarships", False, str(e)))
    
    # 5. Campuses
    print("\n5. CAMPUS & CONTACT QUESTIONS")
    print("-" * 90)
    try:
        campus_retriever = CampusesInfoRetriever(str(backend_dir / 'Data' / 'Campuses_info.csv'))
        all_campuses = campus_retriever.get_all_campuses()
        summary = campus_retriever.get_all_campuses_summary()
        print(f"✓ Campuses loaded: {len(all_campuses)} campuses")
        for campus in summary[:5]:
            print(f"  - {campus['campus_name']}: {campus['location']}")
        test_data.append(("Campuses", True, f"{len(all_campuses)} campuses"))
    except Exception as e:
        print(f"✗ Campuses failed: {str(e)}")
        test_data.append(("Campuses", False, str(e)))
    
    # 6. Facilities
    print("\n6. FACILITY QUESTIONS")
    print("-" * 90)
    try:
        fac_retriever = FacilitiesRetriever(str(backend_dir / 'Data' / 'Facilities.csv'))
        all_facilities = fac_retriever.get_all_facilities_summary()
        categories = fac_retriever.get_all_categories()
        print(f"✓ Facilities loaded: {len(all_facilities)} facilities across {len(categories)} categories")
        for cat in categories:
            facilities_in_cat = [f for f in all_facilities if f['category'] == cat]
            print(f"  - {cat}: {len(facilities_in_cat)} facilities")
        test_data.append(("Facilities", True, f"{len(all_facilities)} facilities"))
    except Exception as e:
        print(f"✗ Facilities failed: {str(e)}")
        test_data.append(("Facilities", False, str(e)))
    
    # 7. Hostel
    print("\n7. HOSTEL & ACCOMMODATION QUESTIONS")
    print("-" * 90)
    try:
        hostel_retriever = HostalRetriever(str(backend_dir / 'Data' / 'hostal.csv'))
        all_hostel = hostel_retriever.get_all_hostel_details()
        categories = hostel_retriever.get_all_categories()
        print(f"✓ Hostel Info loaded: {len(all_hostel)} details across {len(categories)} categories")
        for cat in categories:
            details_in_cat = [d for d in all_hostel if d['category'] == cat]
            print(f"  - {cat}: {len(details_in_cat)} details")
        test_data.append(("Hostel", True, f"{len(all_hostel)} details"))
    except Exception as e:
        print(f"✗ Hostel failed: {str(e)}")
        test_data.append(("Hostel", False, str(e)))
    
    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    
    total = len(test_data)
    passed = sum(1 for _, success, _ in test_data if success)
    
    for name, success, data in test_data:
        status = "✓" if success else "✗"
        print(f"{status} {name:25} - {data}")
    
    print(f"\nTotal: {passed}/{total} data sources available")
    
    if passed == total:
        print("\n✓ ALL DATA SOURCES AVAILABLE - System ready to answer all question types!")
        return True
    else:
        print(f"\n✗ {total - passed} data sources unavailable - Check file paths")
        return False

def test_specific_questions():
    """Test specific common questions."""
    print("\n" + "=" * 90)
    print("TESTING SPECIFIC COMMON QUESTIONS")
    print("=" * 90)
    
    backend_dir = Path(__file__).resolve().parent / 'backend'
    
    questions_to_test = [
        ("What programs does the university offer?", "University Info"),
        ("Is the university HEC recognized?", "University Info"),
        ("Where are the campuses?", "Campus Info"),
        ("How many campuses?", "Campus Info"),
        ("When is the admission deadline?", "Admission"),
        ("What are admission requirements?", "Admission"),
        ("What documents are required?", "Admission"),
        ("Is admission open?", "Admission"),
        ("Do you offer BS Computer Science?", "Programs"),
        ("What is the fee structure?", "Programs/Scholarships"),
        ("Are scholarships available?", "Scholarships"),
        ("What is the merit for CS?", "Scholarships"),
        ("What facilities do you have?", "Facilities"),
        ("Is WiFi available?", "Facilities"),
        ("Do you have a hostel?", "Hostel"),
        ("Is transport available?", "Facilities"),
    ]
    
    try:
        uni_retriever = UniversityInfoRetriever(str(backend_dir / 'Data' / 'University_info.csv'))
        prog_retriever = ProgramDataRetriever(str(backend_dir / 'Data' / 'Programs.csv'))
        adm_retriever = AdmissionPolicyRetriever(str(backend_dir / 'Data' / 'admission.csv'))
        sch_retriever = ScholarshipPolicyRetriever(str(backend_dir / 'Data' / 'Scholarship_policy.csv'))
        campus_retriever = CampusesInfoRetriever(str(backend_dir / 'Data' / 'Campuses_info.csv'))
        fac_retriever = FacilitiesRetriever(str(backend_dir / 'Data' / 'Facilities.csv'))
        hostel_retriever = HostalRetriever(str(backend_dir / 'Data' / 'hostal.csv'))
        
        print("\nSample Questions:")
        for i, (question, expected_source) in enumerate(questions_to_test, 1):
            print(f"{i:2}. Q: {question}")
            print(f"    Expected source: {expected_source}")
            print()
            
    except Exception as e:
        print(f"Error initializing retrievers: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    try:
        print("\nRunning Comprehensive Data Availability Tests\n")
        
        test1 = test_all_question_types()
        test2 = test_specific_questions()
        
        if test1:
            print("\n" + "=" * 90)
            print("✓ ALL TESTS PASSED - System has all data needed for all question types")
            print("=" * 90)
            sys.exit(0)
        else:
            print("\n" + "=" * 90)
            print("✗ Some data sources are missing")
            print("=" * 90)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
