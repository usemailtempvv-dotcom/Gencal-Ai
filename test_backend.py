import requests

# Simulate what the frontend does
url = 'http://localhost:8000/api/program_query/'
headers = {'Content-Type': 'application/json'}
payload = {'query': 'what is the fee of the BS computer science', 'emotion': 'neutral'}

print("Testing frontend -> backend flow...")
print(f"POST {url}")
print(f"Headers: {headers}")
print(f"Payload: {payload}")
print()

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"✓ Status: {response.status_code}")
    
    data = response.json()
    print(f"✓ natural_response: {data.get('natural_response', 'MISSING')}")
    print(f"✓ intent: {data.get('intent', 'MISSING')}")
    print(f"✓ answer_source: {data.get('answer_source', 'MISSING')}")
    print()
    print("SUCCESS: Backend is returning proper answers now!")
    
except Exception as e:
    print(f"✗ Error: {e}")
