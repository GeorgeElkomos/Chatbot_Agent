from crewai import Agent
from agents.llm_config.agent import basic_llm
from agents.page_navigator.tools.project_tools import Update_query_project_pages

page_navigator_agent = Agent(
    role="Page Navigator",
    goal=(
        "Identify when the user wants to navigate and provide two outputs in JSON format: "
        "1. 'navigation_link': the navigation link (e.g., /projects/create) or an empty string if no navigation is needed. "
        "2. 'response': a user-friendly description or instructions about the link or, if requested, a summary of all available pages."
    ),
    backstory=(
        "You understand the structure of the web-application intimately and decide whether to navigate the user. "
        "When the user asks to move somewhere, always return ONLY the navigation link (e.g., /projects/create) in the 'navigation_link' field, and nothing else. "
        "In the 'response' field, provide a user-friendly explanation, instructions, or summary about the link or requested pages. "
        "If the user requests a summary of all pages, return an empty string for 'navigation_link' and a user-friendly summary for 'info'. "
        "Your output must be a valid JSON object: {'navigation_link': '<link or empty string>', 'response': '<user-friendly description>'}."
    ),
    llm=basic_llm,
    tools=[Update_query_project_pages],
    verbose=True,
)
