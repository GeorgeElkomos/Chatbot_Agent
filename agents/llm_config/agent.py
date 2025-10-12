"""
File: agents/llm_config/agent.py (relative to Chatbot_Agent)
"""

from crewai import LLM, BaseLLM
import os
from iteration_tracker import get_tracker

OUTPUT_DIR = "./ai-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create base LLM
_base_llm = LLM(
    name="BasicLLM",
    model="gemini/gemini-2.0-flash-lite",
    api_key="AIzaSyC9nt1TDrXevbKCVNdHTIlUsoHdPpe5dY0",  # "AIzaSyC9nt1TDrXevbKCVNdHTIlUsoHdPpe5dY0", "AIzaSyB33PBwcjDf47uXtFwy2Szvz607TJSEkZY" , "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    output_dir=OUTPUT_DIR,
    max_tokens=8192,
    temperature=0.1,
    top_p=0.9,
)



# _base_llm = LLM(
#     name="BasicLLM",
#     model="ollama/gemma3:27b",  # Format: ollama/<model_name>
#     base_url="http://localhost:11434",  # Ollama default port
#     output_dir=OUTPUT_DIR,
#     temperature=0.1,
#     # Note: Ollama doesn't use api_key or top_p
# )






# Store original call method
_original_call = _base_llm.call


def _tracked_call(messages, *args, **kwargs):
    """Wrapper for LLM call that tracks inputs and outputs"""
    tracker = get_tracker()

    # Check if we're already in an iteration (don't create nested iterations)
    # If current_iteration_data is empty, start a new one
    if not tracker.current_iteration_data:
        tracker.start_iteration()
        should_end = True
    else:
        should_end = False

    # Log input
    tracker.log_llm_input(messages)

    try:
        # Call original LLM
        response = _original_call(messages, *args, **kwargs)

        # Log output
        if isinstance(response, str):
            tracker.log_llm_output(response)
        elif hasattr(response, "content"):
            tracker.log_llm_output(str(response.content))
        elif hasattr(response, "text"):
            tracker.log_llm_output(str(response.text))
        else:
            tracker.log_llm_output(str(response))

        return response

    except Exception as e:
        tracker.log_error(str(e))
        raise
    finally:
        # Only end iteration if we started it
        if should_end:
            tracker.end_iteration()


# Monkey-patch the call method
_base_llm.call = _tracked_call

# Export as basic_llm
basic_llm = _base_llm


# from .ollama_llm import OllamaLLM
# basic_llm = OllamaLLM(model="gemma3:27b", temperature=0.1)
