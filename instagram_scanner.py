import instaloader
import pandas as pd
import re
import time
from datetime import datetime
from random import randint

# Instagram credentials and target
USERNAME = 'kricket513'
PASSWORD = 'dhoni07'
TARGET_PROFILE = 'kricket513'

# Drug-related keywords and patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'cannabis', 'weed', 'deal']
suspicious_patterns = [r'for sale', r'order now', r'delivery', r'ship to']

# Risk scoring weights
WEIGHT_KEYWORD = 30
WEIGHT_PATTERN = 20
WEIGHT_ACTIVITY = 50

def scan_instagram():
    # Initialize Instaloader
    L = instaloader.Instaloader()

    # Mimic a real browser
    L.context._session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    })

    # Load or create a session
    try:
        L.load_session_from_file(USERNAME)  # Correct method
        print(f"✅ Session loaded for {USERNAME}")
    except FileNotFoundError:
        print("🔐 No session found. Logging in...")
        try:
            L.login(USERNAME, PASSWORD)
            L.save_session_to_file()
            print(f"✅ Session saved for {USERNAME}")
        except instaloader.exceptions.BadCredentialsException:
            print("❌ Invalid credentials. Please check USERNAME and PASSWORD.")
            return
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return

    # Handle rate limits with retries
    def retry_on_401(func, retries=3, delay=600):  # 10-minute delay
        for i in range(retries):
            try:
                return func()
            except instaloader.exceptions.QueryReturnedBadRequestException as e:
                print(f"❌ Rate limit detected: {e}. Waiting {delay}s before retrying ({i+1}/{retries})...")
                time.sleep(delay)
            except instaloader.exceptions.ConnectionException as e:
                print(f"❌ Connection error: {e}. Retrying after {delay}s...")
                time.sleep(delay)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return None
        print(f"❌ Failed after {retries} retries.")
        return None

    # Scan the target profile
    print(f"🔍 Scanning profile: {TARGET_PROFILE}")
    profile = retry_on_401(lambda: instaloader.Profile.from_username(L.context, TARGET_PROFILE))

    if not profile:
        print(f"❌ Failed to load profile: {TARGET_PROFILE}. Check if it exists or if you're blocked.")
        return

    all_results = []
    post_count = 0

    try:
        # Process the profile's posts (limit to 1 for testing)
        for post in profile.get_posts():
            if post_count >= 1:  # Reduced to 1 to minimize rate limits
                break

            caption = post.caption if post.caption else ""
            risk_score = 0

            # Calculate risk score
            for keyword in drug_keywords:
                if keyword.lower() in caption.lower():
                    risk_score += WEIGHT_KEYWORD

            for pattern in suspicious_patterns:
                if re.search(pattern, caption.lower()):
                    risk_score += WEIGHT_PATTERN

            if risk_score > 0:
                post_count += 1
                all_results.append({
                    'profile': TARGET_PROFILE,
                    'caption': caption,
                    'date': post.date,
                    'risk_score': risk_score
                })

            # Increased delay between requests
            time.sleep(randint(120, 300))  # 2-5 minutes

        # Calculate profile risk
        if post_count > 0:
            profile_risk = (sum(r['risk_score'] for r in all_results) / post_count) + \
                           (WEIGHT_ACTIVITY if post_count > 2 else 0)
            print(f"📊 Profile '{TARGET_PROFILE}' risk score: {profile_risk}")
        else:
            print(f"📊 Profile '{TARGET_PROFILE}' risk score: 0 (No suspicious posts found)")

        # Save results if any
        if all_results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pd.DataFrame(all_results).to_csv(f'drug_mentions_instagram_{timestamp}.csv', index=False)
            print(f"✅ Results saved to 'drug_mentions_instagram_{timestamp}.csv'")

    except Exception as e:
        print(f"❌ Error processing posts for {TARGET_PROFILE}: {e}")

if __name__ == "__main__":
    scan_instagram()