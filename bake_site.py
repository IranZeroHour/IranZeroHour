import os
import json
import requests
import re
from openai import OpenAI

NEWS_SOURCE = os.environ.get("NEWS")     
AI_ENGINE = os.environ.get("AI")        
SEARCH_TERM = os.environ.get("QUERY")    
INSTRUCTION = os.environ.get("SYSTEM")   
TARGET_FILE = "index.html"

def get_input():
    print("Acquiring signal...")
    if not SEARCH_TERM or not NEWS_SOURCE:
        print("Signal lost: Missing configuration.")
        return []
        
    url = f"https://newsapi.org/v2/everything?q={SEARCH_TERM}&sortBy=publishedAt&pageSize=6&language=en&apiKey={NEWS_SOURCE}"
    try:
        response = requests.get(url)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def process_data(raw_data):
    print("Analyzing pattern...")
    if not raw_data: return []
    
    client = OpenAI(api_key=AI_ENGINE)

    data_block = "\n".join([f"- {a['title']}" for a in raw_data])
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": data_block}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        cleaned = content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"Analysis failed: {e}")
        return [f"[ROUTINE] {a['title'].upper()}" for a in raw_data]

def update_display(processed_data, raw_data):
    print("Updating display...")
    output = []
    
    for i, text in enumerate(processed_data):
        if i < len(raw_data):
            time_stamp = raw_data[i]['publishedAt'].split('T')[1][:5] + " UTC"
            output.append({"time": time_stamp, "text": text})

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    js_payload = "const timelineData = " + json.dumps(output) + ";"
    pattern = r'(\s*<script>)([\s\S]*?)(</script>\s*)'
    new_html = re.sub(pattern, r'\1\n        ' + js_payload + r'\n        \3', html)
    
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    raw = get_input()
    if raw:
        processed = process_data(raw)
        update_display(processed, raw)
        print("Sequence complete.")
    else:
        print("No input found.")
