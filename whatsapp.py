import requests
import re
import time
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
import numpy as np

# WhatsApp API Credentials
access_token = "EAAe0ISuwvocBO4rczbG0MhPfbzejfQOOfdG5gxndNZAZBK2QA6dBiC21lqolZBidXjaIZClB4igZAIsPW52adCp7XhmlzZB5hnqlDhvAzl7m02i4ecVRkCYpx0H2ApSWZB1u4WJg1P9c4ZC3V856ZCucr7dfidJUA5t6kHydRgD5GPtFtxHfZAZAMQcKRvZCnuZCjCJoByv4m1mMIxf5Xi7BfNRZCpfmj9SWzhyMd1HswZD"
phone_number_id = "626030410585928"

# MongoDB Setup
mongo_client = MongoClient("mongodb+srv://Prasanth2310:Yogarajvijayabanu7280@project1.15nmf.mongodb.net/?retryWrites=true&w=majority&appName=Project1")
db = mongo_client["drug_detection"]
collection = db["wa_mentions"]

# Keywords and Patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs','sale', 'narcotics', 'party favors']
suspicious_patterns = [r'for sale', r'order now', r'delivery']

# Send Message
def send_message(user_phone, message):
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "messaging_product": "whatsapp",
        "to": user_phone,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, json=data, headers=headers)
    print("Message Sent:", response.status_code, response.json())

# Fetch Messages
def fetch_messages():
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("messages", [])

# Analyze Messages
def analyze_message(message_text):
    keyword_count = sum(1 for keyword in drug_keywords if keyword.lower() in message_text.lower())
    pattern_count = sum(1 for pattern in suspicious_patterns if re.search(pattern, message_text))
    return keyword_count, pattern_count

# Calculate Risk Score
def calculate_risk_score(length, keyword_count, pattern_count, model):
    feature_vector = np.array([[length, keyword_count, pattern_count]])
    risk_score = -model.decision_function(feature_vector)[0]
    return risk_score

# Monitor and Analyze
features = []
while True:
    messages = fetch_messages()

    for msg in messages:
        phone = msg['from']
        text = msg['text']['body']
        keyword_count, pattern_count = analyze_message(text)

        features.append([len(text), keyword_count, pattern_count])

        # Anomaly Detection
        if features:
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(features)
            risk_score = calculate_risk_score(len(text), keyword_count, pattern_count, model)

            # Save to MongoDB
            collection.insert_one({
                "phone": phone,
                "message": text,
                "length": len(text),
                "keyword_count": keyword_count,
                "pattern_count": pattern_count,
                "risk_score": risk_score
            })

        send_message(phone, "Your message is under review.")

    print("monitoring")
    time.sleep(30)
