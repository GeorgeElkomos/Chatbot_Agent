"""
File: agents/page_navigator/utils/helpers.py (relative to Chatbot_Agent)
"""
"""
File: agents/page_navigator/utils/helpers.py (relative to Chatbot_Agent)
"""
import json

def _load_project_pages() -> str:
    with open("./System-Info/Project Pages.json", "r", encoding="utf-8") as f:
        return json.dumps(json.load(f))
