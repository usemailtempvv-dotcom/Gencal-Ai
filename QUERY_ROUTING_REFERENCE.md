# GenCall AI - Query to Data Source Mapping Reference

## Quick Lookup Guide

### Exact Query Examples and Their Data Sources

#### PROGRAMS CSV
**When to use**: Questions about available programs, degrees, majors

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "Which programs do you offer?" | What programs are available? | program_list | programs | Programs.csv |
| "Tell me about engineering program" | What details about engineering? | program_details | programs | Programs.csv |
| "What's your masters program?" | What masters programs exist? | program_details | programs | Programs.csv |
| "Do you have BS in Computer Science?" | Is BS Computer Science available? | program_search | programs | Programs.csv |
| "How long is the program?" | What is program duration? | program_duration | programs | Programs.csv |

---

#### ADMISSION_POLICY CSV
**When to use**: Questions about how to apply, requirements, deadlines, eligibility

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "What are admission requirements?" | What do I need to apply? | admission_requirements | admission_policy | Admission_policy.csv |
| "When is the application deadline?" | What is the deadline? | admission_deadline | admission_policy | Admission_policy.csv |
| "Am I eligible to apply?" | What is eligibility criteria? | admission_eligibility | admission_policy | Admission_policy.csv |
| "What entry test is required?" | Which test is needed? | admission_test | admission_policy | Admission_policy.csv |
| "How do I apply?" | What is the application process? | admission_process | admission_policy | Admission_policy.csv |

---

#### SCHOLARSHIP_POLICY CSV
**When to use**: Questions about financial aid, scholarships, grants, fees

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "Do you offer scholarships?" | What scholarships available? | scholarship_availability | scholarship_policy | Scholarship_policy.csv |
| "What financial aid do you have?" | What aid programs? | scholarship_types | scholarship_policy | Scholarship_policy.csv |
| "How much is the scholarship?" | What is scholarship amount? | scholarship_amount | scholarship_policy | Scholarship_policy.csv |
| "Can I get a fee waiver?" | What fee waivers available? | scholarship_fee_waiver | scholarship_policy | Scholarship_policy.csv |
| "Who is eligible for grant?" | What is eligibility? | scholarship_eligibility | scholarship_policy | Scholarship_policy.csv |

---

#### CAMPUSES_INFO CSV
**When to use**: Questions about campus locations, addresses, contact information, facilities

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "Where are your campuses?" | What are campus locations? | campus_locations | campuses_info | Campuses_info.csv |
| "What is the Main Campus address?" | Where is Main Campus? | campus_address | campuses_info | Campuses_info.csv |
| "How do I contact Main Campus?" | What is contact info? | campus_contact | campuses_info | Campuses_info.csv |
| "Which campus is in Sargodha?" | Where is Sargodha campus? | campus_location | campuses_info | Campuses_info.csv |
| "What's the phone number?" | What is phone? | campus_phone | campuses_info | Campuses_info.csv |

---

#### FACILITIES CSV
**When to use**: Questions about campus facilities, infrastructure, services

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "What facilities do you have?" | What facilities available? | facilities_list | facilities | Facilities.csv |
| "Do you have a library?" | Is there a library? | facilities_library | facilities | Facilities.csv |
| "Is there medical support?" | Medical facility available? | facilities_medical | facilities | Facilities.csv |
| "Do you have transport?" | Transport facility? | facilities_transport | facilities | Facilities.csv |
| "Is there a lab?" | Lab facility available? | facilities_lab | facilities | Facilities.csv |
| "What about parking?" | Parking available? | facilities_parking | facilities | Facilities.csv |
| "Is daycare available?" | Daycare facility? | facilities_daycare | facilities | Facilities.csv |

---

#### HOSTAL CSV (Hostel Information)
**When to use**: Questions about accommodation, rooms, internet, security

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "Tell me about hostel" | What hostel info available? | hostel_details | hostal | hostal.csv |
| "Do you have accommodation?" | Is accommodation available? | hostel_accommodation | hostal | hostal.csv |
| "What about room types?" | What rooms available? | hostel_rooms | hostal | hostal.csv |
| "Is there internet?" | Internet available? | hostel_internet | hostal | hostal.csv |
| "What about security?" | Security facilities? | hostel_security | hostal | hostal.csv |
| "What meal plans?" | Meal options? | hostel_meals | hostal | hostal.csv |

---

#### UNIVERSITY_INFO CSV (General Information)
**When to use**: Questions about university history, mission, general contact

| User Query | Clean Question | Intent | Data Source | CSV File |
|-----------|-----------------|--------|-------------|----------|
| "Tell me about the university" | What is university info? | university_general | university_info | University_info.csv |
| "What is the university's mission?" | What is mission? | university_mission | university_info | University_info.csv |
| "Who is the principal?" | Who is in charge? | university_leadership | university_info | University_info.csv |

---

## Decision Tree for Query Routing

```
User Question
    │
    ├─→ Contains "program/major/degree/course"? → PROGRAMS
    │
    ├─→ Contains "admission/apply/deadline/eligible/requirements"? → ADMISSION_POLICY
    │
    ├─→ Contains "scholarship/grant/financial/fee/waiver"? → SCHOLARSHIP_POLICY
    │
    ├─→ Contains "campus/location/address/contact/phone"? → CAMPUSES_INFO
    │
    ├─→ Contains "facility/library/lab/medical/transport/parking"? → FACILITIES
    │
    ├─→ Contains "hostel/accommodation/room/internet/security"? → HOSTAL
    │
    └─→ Other general questions → UNIVERSITY_INFO
```

---

## Common Query Patterns

### Multi-Source Queries
Some queries may involve multiple data sources:

| Query | Primary Source | Secondary Source |
|-------|---|---|
| "What programs are in City Campus?" | campuses_info | programs |
| "What facilities support engineering program?" | facilities | programs |
| "Are there scholarships for specific programs?" | scholarship_policy | programs |
| "Hostel fees for international students?" | hostal | university_info |

**System Behavior**: Groq prioritizes primary source, then supplements with secondary if needed.

---

## Ambiguous Queries Resolution

When a query is ambiguous, Groq uses this priority order:

1. **Exact keyword match** - Direct mapping to data source
2. **Intent inference** - Understanding user context
3. **Confidence score** - Selecting most relevant source
4. **Fallback** - General university_info

### Examples of Ambiguous Resolution

| Query | Initial Ambiguity | Resolution | Data Source |
|-------|---|---|---|
| "Tell me everything" | Too broad | Maps to university_info | UNIVERSITY_INFO |
| "What do you have?" | Too vague | Maps to programs (most common) | PROGRAMS |
| "Help me" | No clear topic | Maps to greeting/botpress | BOTPRESS |

---

## Response Format By Data Source

### PROGRAMS Response
```json
{
  "data_source": "programs",
  "data_source_info": "Available bachelor and master programs",
  "program_data": [{
    "program_name": "BS Computer Science",
    "level": "Undergraduate",
    "duration": "4 years",
    "fees": "50000 PKR"
  }],
  "natural_response": "We offer BS Computer Science as a 4-year program..."
}
```

### ADMISSION_POLICY Response
```json
{
  "data_source": "admission_policy",
  "data_source_info": "Admission requirements and deadlines",
  "admission_data": [{
    "requirement": "High School Certificate",
    "deadline": "July 31, 2024",
    "test_required": "Entry Test"
  }],
  "natural_response": "To apply, you need a high school certificate..."
}
```

### CAMPUSES_INFO Response
```json
{
  "data_source": "campuses_info",
  "data_source_info": "Campus locations and contact information",
  "campus_data": {
    "campus_name": "Main Campus",
    "location": "Downtown",
    "phone": "123-456-7890"
  },
  "natural_response": "Main Campus is located in Downtown..."
}
```

### FACILITIES Response
```json
{
  "data_source": "facilities",
  "data_source_info": "Campus facilities and infrastructure",
  "facilities_data": [{
    "category": "Academic",
    "facility_name": "Science Lab",
    "feature": "Well-equipped",
    "details": "Latest equipment, 50+ workstations"
  }],
  "natural_response": "We have well-equipped science labs with..."
}
```

### HOSTAL Response
```json
{
  "data_source": "hostal",
  "data_source_info": "Hostel accommodation and amenities",
  "hostel_data": [{
    "category": "Accommodation",
    "feature": "Single/Double Rooms",
    "details": "Safe, secure, fully furnished"
  }],
  "natural_response": "We provide safe hostel accommodation with..."
}
```

---

## Testing Queries

### Recommended Test Queries

```bash
# Campus Query
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Where are your campuses?"}'

# Facilities Query  
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What facilities do you have?"}'

# Hostel Query
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about hostel accommodation"}'

# Program Query
curl -X POST http://localhost:8000/api/program_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Which programs do you offer?"}'
```

### Expected `data_source` Values
- `programs`
- `admission_policy`
- `scholarship_policy`
- `campuses_info`
- `facilities`
- `hostal`
- `university_info`

---

## Accuracy Improvement Tips

### For Best Results

1. **Be specific**: "What programs do you have?" (specific) vs "Tell me" (vague)
2. **Use keywords**: Include main topic words (campus, facility, hostel, etc.)
3. **Full questions**: "Where are campuses?" works better than "campuses?"
4. **Natural language**: Mix Urdu/English is fine, system handles it
5. **Clear intent**: "How to apply?" vs "Umm, like, the thing about..."

### Example Improvements

| Vague | Better | Best |
|-------|--------|------|
| "Programs?" | "What programs?" | "Which undergraduate programs do you offer?" |
| "Hostel?" | "About hostel" | "What hostel accommodation options are available?" |
| "Facilities?" | "What facilities?" | "What campus facilities support engineering students?" |

---

## Notes

- System works with English, Urdu, and mixed Urdu-English
- Groq automatically normalizes/cleans questions before mapping
- Response includes confidence score for reliability
- If data not found in primary source, can fallback to Botpress
- All queries logged for analytics and improvement

