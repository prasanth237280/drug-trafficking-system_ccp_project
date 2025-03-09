from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.sessions import MemorySession  # Add this import
import pandas as pd
import re
from datetime import datetime
from pymongo import MongoClient

api_id = '27089251'  # API ID
api_hash = '4b941c7958c760da931dc6c4012f5d4c'  # API Hash
phone = '+918807147526'  # Phone number

# Drug-related keywords and patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'party favors']
suspicious_patterns = [r'for sale', r'order now', r'delivery']

# Risk scoring weights
WEIGHT_KEYWORD = 30
WEIGHT_PATTERN = 20
WEIGHT_ACTIVITY = 50

async def scan_telegram():
    client = TelegramClient(MemorySession(), api_id, api_hash)
    await client.start(phone=phone)
    print("Connected to Telegram!")

    # Real public Telegram channel usernames
    channels = ['Moviesi', 'tonkeeper_news']

    # Connect to MongoDB Atlas
    mongo_client = MongoClient("mongodb+srv://Prasanth2310:Yogarajvijayabanu7280@project1.15nmf.mongodb.net/?retryWrites=true&w=majority&appName=Project1")  # Connection string
    db = mongo_client["drug_detection"]
    collection = db["channel_mentions"]

    all_results = []

    for channel_name in channels:
        try:
            channel = await client(ResolveUsernameRequest(channel_name))
            channel_title = channel.chats[0].title
            print(f"Scanning channel: {channel_title}")

            messages = await client.get_messages(channel.chats[0], limit=50)
            channel_risk = 0
            message_count = 0

            for msg in messages:
                if msg.message:
                    message_text = msg.message.lower()
                    risk_score = 0

                    for keyword in drug_keywords:
                        if keyword.lower() in message_text:
                            risk_score += WEIGHT_KEYWORD
                            print(f"Keyword '{keyword}' found in message: {message_text}")

                    for pattern in suspicious_patterns:
                        if re.search(pattern, message_text):
                            risk_score += WEIGHT_PATTERN
                            print(f"Pattern '{pattern}' found in message: {message_text}")

                    if risk_score > 0:
                        message_count += 1
                        result = {
                            'channel': channel_title,
                            'message': msg.message,
                            'date': msg.date,
                            'risk_score': risk_score
                        }
                        all_results.append(result)
                        collection.insert_one(result)

            if message_count > 0:
                channel_risk = (sum(r['risk_score'] for r in all_results if r['channel'] == channel_title) / message_count) + (WEIGHT_ACTIVITY if message_count > 10 else 0)
            else:
                channel_risk = 0

            print(f"Channel '{channel_title}' risk score: {channel_risk}")

        except Exception as e:
            print(f"Error scanning {channel_name}: {e}")

    # Save results to CSV and print MongoDB confirmation
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv('drug_mentions.csv', index=False)
        print("Found drug-related messages! Saved to drug_mentions.csv")

    print("Data stored in MongoDB Atlas.")

# Run the script
with TelegramClient(MemorySession(), api_id, api_hash) as client:
    client.loop.run_until_complete(scan_telegram())