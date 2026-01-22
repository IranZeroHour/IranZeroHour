import os
import re
from google import genai
from google.genai import types

def generate_intel():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.0-flash-exp" # Optimized for speed and search

    system_instruction = """ACT AS: Senior Watch Officer & Intelligence Analyst. 
    TASK: Monitor live feeds for "Hard Security" events occurring strictly within the last 15 minutes in Iran or its proxies. 
    STYLE: LiveUAMap Tactical Feed + High-Level Geopolitical Analysis.
    
    GUIDELINES:
    - Only events from the last 15 minutes.
    - Analysis Requirements: Each entry must explain strategic shifts for the Iranian regime and the counter-effect for opposing forces.
    - Formatting: Return only raw HTML <div> blocks using the tactical-entry structure. No markdown code blocks.
    """

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="Generate the latest 15-minute tactical intelligence SITREPs for the Iran theater.")],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        system_instruction=system_instruction,
        temperature=0.7,
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    # Clean response to ensure only HTML is present
    intel_html = response.text.replace("```html", "").replace("```", "").strip()
    return intel_html

def bake_site():
    # 1. Get the generated intel
    new_intel = generate_intel()

    # 2. Read the template
    with open("index.html", "r", encoding="utf-8") as f:
        template = f.read()

    # 3. Handle the injection
    # If {content} exists (first run), replace it. 
    # If not, we find the container and prepend to maintain a feed history.
    if "{content}" in template:
        final_output = template.replace("{content}", new_intel)
    else:
        container_tag = '<main id="intel-container">'
        insertion_point = template.find(container_tag) + len(container_tag)
        final_output = template[:insertion_point] + "\n" + new_intel + template[insertion_point:]

    # 4. Write back to index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_output)
    
    print("Tactical Feed Baked Successfully.")

if __name__ == "__main__":
    bake_site()
