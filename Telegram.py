from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
import pandas as pd
import re
from datetime import datetime

api_id = '27089251'  #API ID
api_hash = '4b941c7958c760da931dc6c4012f5d4c'  # Your API Hash
phone = '+918807147526'  #phone number

# Drug-related keywords and patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'party favors']
suspicious_patterns = [r'for sale', r'order now', r'delivery']

# Risk scoring weights (customizable)
WEIGHT_KEYWORD = 30  # Points for keyword match
WEIGHT_PATTERN = 20  # Points for suspicious pattern
WEIGHT_ACTIVITY = 50  # Points for frequent activity (placeholder; expand later)

async def scan_telegram():
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start(phone=phone)
    print("Connected to Telegram!")

    # List of public channels to monitor (replace with real ones or dynamically search)
    channels = ['testchannel1', 'testchannel2']  # Example; add more or automate search

    all_results = []

    for channel_name in channels:
        try:
            channel = await client(ResolveUsernameRequest(channel_name))
            channel_title = channel.chats[0].title
            print(f"Scanning channel: {channel_title}")

            # Get recent messages (limit to 50 for now; adjust as needed)
            messages = await client.get_messages(channel.chats[0], limit=50)
            
            channel_risk = 0
            message_count = 0

            for msg in messages:
                if msg.message:  # Check if message has text
                    message_text = msg.message.lower()
                    risk_score = 0

                    # Check keywords
                    for keyword in drug_keywords:
                        if keyword.lower() in message_text:
                            risk_score += WEIGHT_KEYWORD
                            print(f"Keyword '{keyword}' found in message: {message_text}")

                    # Check patterns
                    for pattern in suspicious_patterns:
                        if re.search(pattern, message_text):
                            risk_score += WEIGHT_PATTERN
                            print(f"Pattern '{pattern}' found in message: {message_text}")

                    if risk_score > 0:
                        message_count += 1
                        all_results.append({
                            'channel': channel_title,
                            'message': msg.message,
                            'date': msg.date,
                            'risk_score': risk_score
                        })

            # Calculate channel-level risk (simplified: average per message, plus activity weight)
            if message_count > 0:
                channel_risk = (sum(r['risk_score'] for r in all_results if r['channel'] == channel_title) / message_count) + (WEIGHT_ACTIVITY if message_count > 10 else 0)
            else:
                channel_risk = 0

            print(f"Channel '{channel_title}' risk score: {channel_risk}")

        except Exception as e:
            print(f"Error scanning {channel_name}: {e}")

    # Save results to CSV
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv('drug_mentions.csv', index=False)
        print("Found drug-related messages! Saved to drug_mentions.csv")

    # Store high-risk channels in a simple MySQL database (placeholder; expand later)
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="your_username",
            password="your_password",
            database="drug_detection"
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel_name VARCHAR(255),
                risk_score FLOAT,
                timestamp DATETIME
            )
        """)
        for result in all_results:
            cursor.execute("""
                INSERT INTO channels (channel_name, risk_score, timestamp)
                VALUES (%s, %s, %s)
            """, (result['channel'], result['risk_score'], datetime.now()))
        conn.commit()
        print("Data stored in MySQL database.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# Run the script
with TelegramClient('session_name', api_id, api_hash) as client:
    client.loop.run_until_complete(scan_telegram())