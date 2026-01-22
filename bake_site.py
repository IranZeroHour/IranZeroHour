import os
import json
import requests
import re
from openai import OpenAI

# --- CONFIGURATION ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TARGET_FILE = "index.html"
SEARCH_QUERY = "Iran military protests regime"

# --- 1. FETCH RAW INTEL ---
def fetch_raw_news():
    print("Fetching raw data...")
    url = f"https://newsapi.org/v2/everything?q={SEARCH_QUERY}&sortBy=publishedAt&pageSize=5&language=en&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get('articles', [])
    except Exception as e:
        print(f"News fetch failed: {e}")
        return []

# --- 2. PROCESS WITH LLM ---
def militarize_headlines(articles):
    print("Processing with LLM...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Prepare the list for the LLM
    raw_text = "\n".join([f"- {a['title']}" for a in articles])
    
    prompt = f"""
    You are a military intelligence officer. 
    Convert the following news headlines into strictly FACTUAL, URGENT, UPPERCASE ALERTS.
    Rules:
    1. Maximum 15 words per headline.
    2. No emotional or filler words.
    3. Output as a JSON list of strings.
    
    Input Headlines:
    {raw_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Cheap and fast
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        # Parse the string response back to a list
        content = response.choices[0].message.content
        # Clean up code blocks if the LLM adds them
        content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"LLM processing failed: {e}")
        # Fallback: Just use raw titles if LLM fails
        return [a['title'].upper() for a in articles]

# --- 3. BAKE HTML ---
def bake_site(processed_headlines, original_articles):
    print("Baking HTML...")
    
    # Combine the LLM headline with the raw timestamp
    final_data = []
    for i, headline in enumerate(processed_headlines):
        if i < len(original_articles):
            # Extract time (HH:MM)
            raw_time = original_articles[i]['publishedAt']
            time_code = raw_time.split('T')[1][:5] + " UTC"
            
            final_data.append({
                "time": time_code,
                "headline": headline
            })

    # Read HTML
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # Create JS Injection
    js_payload = "const timelineData = " + json.dumps(final_data) + ";"
    
    # Regex Insertion
    pattern = r'(\s*<script>)([\s\S]*?)(</script>\s*)'
    replacement = r'\1\n                ' + js_payload + r'\n            \3'
    
    new_html = re.sub(pattern, replacement, html)
    
    # Write Back
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("Success.")

# --- EXECUTE ---
if __name__ == "__main__":
    raw_articles = fetch_raw_news()
    if raw_articles:
        clean_headlines = militarize_headlines(raw_articles)
        bake_site(clean_headlines, raw_articles)
    else:
        print("No news found. Aborting.")
