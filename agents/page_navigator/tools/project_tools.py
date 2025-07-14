# Moved from tools/project_tools.py
# Add any page_navigator agent-specific tool code here
from crewai.tools import tool
from agents.page_navigator.utils.helpers import _load_project_pages

@tool
def Update_query_project_pages(query: str) -> str:
    """Append project-page info so agents can make better navigation decisions."""
    query += "\n\nAll the information you need about the pages of the project is this:\n"
    query += _load_project_pages()
    return query