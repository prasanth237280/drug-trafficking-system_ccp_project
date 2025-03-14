from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.sessions import MemorySession
import pandas as pd
import re
from datetime import datetime
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
import numpy as np

api_id = "18118864"
api_hash = "798addea568cb787edd220cc204d7f88"
phone = "+91 8124063917"

# Keywords and patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'party favors']
suspicious_patterns = [r'for sale', r'order now', r'delivery']

async def scan_telegram():
    client = TelegramClient(MemorySession(), api_id, api_hash)
    await client.start(phone=phone)
    print("Connected to Telegram!")

    channels = ['Moviesi', 'tonkeeper_news']

    mongo_client = MongoClient("mongodb+srv://Prasanth2310:Yogarajvijayabanu7280@project1.15nmf.mongodb.net/?retryWrites=true&w=majority&appName=Project1")
    db = mongo_client["drug_detection"]
    collection = db["channel_mentions"]

    all_results = []

    for channel_name in channels:
        try:
            channel = await client(ResolveUsernameRequest(channel_name))
            channel_title = channel.chats[0].title
            print(f"Scanning channel: {channel_title}")

            messages = await client.get_messages(channel.chats[0], limit=50)

            features = []

            for msg in messages:
                if msg.message:
                    message_text = msg.message.lower()
                    keyword_count = sum(1 for keyword in drug_keywords if keyword.lower() in message_text)
                    pattern_count = sum(1 for pattern in suspicious_patterns if re.search(pattern, message_text))

                    sender = await client.get_entity(msg.sender_id) if msg.sender_id else None
                    username = sender.username if sender and hasattr(sender, 'username') else "Unknown"

                    features.append([len(message_text), keyword_count, pattern_count])

                    all_results.append({
                        'channel': channel_title,
                        'username': username,
                        'message': msg.message,
                        'date': msg.date,
                        'length': len(message_text),
                        'keyword_count': keyword_count,
                        'pattern_count': pattern_count
                    })

            # Train Isolation Forest for anomaly detection
            if features:
                model = IsolationForest(contamination=0.1, random_state=42)
                anomaly_scores = model.fit_predict(features)

                for i, result in enumerate(all_results[-len(features):]):
                    result['risk_score'] = -model.decision_function([features[i]])[0]
                    collection.insert_one(result)

                print(f"Processed {len(features)} messages from {channel_title}.")

        except Exception as e:
            print(f"Error scanning {channel_name}: {e}")

    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv('drug_mentions.csv', index=False)
        print("Results saved to drug_mentions.csv")

    print("Data stored in MongoDB Atlas.")

with TelegramClient(MemorySession(), api_id, api_hash) as client:
    client.loop.run_until_complete(scan_telegram())