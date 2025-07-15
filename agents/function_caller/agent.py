from crewai import Agent
from agents.llm_config import basic_llm
from agents.function_caller.utils.helpers import find_matching_function
from agents.function_caller.tools.function_tools import call_function_from_user_intent

function_caller_agent = Agent(
    role="Function Caller",
    goal="Given a user request, find the best matching API function from the project, extract all required details, and prepare the API call.",
    backstory=(
        "You are an expert at mapping user requests to backend API functions. "
        "You search the available functions, understand their parameters, and prepare the correct API call. "
        "If required data is missing, you ask for it. If the function is not found, you explain why. "
        "You always return the API method, URL, required parameters, and a sample request body."
    ),
    llm=basic_llm,
    tools=[find_matching_function, call_function_from_user_intent],
    verbose=False,
)
