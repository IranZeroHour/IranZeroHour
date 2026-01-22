import os
from google import genai
from google.genai import types

def fetch_intel():
    """Fetches real-time tactical intel using the Gemini API."""
    # The client automatically uses the GEMINI_API_KEY from GitHub Secrets
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Project Settings (formerly in YAML)
    project_name = "IRAN ZERO HOUR"
    model_id = "gemini-2.0-flash-thinking-exp"

    system_instr = f"""ACT AS: Senior Watch Officer & Intelligence Analyst. 
    PROJECT: {project_name}
    TASK: Monitor live data for 'Hard Security' events occurring strictly within the last 15 minutes. 
    STYLE: LiveUAMap Tactical Feed + High-Level Geopolitical Analysis.
    FORMATTING: Return ONLY raw HTML <div> blocks using the tactical-entry class."""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text("Generate the latest tactical report for the Iran sector.")],
        ),
    ]

    config = types.GenerateContentConfig(
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
        system_instruction=system_instr
    )

    response = client.models.generate_content(model=model_id, contents=contents, config=config)
    return response.text

def bake_site(content):
    """Injects the AI content into the index.html template."""
    # Reads the existing index.html template from the repo
    with open("index.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    # Replaces the {content} placeholder with the new tactical reports
    final_site = template.replace("{content}", content)
    
    # Writes the updated site back to index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_site)

if __name__ == "__main__":
    try:
        raw_intel = fetch_intel()
        bake_site(raw_intel)
        print("Successfully updated index.html with latest intel.")
    except Exception as e:
        print(f"Error during intel update: {e}")
        exit(1)
