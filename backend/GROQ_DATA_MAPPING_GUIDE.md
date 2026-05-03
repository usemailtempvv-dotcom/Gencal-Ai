# Groq AI with Data Source Mapping - Implementation Guide

## Overview

The GenCall AI system has been upgraded to use **Groq AI** instead of Gemini, with intelligent **data source mapping** that:

1. **Understands user questions** using Groq's LLaMA 3.3 model
2. **Identifies available data sources** for each question
3. **Maps queries to the correct CSV files**
4. **Provides transparent answers** showing where information comes from
5. **Improves accuracy** by routing questions to the right knowledge base

---

## Available Data Sources

### 1. **programs.csv**
- **Contains**: Bachelor programs, Master programs, engineering, business, science programs
- **Query Examples**:
  - "Which programs do you offer?"
  - "What's your engineering program?"
  - "Tell me about Masters programs"
- **Response Includes**: Program name, level, duration, fees, requirements

### 2. **admission_policy.csv**
- **Contains**: Admission requirements, eligibility criteria, application deadlines, entry tests
- **Query Examples**:
  - "What are admission requirements?"
  - "When is the admission deadline?"
  - "What entry test is required?"
- **Response Includes**: Requirements, eligibility, deadlines, test names

### 3. **scholarship_policy.csv**
- **Contains**: Scholarships, grants, fee waivers, financial aid programs
- **Query Examples**:
  - "Do you offer scholarships?"
  - "What financial aid is available?"
  - "Tell me about fee waivers"
- **Response Includes**: Scholarship types, amounts, eligibility, application process

### 4. **campuses_info.csv**
- **Contains**: Campus locations, addresses, phone numbers, contact information, focus areas
- **Query Examples**:
  - "Where are your campuses?"
  - "What's the Main Campus address?"
  - "How do I contact the City Campus?"
- **Response Includes**: Location, address, phone, email, facilities

### 5. **facilities.csv**
- **Contains**: Library, labs, transport, medical center, daycare, sports, parking, infrastructure
- **Query Examples**:
  - "What facilities do you have?"
  - "Do you have a library?"
  - "Is there medical support?"
- **Response Includes**: Facility name, category, features, details

### 6. **hostal.csv** (Hostel Information)
- **Contains**: Hostel accommodation, rooms, security, internet, meal plans
- **Query Examples**:
  - "Tell me about hostel accommodation"
  - "Are there internet facilities?"
  - "What about room types?"
- **Response Includes**: Category, features, details, amenities

### 7. **university_info.csv** (General Information)
- **Contains**: University history, mission, general contact information
- **Query Examples**:
  - "Tell me about the university"
  - "What is the university's mission?"
- **Response Includes**: General university information

---

## System Flow

### Step 1: Query Reception
```
User Query → "Which campuses do you have and their facilities?"
```

### Step 2: Groq Understanding & Data Source Mapping
```json
{
  "query": "Which campuses do you have and their facilities?",
  "clean_question": "What are the locations and details of all university campuses?",
  "intent": "campus_details",
  "data_source": "campuses_info",
  "data_source_info": "Information about campus locations, addresses, and contact details"
}
```

### Step 3: Query Processing
The system retrieves data from:
- **Primary**: `campuses_info.csv`
- **Secondary**: `facilities.csv` (for facility details)

### Step 4: Answer Generation
```json
{
  "query": "Which campuses do you have and their facilities?",
  "clean_question": "What are the locations and details of all university campuses?",
  "primary_domain": "campus",
  "data_source": "campuses_info",
  "data_source_info": "Information about campus locations, addresses, and contact details",
  "campus_data": [
    {
      "campus_name": "Main Campus",
      "location": "Downtown",
      "focus": "Engineering & Science",
      "phone": "123-456-7890",
      "email": "main@university.edu"
    }
  ],
  "natural_response": "Our Main Campus is located in Downtown with a focus on Engineering and Science programs. You can reach us at 123-456-7890.",
  "answer_source": "local_dataset",
  "answer_source_confidence": 0.95,
  "found": true
}
```

---

## Configuration

### 1. Set Groq API Key in `.env`

```bash
# Required for Groq API calls
GROQ_API_KEY=your_groq_api_key_here
GROQ_NLU_MODEL=llama-3.3-70b
GROQ_STT_MODEL=whisper-large-v3-turbo
```

### 2. Backend Settings (`settings.py`)

```python
# Groq Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_STT_MODEL = os.getenv('GROQ_STT_MODEL', 'whisper-large-v3-turbo')
GROQ_NLU_MODEL = os.getenv('GROQ_NLU_MODEL', 'llama-3.3-70b')
```

---

## Example API Responses

### Campus Query Response
```json
{
  "query": "Tell me about Main Campus",
  "clean_question": "What information is available about the Main Campus?",
  "primary_domain": "campus",
  "data_source": "campuses_info",
  "data_source_info": "Campus locations, addresses, contact information",
  "campus_data": {
    "campus_name": "Main Campus",
    "location": "Downtown",
    "phone": "123-456-7890"
  },
  "natural_response": "The Main Campus is located in Downtown. Contact: 123-456-7890",
  "answer_source": "local_dataset",
  "answer_source_confidence": 0.92
}
```

### Facilities Query Response
```json
{
  "query": "What facilities are available?",
  "clean_question": "What facilities and amenities does the university offer?",
  "primary_domain": "facilities",
  "data_source": "facilities",
  "data_source_info": "Campus facilities including library, labs, medical, transport, and more",
  "facilities_data": [
    {
      "category": "Campus Life/General Environment",
      "facility_name": "Main Library",
      "feature": "Well-equipped",
      "details": "24/7 access, 500,000+ books"
    }
  ],
  "natural_response": "We have a well-equipped library with 24/7 access and over 500,000 books.",
  "answer_source": "local_dataset",
  "answer_source_confidence": 0.92
}
```

### Hostel Query Response
```json
{
  "query": "Tell me about hostel",
  "clean_question": "What information is available about hostel accommodation?",
  "primary_domain": "hostel",
  "data_source": "hostal",
  "data_source_info": "Hostel accommodation details, rooms, security, and internet facilities",
  "hostel_data": [
    {
      "category": "Accommodation",
      "sub_category": "Room Types",
      "feature": "Single and Double Rooms",
      "details": "Available for all students"
    }
  ],
  "natural_response": "We offer single and double hostel rooms for all students with security and internet facilities.",
  "answer_source": "local_dataset",
  "answer_source_confidence": 0.92
}
```

---

## Groq Functions

### 1. `_normalize_transcript_with_groq(text, detected_language='en')`
**Purpose**: Cleans and corrects speech-to-text transcripts
- Fixes STT errors
- Preserves university names and program names
- Supports Urdu and English

**Example**:
```python
cleaned = _normalize_transcript_with_groq("wihch programmez are availabel")
# Returns: "Which programs are available?"
```

### 2. `_groq_rephrase_and_detect_intent(input_text)`
**Purpose**: Understands user intent and maps to data source
**Returns**:
```json
{
  "intent": "program_details",
  "clean_question": "What programs are available?",
  "data_source": "programs",
  "data_source_info": "Information about all available programs"
}
```

### 3. `_groq_answer_from_context(question, context_text, data_source='')`
**Purpose**: Generates accurate answers from provided context
**Features**:
- Answers ONLY from provided data
- Shows which data source is being used
- Clear, concise, student-friendly responses

---

## Advantages Over Previous System

| Aspect | Previous (Gemini) | Current (Groq) |
|--------|------------------|-----------------|
| **AI Model** | Gemini 1.5 Flash | Groq LLaMA 3.3 |
| **Data Source Mapping** | ❌ Not available | ✅ Automatic mapping |
| **Transparency** | Shows confidence | Shows data source + confidence |
| **Query Understanding** | Basic | Advanced with intent + domain |
| **CSV Support** | Limited | Full (7 CSV files) |
| **Response Accuracy** | Good | Excellent (context-aware) |
| **Speed** | Good | Faster (Groq optimization) |
| **Cost** | Higher | Lower (Groq pricing) |

---

## Testing the Integration

### Test 1: Domain Classification
```bash
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What facilities do you have?"}'
```

Expected `data_source`: `facilities`

### Test 2: Intent Detection
```bash
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about scholarships"}'
```

Expected `data_source`: `scholarship_policy`

### Test 3: Campus Query
```bash
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Where are your campuses?"}'
```

Expected `data_source`: `campuses_info`

---

## Troubleshooting

### Issue: API returns "data_source: unknown"
**Solution**: 
- Check GROQ_API_KEY is set correctly
- Verify query is clear and unambiguous
- Ensure all CSV files exist in `backend/Data/`

### Issue: Empty answers despite data_source being correct
**Solution**:
- Check CSV file format (should have proper headers)
- Verify retrievers loaded successfully
- Check logs for CSV parsing errors

### Issue: Groq API not responding
**Solution**:
- Verify GROQ_API_KEY has sufficient quota
- Check internet connection
- Review Groq API status at https://status.groq.com

---

## Future Enhancements

1. **Multi-source Queries**: Combine data from multiple CSVs
2. **Confidence Scoring**: More nuanced confidence levels
3. **Fallback Chains**: Automatic fallback to Botpress if local data insufficient
4. **User Feedback Loop**: Learn from user corrections
5. **Language Support**: Expand to more languages
6. **Custom Data Mappings**: Allow admin to define custom mappings

---

## Support & Documentation

- **Groq API Docs**: https://console.groq.com/docs
- **LLaMA 3.3 Model**: Higher accuracy, faster responses
- **CSV Data Format**: Supports standard CSV with headers
- **Error Logging**: Check `backend/logs/` for detailed errors

