#!/usr/bin/env python3
"""
Test script to verify BS Computer Science duration query flow.
Tests entity extraction, intent detection, and response formatting.
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

from backend.services.data_retriever import ProgramDataRetriever
from backend.services.entity_extractor import EntityExtractor
from backend.services.response_formatter import ProgramResponseFormatter
from pathlib import Path

def test_duration_flow():
    """Test the complete flow for duration query."""
    print("=" * 80)
    print("TEST: BS Computer Science Duration Query Flow")
    print("=" * 80)
    
    # Initialize services
    print("\n1. Initializing services...")
    backend_dir = Path(__file__).resolve().parent / 'backend'
    csv_path = backend_dir / 'Data' / 'Programs.csv'
    
    try:
        retriever = ProgramDataRetriever(str(csv_path))
        print(f"✓ ProgramDataRetriever loaded {len(retriever.df)} programs")
        
        extractor = EntityExtractor(retriever.df.copy())
        print("✓ EntityExtractor initialized")
        
        formatter = ProgramResponseFormatter()
        print("✓ ProgramResponseFormatter initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {str(e)}")
        return False
    
    # Test cases
    test_queries = [
        "What is the duration of BS Computer Science?",
        "How long is BS Computer Science?",
        "How many semesters in BS CS?",
        "Duration of computer science?",
        "Tell me the duration of CS program",
        "How long does BS Computer Science take?",
    ]
    
    print("\n2. Testing entity extraction and program retrieval...")
    print("-" * 80)
    
    all_passed = True
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Extract program and level
        extraction = extractor.extract_program_and_level(query)
        program_name = extraction['program']
        level = extraction['level']
        
        print(f"  Extracted program: {program_name}")
        print(f"  Extracted level: {level}")
        
        if program_name:
            # Get program data
            program_data = retriever.get_program_by_name(program_name, level)
            
            if program_data:
                print(f"  ✓ Program found in database")
                print(f"    - Level: {program_data['level']}")
                print(f"    - Faculty: {program_data['faculty']}")
                print(f"    - Duration: {program_data['semesters']} semesters")
                print(f"    - Total Fee: {program_data['total_fee']}")
                
                # Format response
                response = formatter.format_duration_query(program_data)
                print(f"  ✓ Formatted response: {response}")
            else:
                print(f"  ✗ Program not found in database!")
                all_passed = False
        else:
            print(f"  ✗ Could not extract program name!")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    print("=" * 80)
    
    return all_passed

def test_abbreviation_matching():
    """Test abbreviation matching for CS."""
    print("\n" + "=" * 80)
    print("TEST: Abbreviation Matching")
    print("=" * 80)
    
    backend_dir = Path(__file__).resolve().parent / 'backend'
    csv_path = backend_dir / 'Data' / 'Programs.csv'
    
    retriever = ProgramDataRetriever(str(csv_path))
    extractor = EntityExtractor(retriever.df.copy())
    
    print("\nAbbreviation mappings:")
    for abbrev, program in extractor.abbreviations.items():
        if program and abbrev in ['cs', 'it', 'se', 'ai', 'ds']:
            print(f"  {abbrev} -> {program}")
            # Check if program exists
            if program in extractor.all_programs:
                print(f"    ✓ Program exists in database")
            else:
                print(f"    ✗ Program NOT found in database!")
    
    return True

def test_groq_intent_mapping():
    """Test that Groq intents are properly mapped."""
    print("\n" + "=" * 80)
    print("TEST: Groq Intent Mapping")
    print("=" * 80)
    
    # Import the normalize function
    sys.path.insert(0, backend_path)
    from calls.views import _normalize_program_intent
    
    test_intents = [
        ('program_duration', 'ask_duration'),
        ('program_fee', 'ask_fee'),
        ('program_info', 'full_info'),
        ('ask_duration', 'ask_duration'),
        ('ask_fee', 'ask_fee'),
    ]
    
    print("\nIntent mapping tests:")
    all_passed = True
    for groq_intent, expected in test_intents:
        result = _normalize_program_intent(groq_intent)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {groq_intent} -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

if __name__ == '__main__':
    try:
        print("\nRunning BS Computer Science Duration Query Tests\n")
        
        test1 = test_abbreviation_matching()
        test2 = test_groq_intent_mapping()
        test3 = test_duration_flow()
        
        if test1 and test2 and test3:
            print("\n✓ All test suites passed!")
            sys.exit(0)
        else:
            print("\n✗ Some test suites failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
