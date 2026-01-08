import requests
import json

def test_chat(query):
    url = "http://localhost:5000/chat"
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print(f"Query: {query}")
            print(f"Response: {response.json().get('response')[:200]}...")
            print("-" * 50)
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test cases for minute problems
    test_queries = [
        "hiccups",
        "dry lips",
        "tech neck",
        "foot cracks",
        "eye strain",
        "dark circles",
        "morning sluggishness",
        "joint clicks",
        "bad breath",
        "swollen ankles",
        "sneezing fits",
        "hoarse voice",
        "thirst"
    ]
    
    print("Testing Chatbot for Minute Problems...\n")
    for q in test_queries:
        test_chat(q)
