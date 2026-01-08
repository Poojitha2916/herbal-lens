import requests
import json

def test_chat(query):
    url = "http://127.0.0.1:5000/chat"
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    
    print(f"\n" + "="*50)
    print(f"Testing query: '{query}'")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("Response Received:")
            print(data.get("response"))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection failed: {e}. Is the server running?")

if __name__ == "__main__":
    print("Starting Comprehensive Chatbot Knowledge Test...")
    
    # 🟢 SMALL / COMMON PROBLEMS
    common_problems = [
        "common cold", "cough", "fever", "headache", "sore throat", 
        "indigestion", "gas & bloating", "constipation", "diarrhea", 
        "nausea", "mouth ulcers", "toothache", "bad breath", 
        "minor wounds", "insect bites", "skin rashes", "acne", 
        "dandruff", "hair fall", "sibver", "vomit", "hairloss"
    ]
    
    # 🟡 MODERATE PROBLEMS
    moderate_problems = [
        "sinusitis", "asthma", "bronchitis", "allergies", "joint pain", 
        "muscle pain", "back pain", "arthritis", "migraine", 
        "gastritis", "ulcers", "uti", "skin infections", 
        "fungal infections", "menstrual pain", "irregular periods", 
        "stress", "anxiety", "insomnia", "fatigue"
    ]
    
    # 🟠 CHRONIC / LIFESTYLE PROBLEMS
    chronic_problems = [
        "diabetes", "high blood pressure", "cholesterol", "obesity", 
        "thyroid disorders", "pcos", "anemia", "liver disorders", 
        "kidney support", "weak immunity"
    ]
    
    # 🔴 SERIOUS / MAJOR PROBLEMS
    serious_problems = [
        "cancer", "tumors", "heart diseases", "stroke recovery", 
        "autoimmune disorders", "chronic respiratory", "chronic digestive"
    ]

    print("\n--- Testing Common Problems ---")
    for prob in common_problems[:5]: # Testing a sample to keep output clean
        test_chat(prob)
        
    print("\n--- Testing Moderate Problems ---")
    for prob in moderate_problems[:5]:
        test_chat(prob)
        
    print("\n--- Testing Chronic Problems ---")
    for prob in chronic_problems[:3]:
        test_chat(prob)
        
    print("\n--- Testing Serious Problems ---")
    for prob in serious_problems[:2]:
        test_chat(prob)
        
    print("\n--- Testing Variations & Typos ---")
    test_chat("i have hairloss")
    test_chat("feeling sibver")
    test_chat("want to vomit")
