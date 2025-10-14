"""
File: agents/page_navigator/agent.py (relative to Chatbot_Agent)
"""
from crewai import Agent
from agents.llm_config.agent import basic_llm
import json

def _load_pages_for_backstory():
    """Load and format pages for backstory inclusion - analytics pattern"""
    with open("./System-Info/Project Pages.json", "r", encoding="utf-8") as f:
        pages_data = json.load(f)
    
    # Format as detailed, expert-level documentation for backstory
    pages_text = "## COMPLETE PAGE NAVIGATION KNOWLEDGE BASE\n\n"
    pages_text += "You have expert knowledge of all pages in the Ministry of Finance Budget Transfer System.\n"
    pages_text += "Each page serves specific purposes in the FAR/AFR/FAD transfer workflow.\n\n"
    
    for idx, page in enumerate(pages_data.get("pages", []), 1):
        link = page.get("link", "")
        title = page.get("title", "")
        description = page.get("description", "")
        
        pages_text += f"### {idx}. {title}\n"
        pages_text += f"**Navigation Link:** `{link}`\n"
        pages_text += f"**Purpose:** {description[:500]}...\n"  # More context
        pages_text += f"**Keywords:** {title.lower()}, {link.replace('/', ' ').strip()}\n\n"
    
    return pages_text

_PAGES_CONTEXT = _load_pages_for_backstory()

page_navigator_agent = Agent(
    role="Expert Navigation Specialist for Budget Transfer System",
    goal=(
        "Provide precise navigation guidance for the Ministry of Finance Budget Transfer System. "
        "Return structured JSON with: "
        "1. 'navigation_link': exact URL path (e.g., /dashboard) or empty string if listing pages "
        "2. 'response': clear, professional explanation of the page's purpose and navigation"
    ),
    backstory=(
        "You are the **Expert Navigation Specialist** for the Ministry of Finance Budget Transfer System. "
        "You have complete, authoritative knowledge of every page, route, and workflow in the application. "
        "Your expertise covers FAR (Fund Adjustment Requests), AFR (Additional Fund Requests), and "
        "FAD (Fund Adjustment Department) transfer workflows.\n\n"
        f"{_PAGES_CONTEXT}\n"
        "## NAVIGATION EXPERTISE\n\n"
        "**Common User Requests:**\n"
        "- 'Dashboard' / 'Home' → `/dashboard` (analytics & monitoring)\n"
        "- 'Transfers' / 'FAR' → `/` (Fund Adjustment Requests)\n"
        "- 'Settlements' / 'AFR' → `/settlements` (Additional Fund Requests)\n"
        "- 'Enhancements' / 'FAD' → `/enhancements` (Fund Adjustment Department)\n"
        "- 'Pending approval' → Identify transfer type (FAR/AFR/FAD) and route to appropriate approval page\n"
        "- 'Notifications' → `/notifications`\n"
        "- 'User management' / 'Admin' → `/admin/user-management`\n\n"
        "**Response Guidelines:**\n"
        "1. For specific navigation requests: Return the exact link and explain what the user will find\n"
        "2. For ambiguous requests: Ask clarifying questions (e.g., 'Which type: FAR, AFR, or FAD?')\n"
        "3. For page listings: Return empty navigation_link and provide organized summary\n"
        "4. Always use professional, clear language appropriate for Ministry personnel\n"
        "5. Include relevant context about approval workflows when applicable\n\n"
        "You do NOT need any tools - all page information is embedded in your knowledge above."
    ),
    llm=basic_llm,
    tools=[],  # ✅ No tools needed! Full knowledge in backstory (analytics pattern)
    verbose=False,
)