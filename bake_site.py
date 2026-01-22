import os
import json
import requests
import re
import google.generativeai as genai

# --- OBFUSCATED CONFIGURATION ---
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
        
    headers = {'User-Agent': 'ZeroHour/1.0'}
    url = f"https://newsapi.org/v2/everything?q={SEARCH_TERM}&sortBy=publishedAt&pageSize=6&language=en&apiKey={NEWS_SOURCE}"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def process_data(raw_data):
    print("Analyzing pattern (Gemini Core)...")
    if not raw_data: return []
    
    try:
        # Configure Gemini
        genai.configure(api_key=AI_ENGINE)
        model = genai.GenerativeModel('gemini-pro')
        
        # Prepare Data
        data_block = "\n".join([f"- {a['title']}" for a in raw_data])
        full_prompt = f"{INSTRUCTION}\n\nINPUT DATA:\n{data_block}"
        
        # Generate
        response = model.generate_content(full_prompt)
        content = response.text
        
        # Clean Markdown
        cleaned = content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"Analysis failed (Using fallback): {e}")
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

    js_payload = f'\n    const timelineData = {json.dumps(output)};\n'
    
    # Targeted Regex: Only replaces the content inside the script tag with id="data-core"
    # This prevents overwriting the main application logic
    pattern = r'(<script id="data-core">)([\s\S]*?)(</script>)'
    
    if re.search(pattern, html):
        new_html = re.sub(
            pattern, 
            lambda m: m.group(1) + js_payload + m.group(3), 
            html
        )
        
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            f.write(new_html)
    else:
        print("CRITICAL: Data injection point not found in HTML.")

if __name__ == "__main__":
    raw = get_input()
    if raw:
        processed = process_data(raw)
        update_display(processed, raw)
        print("Sequence complete.")
    else:
        print("No input found.")
