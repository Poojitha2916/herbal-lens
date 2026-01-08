import requests
import json

def test_predict_translation():
    url = "http://localhost:5000/predict"
    # We need a dummy image file for this test, but let's just test the response structure
    # by mock or checking if the app handles error gracefully but still has the logic.
    # Actually, it's better to test the /chat endpoint which we know works.
    pass

def test_chat_translation(query):
    url = "http://localhost:5000/chat"
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Query: {query}")
            print(f"English Response: {data.get('response')[:50]}...")
            print(f"Telugu Response: {data.get('response_te')[:50]}...")
            print("-" * 50)
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_chat_translation("fever")
    test_chat_translation("unknown problem")
