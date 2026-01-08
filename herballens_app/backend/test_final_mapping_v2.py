import requests
import json
import time

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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            resp_text = res_json.get('response', '')
            
            # Check if specific plants are in the response
            plants_to_check = ["Raktachandini", "Rose", "Saga Manis", "Sapota", "Secang", "Sereh", "Sirih", "Srikaya", "Tin", "Tulasi", "Wood Sorel", "Zigzag"]
            found = [p for p in plants_to_check if p in resp_text]
            print(f"Q: {query} ({lang}) -> Found: {found if found else 'None'}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    # Test cases for plants 75-86
    test_queries = [
        "skin inflammation and stress",
        "throat irritation",
        "digestive bloating and fever",
        "fatigue and digestive weakness",
        "blood purification and fever",
        "oral infections and bad breath",
        "antioxidant support and digestive weakness",
        "constipation and digestive irritation",
        "asthma and weak immunity",
        "acidity and digestive irritation",
        "skin diseases and blood purification"
    ]

    # Add Telugu test cases
    test_queries.extend([
        "జ్వరం మరియు అలసట", # Fever and fatigue
        "గొంతు నొప్పి",      # Sore throat / Throat irritation
        "షుగర్",             # Sugar / Diabetes
        "ఒత్తిడి",           # Stress
        "రక్త శుద్ధి"         # Blood purification
    ])

    for query in test_queries:
        # Determine language: Telugu if Telugu characters present, else English
        lang = 'te' if any('\u0c00' <= c <= '\u0c7f' for c in query) else 'en'
        test_chat(query, lang=lang)
        time.sleep(0.5)
