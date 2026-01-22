import os
import json
import requests
import re
import google.generativeai as genai

# --- CONFIGURATION ---
# Secrets are injected via GitHub Actions (see update.yml)
NEWS_SOURCE = os.environ.get("NEWS")
AI_ENGINE = os.environ.get("AI")
SEARCH_BASE = os.environ.get("QUERY")  # Now strictly from secrets
SYSTEM_PROMPT = os.environ.get("SYSTEM") # Now strictly from secrets
TARGET_FILE = "index.html"

def get_input():
    print("Acquiring intelligence signals...")
    if not NEWS_SOURCE or not SEARCH_BASE:
        print("Signal lost: Missing configuration (NEWS or QUERY).")
        return []
        
    headers = {'User-Agent': 'ZeroHour/2.0 (IntelOps)'}
    
    # The QUERY secret should contain the full boolean logic:
    # e.g., "Iran AND (military OR IRGC OR nuclear OR missile OR strike OR army)"
    url = f"https://newsapi.org/v2/everything?q={SEARCH_BASE}&sortBy=publishedAt&pageSize=15&language=en&apiKey={NEWS_SOURCE}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get('articles', [])
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def process_data(raw_data):
    print("Synthesizing tactical report (Gemini Core)...")
    if not raw_data: return []
    if not SYSTEM_PROMPT:
        print("CRITICAL: System instruction secret (SYSTEM) is missing.")
        return []
    
    try:
        genai.configure(api_key=AI_ENGINE)
        model = genai.GenerativeModel('gemini-pro')
        
        feed_content = "\n".join([f"- {a['title']} (Source: {a['source']['name']})" for a in raw_data])
        
        # The prompt logic is now hidden in your GitHub Secret "SYSTEM"
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nRAW INTEL:\n{feed_content}")
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"Analysis failed (Fallback Mode): {e}")
        return [f"[ROUTINE] {a['title']}" for a in raw_data[:6]]

def update_display(processed_data, raw_data):
    print("Updating dashboard...")
    output = []
    
    for i, text in enumerate(processed_data):
        if i < len(raw_data):
            t_raw = raw_data[i]['publishedAt']
            time_stamp = t_raw.split('T')[1][:5] + " UTC"
            output.append({"time": time_stamp, "text": text})

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    js_payload = f'\n    const timelineData = {json.dumps(output)};\n'
    
    pattern = r'(<script id="data-core">)([\s\S]*?)(</script>)'
    
    if re.search(pattern, html):
        new_html = re.sub(
            pattern, 
            lambda m: m.group(1) + js_payload + m.group(3), 
            html
        )
        
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("Dashboard updated successfully.")
    else:
        print("CRITICAL ERROR: Injection anchor <script id='data-core'> not found.")

if __name__ == "__main__":
    raw_intel = get_input()
    if raw_intel:
        tactical_summary = process_data(raw_intel)
        update_display(tactical_summary, raw_intel)
    else:
        print("No intel sources available.")
