# BS Computer Science Duration Query - Fix Summary

## Problem
When users asked about the duration of BS Computer Science, the system returned:
> "This information is not available in our database. Please contact the university."

But the information **was** available in the database (Programs.csv contains 8 semesters for BS Computer Science).

## Root Causes Identified and Fixed

### 1. **Incorrect Abbreviation Mapping** (entity_extractor.py)
**Issue:** The abbreviation `'cs'` mapped to `'Computer Science'` instead of the actual program name `'BS Computer Science'`.

**Fix:** Updated all abbreviation mappings to use actual program names from the CSV:
```python
# Before
'cs': 'Computer Science',  # Not a valid program name
'it': 'Information Technology',  # Not a valid program name

# After  
'cs': 'BS Computer Science',  # Actual program name
'it': 'BS Information Technology',  # Actual program name
```

### 2. **Missing Groq Intent Mapping** (views.py)
**Issue:** When Groq detected a query as `program_duration` intent, the system didn't recognize it because the intent normalization function didn't have a mapping for it.

**Fix:** Added missing intent mappings in `_normalize_program_intent()`:
```python
# Added mappings
'program_duration': 'ask_duration',
'program_fee': 'ask_fee',
'program_info': 'full_info',
'program_availability': 'check_program_offered',
```

### 3. **Limited Groq Intent Detection Prompt** (views.py)
**Issue:** The Groq prompt for intent detection didn't explicitly mention program duration queries, so it might not always route them to the programs data source.

**Fix:** Enhanced the Groq prompt to explicitly include program-specific intents and keywords:
```python
# Added to prompt:
'DATA SOURCE MAPPING:\n'
'- If asking about "programs", "majors", "degrees", "duration", "semesters", "how long", "how many semesters", "program fee", "tuition" -> programs\n'
...
'PROGRAM-SPECIFIC INTENTS:\n'
'- Questions about how long a program is -> "program_duration"\n'
'- Questions about program fees/tuition -> "program_fee"\n'
...
```

## Test Results
All tests passed successfully:

✅ **Abbreviation Matching:** CS, IT, SE, AI, DS all map to correct programs
✅ **Intent Mapping:** Groq intents properly convert to system intents  
✅ **Duration Query Flow:** 6/6 test queries correctly extracted BS Computer Science and returned 8 semesters

Example test queries:
- "What is the duration of BS Computer Science?" → 8 semesters ✓
- "How long is BS Computer Science?" → 8 semesters ✓
- "How many semesters in BS CS?" → 8 semesters ✓
- "Tell me the duration of CS program" → 8 semesters ✓

## Files Modified
1. `backend/services/entity_extractor.py` - Updated abbreviation mappings
2. `backend/calls/views.py` - Updated intent mapping and Groq prompt
3. `test_duration_query.py` - Created comprehensive test suite

## How It Works Now

```
User: "What is the duration of BS Computer Science?"
    ↓
Groq: Identifies intent="program_duration", data_source="programs"
    ↓
Intent Normalizer: Converts "program_duration" → "ask_duration"
    ↓
Entity Extractor: Extracts program="BS Computer Science", level="Undergraduate"
    ↓
Data Retriever: Finds program in CSV with 8 semesters
    ↓
Response Formatter: "BS Computer Science is a 8-semester program."
    ↓
User: Receives correct answer ✓
```

## Next Steps (Optional Enhancements)
1. Consider adding similar handling for other common programs (engineering programs, business programs, etc.)
2. Add more training examples to Groq prompt for other program-related queries
3. Monitor for other similar issues with different programs
