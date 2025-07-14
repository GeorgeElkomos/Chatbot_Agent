import json

def _load_project_database() -> str:
    with open("./System-Info/Database Tables.json", "r", encoding="utf-8") as f:
        return json.dumps(json.load(f))
