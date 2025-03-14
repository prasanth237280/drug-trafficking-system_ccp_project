import instaloader
import pandas as pd
import re
from datetime import datetime

# Drug-related keywords and patterns
drug_keywords = ['MDMA', 'LSD', 'Mephedrone', 'buy drugs', 'narcotics', 'party favors', 'cannabis', 'weed', 'deal']
suspicious_patterns = [r'for sale', r'order now', r'delivery', r'ship to', r'get now']

# Risk scoring weights
WEIGHT_KEYWORD = 30
WEIGHT_PATTERN = 20
WEIGHT_ACTIVITY = 50

def scan_instagram():
    # Initialize Instaloader
    L = instaloader.Instaloader()

    # Optionally login (required for private accounts or to avoid rate limits)
    # Uncomment and add your credentials if needed
    # L.login('your_username', 'your_password')

    # Profile or hashtag to scan (replace with your test account or a public profile)
    target = 'testdrugaccount'  # Use a public profile username or hashtag (e.g., 'drugdeal' without #)

    # Results list
    all_results = []
    post_count = 0

    try:
        # Load the profile
        profile = instaloader.Profile.from_username(L.context, target)

        print(f"Scanning profile: {target}")

        # Iterate over the profile's posts (limit to 10 for testing)
        for post in profile.get_posts():
            if post_count >= 10:  # Limit to 10 posts to avoid rate limits
                break

            caption = post.caption if post.caption else ""
            caption_lower = caption.lower()
            risk_score = 0

            # Check for drug keywords
            for keyword in drug_keywords:
                if keyword.lower() in caption_lower:
                    risk_score += WEIGHT_KEYWORD
                    print(f"Keyword '{keyword}' found in post: {caption}")

            # Check for suspicious patterns
            for pattern in suspicious_patterns:
                if re.search(pattern, caption_lower):
                    risk_score += WEIGHT_PATTERN
                    print(f"Pattern '{pattern}' found in post: {caption}")

            if risk_score > 0:
                post_count += 1
                result = {
                    'profile': target,
                    'caption': caption,
                    'date': post.date,
                    'risk_score': risk_score
                }
                all_results.append(result)

        # Calculate profile risk score
        if post_count > 0:
            profile_risk = (sum(r['risk_score'] for r in all_results) / post_count) + (WEIGHT_ACTIVITY if post_count > 5 else 0)
        else:
            profile_risk = 0

        print(f"Profile '{target}' risk score: {profile_risk}")

    except Exception as e:
        print(f"Error scanning {target}: {e}")

    # Save results to CSV
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv('drug_mentions_instagram.csv', index=False)
        print("Found drug-related posts! Saved to drug_mentions_instagram.csv")

if __name__ == "__main__":
    scan_instagram()