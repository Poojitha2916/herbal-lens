import requests
import json

def test_chat(query, lang='en'):
    url = "http://localhost:5000/chat"
    payload = {
        "query": query,
        "lang": lang
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Query: {query} ({lang})")
            print(f"Response (EN): {response.json().get('response')}")
            print(f"Response (TE): {response.json().get('response_te')}")
            print("-" * 50)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    # Test cases for new health conditions
    test_chat("I need help with anemia support")
    test_chat("something for blood purification")
    test_chat("how to treat skin diseases")
    test_chat("anemia support", lang='te')
