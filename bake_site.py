import os
import json
import requests
import re
from openai import OpenAI

# --- ONFIGURATION  ---

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
AI_API_KEY = os.environ.get("AI_API_KEY")
TARGET_QUERY = os.environ.get("TARGET_QUERY")     
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")   
TARGET_FILE = "index.html"

def fetch_intel():
    print("Fetching data from source...")
    if not TARGET_QUERY or not NEWS_API_KEY:
        print("Error: Missing Query or API Key.")
        return []
        
    url = f"https://newsapi.org/v2/everything?q={TARGET_QUERY}&sortBy=publishedAt&pageSize=6&language=en&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def process_intel(articles):
    print("Processing via Neural Link...")
    if not articles: return []
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    headlines = "\n".join([f"- {a['title']}" for a in articles])
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": headlines}
            ],
            temperature=0.1
        )
        # Expecting JSON list
        content = response.choices[0].message.content
        cleaned_content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_content)
    except Exception as e:
        print(f"AI Processing Error: {e}")
        # Fallback if AI fails: Return raw titles tagged as routine
        return [f"[ROUTINE] {a['title'].upper()}" for a in articles]

def bake_dashboard(processed_data, raw_articles):
    print("Baking static dashboard...")
    final_output = []
    
    # Merge AI text with Official Time
    for i, text in enumerate(processed_data):
        if i < len(raw_articles):
            time_utc = raw_articles[i]['publishedAt'].split('T')[1][:5] + " UTC"
            final_output.append({"time": time_utc, "text": text})

    # Injection
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    js_payload = "const timelineData = " + json.dumps(final_output) + ";"
    pattern = r'(\s*<script>)([\s\S]*?)(</script>\s*)'
    new_html = re.sub(pattern, r'\1\n        ' + js_payload + r'\n        \3', html)
    
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    raw = fetch_intel()
    if raw:
        processed = process_intel(raw)
        bake_dashboard(processed, raw)
        print("Update Complete.")
    else:
        print("No Intel Found.")
