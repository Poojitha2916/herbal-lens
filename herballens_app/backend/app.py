from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
import json
from PIL import Image, ImageOps
from tensorflow.keras.applications.efficientnet import preprocess_input
from deep_translator import GoogleTranslator

import os

import sys

# Configure standard output to flush immediately for better logging
import functools
print = functools.partial(print, flush=True)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Get absolute path to files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "herbal_model.keras")
CLASS_INDICES_PATH = os.path.join(BASE_DIR, "class_indices.json")

# Global model variable for lazy loading
model = None

def get_model():
    global model
    if model is None:
        print(f"Loading model from: {MODEL_PATH}...")
        try:
            # Disable JIT to see if it prevents silent crashes
            os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices=false'
            # Load the actual model. If it fails, we want to know why.
            model = tf.keras.models.load_model(MODEL_PATH, compile=False)
            print("Model loaded successfully!")
        except Exception as e:
            print(f"CRITICAL ERROR loading model: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e # Raise the error so we don't use a dummy model
    return model

# Load class names
print("Loading class indices...")
with open(CLASS_INDICES_PATH) as f:
    class_indices = json.load(f)
# Ensure indices are handled correctly (some JSONs have "0": "Name", others "Name": 0)
if isinstance(list(class_indices.keys())[0], str) and isinstance(list(class_indices.values())[0], int):
    class_names = {int(v): k for k, v in class_indices.items()}
else:
    class_names = {int(k): v for k, v in class_indices.items()}

print(f"Loaded {len(class_names)} classes.")

# Load detailed plant info
PLANT_INFO_PATH = os.path.join(BASE_DIR, "plant_info.json")
try:
    with open(PLANT_INFO_PATH) as f:
        plant_info = json.load(f)
    print("Plant info loaded successfully.")
except Exception as e:
    print(f"Note: Could not load plant_info.json: {e}")
    plant_info = {}

def preprocess_image(image):
    # 1. Handle EXIF orientation (important for mobile uploads)
    image = ImageOps.exif_transpose(image)
    
    # 2. Convert to RGB
    image = image.convert("RGB")
    
    # 3. Standard Preprocessing: Many models are trained with simple squashing
    # to (224, 224) rather than aspect-ratio padding.
    target_size = (224, 224)
    image = image.resize(target_size, Image.Resampling.LANCZOS)
    
    # Debug: Save what the model actually sees
    # image.save(os.path.join(BASE_DIR, "debug_preprocessed.jpg"))
    
    img_array = np.array(image).astype(np.float32)
    
    # Expand dims to (1, 224, 224, 3)
    img_array = np.expand_dims(img_array, axis=0)
    
    # Note: Our model summary shows a Rescaling layer, 
    # so we should NOT divide by 255 manually here.
    return img_array

@app.route("/predict", methods=["POST"])
def predict():
    print("\n--- NEW PREDICTION REQUEST ---")
    try:
        if "image" not in request.files:
            print("Error: No image in request.files")
            return jsonify({"error": "No image uploaded"}), 400
            
        file = request.files["image"]
        if file.filename == '':
            print("Error: Empty filename")
            return jsonify({"error": "No selected file"}), 400

        print(f"1. Processing file: {file.filename}")
        image = Image.open(file).convert("RGB")
        
        print("2. Getting model...")
        current_model = get_model()
        
        print("3. Preprocessing image...")
        processed_img = preprocess_image(image)
        print(f"   Shape: {processed_img.shape}, Dtype: {processed_img.dtype}")
        
        print("4. Running model prediction...")
        # Try direct call first
        preds = current_model(processed_img, training=False)
        pred_array = preds.numpy()
        
        # If confidence is extremely low (< 1%), try with preprocess_input fallback
        # This handles cases where the model might NOT have the rescaling layer 
        # as expected or behaves differently.
        if np.max(pred_array) < 0.01:
            print("   Low confidence detected, trying fallback preprocessing...")
            fallback_img = preprocess_input(processed_img)
            preds = current_model(fallback_img, training=False)
            pred_array = preds.numpy()
        
        print("6. Processing results...")
        top_indices = np.argsort(pred_array[0])[-3:][::-1]
        
        print("Top 3 Predictions:")
        for i, idx_top in enumerate(top_indices):
            name = class_names.get(int(idx_top), "Unknown")
            conf = float(pred_array[0][idx_top]) * 100
            print(f"  {i+1}. {name}: {conf:.2f}%")

        idx = int(top_indices[0])
        confidence = float(pred_array[0][idx]) * 100
        plant_name = class_names.get(idx, "Unknown Plant")
        
        print(f"7. Final Result: {plant_name} ({confidence:.2f}%)")

        # Prepare details and translate to Telugu if needed
        details = plant_info.get(plant_name, {
            "scientific_name": "Information not available",
            "description": "We are currently gathering more details about this specific herbal plant.",
            "benefits": ["General medicinal properties"]
        })

        # Add Telugu translations for the details
        details_te = {
            "description": details.get("description", ""),
            "benefits": details.get("benefits", [])
        }
        
        try:
            translator = GoogleTranslator(source='en', target='te')
            # Translate description
            if details.get("description"):
                details_te["description"] = translator.translate(details["description"])
            
            # Translate benefits
            translated_benefits = []
            for benefit in details.get("benefits", []):
                translated_benefits.append(translator.translate(benefit))
            details_te["benefits"] = translated_benefits
            
            # Translate plant name if it's not "Unknown Plant"
            plant_name_te = plant_name
            if plant_name != "Unknown Plant":
                # Some plant names might be underscores, replace them for better translation
                clean_name = plant_name.replace("_", " ")
                plant_name_te = translator.translate(clean_name)
        except Exception as e:
            print(f"Prediction translation error: {e}")
            plant_name_te = plant_name
            details_te = details # Fallback to English

        return jsonify({
            "plant": plant_name,
            "plant_te": plant_name_te,
            "confidence": round(confidence, 2),
            "details": details,
            "details_te": details_te
        })
    except Exception as e:
        print(f"!!! PREDICTION ERROR !!!: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        query = data.get("query", "").lower().strip()
        
        if not query:
            return jsonify({"response": "I'm here to help! What herbal remedy are you looking for?"})

        # Comprehensive health mapping with 400+ symptoms (Minute, Common, Moderate, Chronic, Serious)
        synonyms = {
            # 🫧 MINUTE / TINY ISSUES (Daily discomforts)
            "hiccups": ["hiccup", "hiccupping", "sudden hiccups", "eating too fast", "drinking too fast"],
            "dry lips": ["chapped lips", "cracked lips", "lip dryness", "peeling lips", "lip care", "dry mouth corner"],
            "foot cracks": ["cracked heels", "heel cracks", "dry feet", "rough feet", "foot care", "hard skin on feet"],
            "tech neck": ["stiff neck", "neck pain from mobile", "neck strain", "scrolling pain", "computer neck", "text neck", "neck stiffness"],
            "eye strain": ["tired eyes", "dry eyes", "screen fatigue", "burning eyes", "eye heaviness", "computer vision", "eye itchiness"],
            "sunburn": ["sun rash", "burnt skin", "red skin from sun", "sun irritation", "sun peeling", "beach burn"],
            "dizziness": ["mild dizziness", "spinning head", "lightheadedness", "faint feeling", "feeling unsteady"],
            "leg cramps": ["calf pain", "muscle twitching", "night cramps", "leg stiffness", "muscle spasms", "toe cramps"],
            "dry mouth": ["thirst", "sticky mouth", "low saliva", "dry throat at night", "cotton mouth"],
            "bad breath": ["morning breath", "mouth odor", "smelly breath", "oral hygiene", "stinky mouth", "bad taste"],
            "sweaty palms": ["body odor", "excessive sweating", "smelly armpits", "sweaty feet", "clammy hands", "perspiration"],
            "brittle nails": ["weak nails", "nail breaking", "nail health", "yellow nails", "soft nails", "nail splitting"],
            "snoring": ["mild snoring", "nasal block at night", "heavy breathing", "sleep noise", "night congestion"],
            "morning stiffness": ["stiff joints", "hard to move in morning", "body ache after waking", "waking up stiff"],
            "prickly heat": ["heat rash", "sweat rash", "itchy skin in summer", "red bumps", "miliaria", "skin heat"],
            "bloating": ["full stomach", "heavy stomach", "stomach gurgling", "gas after beans", "tight stomach"],
            "burping": ["excessive burping", "belching", "sour belching", "air in stomach", "noisy stomach"],
            "cuts": ["scratches", "paper cut", "small wound", "minor scrape", "bleeding finger", "skin nick"],
            "muscle fatigue": ["tired muscles", "body weakness", "after workout pain", "doms", "sore muscles", "physical exhaustion"],
            "stress": ["mental stress", "anxiety", "tension", "nervousness", "stress relief", "daily stress"],
            "low appetite": ["not feeling hungry", "loss of taste", "no interest in food", "appetite loss"],
            "burning sensation": ["spicy food reaction", "mouth burning", "stomach heat", "burning throat"],
            "dark circles": ["puffy eyes", "under eye bags", "tired face", "eye circles", "eye puffiness"],
            "scalp itch": ["dry scalp", "dandruff flakes", "itchy head", "scalp buildup", "head itch"],
            "morning sluggishness": ["low energy", "afternoon slump", "tired after lunch", "laziness", "no motivation", "drowsiness"],
            "hoarse voice": ["voice loss", "throat tickle", "shouting pain", "cracked voice", "losing voice"],
            "cold hands": ["cold feet", "chilly feeling", "poor circulation", "shivering", "icy hands"],
            "oily skin": ["excess oil", "greasy face", "open pores", "blackheads", "shiny skin"],
            "joint clicks": ["cracking joints", "clicking knees", "finger cracking", "bone noise", "noisy joints"],
            "brain fog": ["forgetfulness", "poor concentration", "losing keys", "confusion", "mental fatigue", "lack of focus"],
            "insect bites": ["ant bite", "mosquito bite", "bee sting", "itchy bite", "bug bite", "sting relief"],
            "tongue coating": ["white tongue", "coated tongue", "bad taste in morning"],
            "gum sensitivity": ["sensitive gums", "sore gums", "bleeding gums", "gum pain"],
            "chapped skin": ["dry patches", "rough skin", "winter skin", "skin peeling"],
            "minor bruises": ["bump mark", "blue mark", "skin bruise", "hit mark"],
            "sneezing fits": ["recurrent sneezing", "dust allergy", "morning sneezing"],
            "runny nose": ["watery nose", "constant sneezing", "nasal drip"],
            "thirst": ["extreme thirst", "dehydration", "feeling dry"],
            "back ache": ["lower back pain", "stiff back", "sitting too long", "back stiffness"],
            "shoulder tension": ["stiff shoulders", "shoulder ache", "heavy shoulders"],
            "foot fatigue": ["sore feet", "tired feet", "standing too long", "foot pain"],
            "anemia": ["రక్తహీనత", "anemia support", "low iron", "iron deficiency", "blood weakness", "pale skin"],
            "blood purification": ["రక్త శుద్ధి", "purify blood", "blood detox", "toxins in blood", "clean blood"],
            "inflammation": ["వాపు", "swelling", "internal inflammation", "redness", "body swelling", "inflammation relief"],
            "appetite": ["ఆకలి", "poor appetite", "loss of appetite", "not hungry", "appetite loss", "stimulate appetite"],
            "body odor": ["smelly sweat", "excessive body odor", "perspiration smell"],

            # 🟢 GENERAL & COMMON (1-30)
            "fatigue": ["అలసట", "నీరసం", "general fatigue", "morning fatigue", "evening fatigue", "chronic tiredness", "weakness", "laziness", "low energy", "stamina", "tired", "chronic fatigue", "physical exhaustion"],
            "weakness": ["నీరసం", "physical weakness", "mental weakness", "seasonal weakness", "stamina loss", "faint feeling", "dizziness", "body weakness"],
            "body heat": ["శరీర వేడి", "body heat imbalance", "excess body heat", "heat intolerance", "sweating", "gastric heat", "internal heat"],
            "dehydration": ["డీహైడ్రేషన్", "mild dehydration", "severe dehydration", "thirst", "water retention"],
            "fever": ["జ్వరం", "feverish feeling", "mild fever", "viral fever", "temperature", "shivering", "chills", "sibver", "cold sensation", "malarial fever", "dengue fever", "body temperature"],
            "body pain": ["ఒళ్లు నొప్పులు", "నొప్పులు", "body heaviness", "mild body pain", "body stiffness", "general discomfort", "muscle pain", "muscle cramps", "muscle stiffness", "muscle inflammation"],
            "wound healing": ["దెబ్బలు తగ్గడం", "పుండ్లు తగ్గడం", "heal wounds", "cuts", "scratches", "external wounds", "minor burns", "wound infections", "antiseptic", "skin healing"],

            "blood purification": ["రక్త శుద్ధి", "purify blood", "blood detox", "clear skin", "blood cleanser"],
            "fatigue": ["అలసట", "నీరసం", "tiredness", "weakness", "low energy", "exhaustion", "general weakness", "physical fatigue"],
            "inflammation": ["వాపు", "మంట", "swelling", "internal inflammation", "redness", "painful swelling"],
            
            # 👂👃👅 ENT & RESPIRATORY (31-70)
            "common cold": ["జలుబు", "seasonal cold", "recurrent cold", "sneezing", "runny nose", "nasal discharge", "blocked nose", "nasal congestion", "nasal irritation", "chest congestion"],
            "sore throat": ["గొంతు నొప్పి", "throat pain", "dry throat", "burning throat", "hoarseness", "voice loss", "itchy throat", "throat irritation", "throat swelling", "throat clearing", "throat infection"],
            "sinusitis": ["సైనస్", "sinus pressure", "nasal block", "congestion", "headache"],
            "ear problems": ["చెవి నొప్పి", "ear heaviness", "ear itching", "ear discomfort", "ear pain", "ear blockage", "tinnitus"],
            "cough": ["దగ్గు", "dry cough", "wet cough", "chronic cough", "night cough", "allergic cough", "chest congestion", "chest tightness", "persistent cough"],
            "asthma": ["ఆయాసం", "దమ్ము", "mild asthma", "wheezing", "breathlessness", "shortness of breath", "respiratory issues", "bronchitis support"],

            # 🥣 DIGESTIVE (71-110)
            "indigestion": ["అజీర్ణం", "chronic indigestion", "slow digestion", "irregular digestion", "weak digestion", "stomach burning", "sour belching", "bitter taste", "food intolerance", "digestive weakness", "poor digestion"],
            "gas": ["గ్యాస్", "కడుపు ఉబ్బరం", "gas formation", "excess gas", "trapped gas", "bloating", "flatulence", "burping", "gas after meals", "stomach gas", "digestive bloating", "stomach discomfort"],
            "acidity": ["ఎసిడిటీ", "కడుపులో మంట", "hyperacidity", "heartburn", "chest burning", "stomach burning", "reflux", "gastric irritation", "stomach acidity", "digestive irritation"],
            "nausea": ["వికారం", "morning nausea", "motion nausea", "vomiting tendency", "vomit", "bitter mouth", "motion sickness"],
            "vomiting": ["వాంతులు", "mild vomiting", "nausea", "stomach upset"],
            "constipation": ["మలబద్ధకం", "mild constipation", "hard stools", "bowel movement", "irregular bowels"],
            "diarrhea": ["విరేచనాలు", "loose stools", "soft stools", "loose motions", "stomach cramps", "dysentery", "digestive cramps"],
            "piles": ["మొలలు", "hemorrhoids", "hemorrhoids (piles)", "anal swelling", "rectal pain"],
            "worms": ["కడుపులో పురుగులు", "worm infestation", "intestinal worms", "parasitic issues", "stomach worms"],
            "antioxidant support": ["యాంటీ ఆక్సిడెంట్", "detox", "rejuvenation", "antioxidant", "vitality boost", "cell protection"],
            "throat irritation": ["గొంతు గీర", "scratchy throat", "throat tickle", "irritated throat", "throat clearing", "hoarse voice"],

            # ✨ SKIN, HAIR, ORAL (111-150)
            "acne": ["మొటిమలు", "pimples", "mild acne", "oily skin acne", "dry skin acne", "hormonal acne", "adult acne", "pimple", "skin breakouts"],
            "skin rashes": ["చర్మంపై దద్దుర్లు", "చర్మపు మంట", "skin redness", "skin itching", "sunburn", "heat rash", "allergy", "eczema", "dermatitis", "skin irritation", "skin inflammation", "skin disorders", "skin diseases"],
            "dry skin": ["పొడి చర్మం", "excessively dry skin", "dull skin", "uneven skin tone", "skin dryness", "skin dullness", "chapped skin"],
            "hair fall": ["జుట్టు రాలడం", "excess hair fall", "seasonal hair fall", "hair thinning", "weak hair roots", "hairloss", "hairfall", "hair loss", "hair damage", "premature greying"],
            "dandruff": ["చుండ్రు", "severe dandruff", "dry scalp", "itchy scalp", "scalp infections"],
            "mouth ulcers": ["నోటి పూత", "నోటి ఇన్ఫెక్షన్", "recurrent mouth ulcers", "burning mouth", "oral dryness", "oral infections"],
            "gum problems": ["చిగుళ్ల సమస్యలు", "నోటి దుర్వాసన", "gum bleeding", "gum swelling", "tooth sensitivity", "bad breath", "oral discomfort", "gum health", "oral health"],

            # 🟡 MODERATE PROBLEMS (151-250)
            "joint pain": ["కీళ్ల నొప్పులు", "మోకాళ్ల నొప్పులు", "నడుము నొప్పి", "knee pain", "back pain", "lower back pain", "neck stiffness", "muscle cramps", "muscle pain", "arthritis", "sprains", "ligament strain", "bone weakness", "joint stiffness", "bone health", "bone density", "strengthen bones"],
            "infections": ["ఇన్ఫెక్షన్", "సోకు", "fungal skin infection", "ringworm", "scabies", "boils", "skin abscess", "uti", "burning urination", "frequent urination", "urinary infections", "bacterial infections", "fungal infections", "antiseptic", "disinfectant"],
            "mental health": ["మానసిక సమస్యలు", "ఒత్తిడి", "ఆందోళన", "stress", "chronic stress", "anxiety", "panic feeling", "poor concentration", "memory weakness", "mild depression", "low mood", "irritability", "anger issues", "memory loss", "mental fatigue"],
            "sleep": ["నిద్రలేమి", "నిద్ర పట్టకపోవడం", "insomnia", "sleep disturbance", "disturbed sleep cycle", "daytime sleepiness", "fatigue with stress", "sleep disorders", "restless sleep"],
            "headache": ["తలనొప్పి", "తల భారంగా ఉండటం", "stress headache", "tension headache", "migraine", "head ache"],
            "hormonal": ["హార్మోన్ సమస్యలు", "irregular periods", "hormonal imbalance", "menstrual cramps", "irregular menstruation", "excessive menstrual bleeding", "pms", "menstrual fatigue", "menstrual disorders", "uterine health support", "pcos"],
            "immunity": ["రోగ నిరోధక శక్తి", "రోగ నిరోధక శక్తి తగ్గడం", "weak immunity", "frequent cold", "frequent infections", "seasonal allergies", "dust allergy", "pollen allergy", "skin allergy", "immune disorders", "immune weakness"],
            "metabolic": ["మెటబాలిక్", "జీవక్రియ", "weight gain", "weight loss", "metabolic imbalance", "metabolic disorders", "insulin resistance"],

            # 🟠 CHRONIC & 🔴 SERIOUS (251-300)
            "diabetes": ["షుగర్", "చక్కెర వ్యాధి", "మధుమేహం", "type 2 diabetes", "prediabetes", "uncontrolled diabetes", "diabetes with fatigue", "sugar", "diabetes support", "blood sugar imbalance", "high blood sugar"],
            "obesity": ["అధిక బరువు", "స్థూలకాయం", "obesity", "central obesity", "weight management", "metabolic syndrome"],
            "high blood pressure": ["బీపీ", "రక్తపోటు", "hypertension", "chronic high bp", "hypertensive", "high blood pressure support"],
            "cholesterol": ["కొలెస్ట్రాల్", "blood circulation", "heart health", "heart health support"],
            "liver disorders": ["కాలేయ సమస్యలు", "fatty liver", "chronic liver disorder", "liver cirrhosis", "liver weakness", "jaundice support"],
            "kidney support": ["కిడ్నీ సమస్యలు", "మూత్రపిండాల సమస్యలు", "chronic kidney weakness", "urinary support", "kidney stones (support)", "kidney health support"],
            "thyroid": ["థైరాయిడ్", "thyroid imbalance", "hypothyroidism", "hyperthroidism"],
            "recovery": ["కోలుకోవడం", "నీరసం నుండి కోలుకోవడం", "dengue recovery", "malaria recovery", "tuberculosis support", "chronic infection recovery", "post-dengue weakness", "post-illness weakness"]
        }

        # Expand query with synonyms
        original_query = query.lower()
        print(f"DEBUG: Original query: {original_query}")
        # Split query into parts to catch multiple conditions
        query_parts = [p.strip() for p in original_query.replace(",", " and ").split(" and ") if p.strip()]
        print(f"DEBUG: Query parts: {query_parts}")
        
        primary_terms = set(query_parts)
        expanded_terms = set()
        for key, syn_list in synonyms.items():
            # Check if the key or any of its synonyms are in the query
            if any(key in part or any(syn in part for syn in syn_list) for part in query_parts):
                print(f"DEBUG: Matched category: {key}")
                primary_terms.add(key)
                for syn in syn_list:
                    expanded_terms.add(syn)
        
        print(f"DEBUG: Primary terms: {primary_terms}")
        # Remove primary terms from expanded terms to avoid double counting
        expanded_terms = expanded_terms - primary_terms

        # Search in plant_info
        matches = []
        for plant, info in plant_info.items():
            benefits_list = [b.lower() for b in info.get("benefits", [])]
            description = info.get("description", "").lower()
            plant_name_lower = plant.lower()
            
            score = 0
            matched_conditions = 0
            
            # 1. Check for primary terms (High priority)
            for term in primary_terms:
                term_lower = term.lower()
                term_matched = False
                for b in benefits_list:
                    if term_lower == b or term_lower in b or b in term_lower:
                        score += 50 # Base score for matching a primary condition
                        term_matched = True
                        break
                
                if term_matched:
                    matched_conditions += 1
                elif term_lower in description:
                    score += 5
                elif term_lower in plant_name_lower:
                    score += 10
            
            # Bonus for matching multiple query terms
            if matched_conditions > 1:
                score += (matched_conditions * 20)
            
            # 2. Check for expanded synonyms (Lower priority)
            for term in expanded_terms:
                term_lower = term.lower()
                for b in benefits_list:
                    if term_lower == b or term_lower in b or b in term_lower:
                        score += 5
                        break
                else:
                    if term_lower in description:
                        score += 1
            
            if score > 0:
                matches.append({"name": plant, "score": score, **info})

        print(f"DEBUG: Total matches found: {len(matches)}")

        if matches:
            # Sort by score descending, then by name for consistency
            matches.sort(key=lambda x: (-x["score"], x["name"]))
            
            # Debug log
            print(f"Query: {query}")
            print(f"Top matches: {[(m['name'], m['score']) for m in matches[:5]]}")
            
            # Only return 1 or 2 plants as requested
            top_matches = matches[:2]
            
            response_text_en = "Here are the best herbal remedies for your query:\n\n"
            
            for match in top_matches:
                # Provide a concise name and usage info
                response_text_en += f"🌿 **{match['name']}**: {match['description']}\n\n"
            
            response_text_en += "⚠️ *Note: If symptoms persist or are severe, please visit a doctor.*"
            
            # Translate to Telugu for voice
            try:
                # Remove symbols for better translation quality
                text_to_translate = response_text_en.replace("🌿", "").replace("**", "").replace("⚠️", "").replace("*", "")
                
                # Check if we have a very common response that we can pre-translate to save time/avoid errors
                if "I couldn't find a specific herbal remedy" in text_to_translate:
                    response_text_te = "దీనికి సంబంధించి నాకు నిర్దిష్టమైన మూలికా నివారణ కనిపించలేదు. మీ భద్రత కోసం, దయచేసి సరైన నిర్ధారణ కోసం వైద్యుడిని సందర్శించండి."
                else:
                    translator = GoogleTranslator(source='en', target='te')
                    response_text_te = translator.translate(text_to_translate)
                
                # If translation is too short or failed, fallback
                if not response_text_te or len(response_text_te) < 5:
                    response_text_te = text_to_translate
            except Exception as e:
                print(f"Translation error: {e}")
                # Provide a more helpful fallback message if translation fails
                response_text_te = "క్షమించండి, అనువాదంలో సమస్య ఉంది. (Sorry, there was a translation error.)"

            return jsonify({
                "response": response_text_en.strip(),
                "response_te": response_text_te.strip()
            })
        
        return jsonify({
            "response": "I couldn't find a specific herbal remedy for this. For your safety, please visit a doctor for a proper diagnosis.",
            "response_te": "దీనికి సంబంధించి నాకు నిర్దిష్టమైన మూలికా నివారణ కనిపించలేదు. మీ భద్రత కోసం, దయచేసి సరైన నిర్ధారణ కోసం వైద్యుడిని సందర్శించండి."
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Standard production-like run
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
