import requests
import re
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
import numpy as np
from flask import Flask, request, jsonify

# Flask App Setup
app = Flask(__name__)

# WhatsApp API Credentials
access_token = "EAAe0ISuwvocBO4rczbG0MhPfbzejfQOOfdG5gxndNZAZBK2QA6dBiC21lqolZBidXjaIZClB4igZAIsPW52adCp7XhmlzZB5hnqlDhvAzl7m02i4ecVRkCYpx0H2ApSWZB1u4WJg1P9c4ZC3V856ZCucr7dfidJUA5t6kHydRgD5GPtFtxHfZAZAMQcKRvZCnuZCjCJoByv4m1mMIxf5Xi7BfNRZCpfmj9SWzhyMd1HswZD"
phone_number_id = "8124063917"

# MongoDB Setup
mongo_client = MongoClient("mongodb+srv://your_username:your_password@cluster.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["drug_detection"]
collection = db["wa_mentions"]

# Keywords and Patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'party favors']
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
    print("Message Sent:", response.json())

# Analyze Messages
def analyze_message(message_text):
    keyword_count = sum(1 for keyword in drug_keywords if keyword.lower() in message_text.lower())
    pattern_count = sum(1 for pattern in suspicious_patterns if re.search(pattern, message_text))
    return keyword_count, pattern_count

# WhatsApp Webhook Endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_data = request.json

    # Extract message and sender details
    try:
        if "messages" in incoming_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            message_info = incoming_data["entry"][0]["changes"][0]["value"]["messages"][0]
            phone = message_info["from"]
            message_text = message_info["text"]["body"]

            print(f"Received message from {phone}: {message_text}")

            # Analyze message
            keyword_count, pattern_count = analyze_message(message_text)

            # Store in MongoDB
            collection.insert_one({
                "phone": phone,
                "message": message_text,
                "length": len(message_text),
                "keyword_count": keyword_count,
                "pattern_count": pattern_count
            })

            # Send acknowledgment message
            send_message(phone, "Your message is under review.")

            return jsonify({"status": "Message processed."}), 200
    except Exception as e:
        print("Error processing message:", str(e))
        return jsonify({"error": str(e)}), 500

# Anomaly Detection
@app.route("/detect_anomalies", methods=["GET"])
def detect_anomalies():
    messages = list(collection.find({}, {"_id": 0, "length": 1, "keyword_count": 1, "pattern_count": 1}))

    if not messages:
        return jsonify({"error": "No messages found."}), 404

    features = np.array([[msg["length"], msg["keyword_count"], msg["pattern_count"]] for msg in messages])

    model = IsolationForest(contamination=0.1, random_state=42)
    anomaly_scores = model.fit_predict(features)

    # Identify anomalies
    anomalies = [messages[i] for i in range(len(messages)) if anomaly_scores[i] == -1]

    return jsonify({"anomalies": anomalies}), 200

# Start Flask Application
if __name__ == "__main__":
    app.run(port=5000, debug=True)