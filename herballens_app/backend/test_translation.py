import requests
import json

def test_chat_translation(query):
    url = "http://localhost:5000/chat"
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Query: {query}")
            print(f"English Response: {data.get('response')[:100]}...")
            print(f"Telugu Response: {data.get('response_te')[:100]}...")
            print("-" * 50)
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    # Test a common problem
    test_chat_translation("fever")
    # Test a minute problem
    test_chat_translation("hiccups")
    # Test a fallback response
    test_chat_translation("asdfghjkl")
