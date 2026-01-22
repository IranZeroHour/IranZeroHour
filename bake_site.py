import os
import yaml
from google import genai
from google.genai import types

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def fetch_intel(config):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # System Instruction from your refined prompt
    system_instr = f"""ACT AS: Senior Watch Officer & Intelligence Analyst. 
    PROJECT: {config['project_name']}
    TASK: Monitor live data for 'Hard Security' events occurring strictly within the last 15 minutes. 
    STYLE: LiveUAMap Tactical Feed + High-Level Geopolitical Analysis.
    FORMATTING: Return ONLY raw HTML <div> blocks using the tactical-entry class."""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text("Generate the latest tactical report for the Iran sector.")],
        ),
    ]

    generate_config = types.GenerateContentConfig(
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
        system_instruction=system_instr,
        thinking_config=types.ThinkingConfig(thinking_level="HIGH")
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-thinking-exp", 
        contents=contents, 
        config=generate_config
    )
    return response.text

def bake_site(content, config):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{config['project_name']} | Tactical Dashboard</title>
        <style>
            body {{ background: #06080a; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 20px; }}
            .sidebar {{ border-left: 2px solid #238636; padding-left: 20px; max-width: 800px; margin: auto; }}
            h1 {{ color: #ffffff; border-bottom: 1px solid #30363d; padding-bottom: 10px; font-weight: 300; letter-spacing: 2px; }}
            .tactical-entry {{ background: #0d1117; border: 1px solid #30363d; padding: 20px; margin-bottom: 15px; border-radius: 6px; }}
            .header {{ display: flex; justify-content: space-between; font-size: 0.85em; margin-bottom: 12px; font-family: monospace; }}
            .datetime {{ color: #8b949e; }}
            .location-tag {{ color: #58a6ff; font-weight: bold; }}
            .severity-badge {{ padding: 2px 8px; border-radius: 2px; text-transform: uppercase; font-size: 0.9em; }}
            .FLASH {{ background: #da3633; color: #fff; }}
            .WARNING {{ background: #d29922; color: #000; }}
            .intel-body {{ line-height: 1.6; margin-bottom: 15px; border-left: 3px solid #30363d; padding-left: 15px; }}
            .strategic-analysis {{ font-size: 0.9em; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding-top: 15px; border-top: 1px solid #21262d; }}
            .iran-impact strong {{ color: #f85149; }}
            .opposition-impact strong {{ color: #58a6ff; }}
        </style>
    </head>
    <body>
        <h1>{config['project_name']} // OSINT_FEED</h1>
        <div class="sidebar">
            {content}
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    cfg = load_config()
    intel = fetch_intel(cfg)
    bake_site(intel, cfg)
