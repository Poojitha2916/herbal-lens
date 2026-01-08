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
            res_json = response.json()
            print(f"Response (EN): {res_json.get('response')}")
            # print(f"Response (TE): {res_json.get('response_te')}")
            print("-" * 50)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    # Test cases for plants 75-86
    test_chat("I have skin inflammation and stress") # Should include Rose or Zigzag
    test_chat("something for throat irritation") # Should include Saga Manis
    test_chat("how to treat digestive bloating and fever") # Should include Sereh
    test_chat("antioxidant support") # Should include Secang or Srikaya
    test_chat("asthma support") # Should include Tulasi
    test_chat("acidity and digestive irritation") # Should include Wood_sorel or Tin
