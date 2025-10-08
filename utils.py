"""
File: utils.py (relative to Chatbot_Agent)
"""

import os
import sys
import json
import logging
from contextlib import contextmanager

OUTPUT_DIR = "./ai-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def set_global_logging(logs: bool):
    """Globally suppress or enable logging for CrewAI and Python, but not print()."""
    if not logs:
        logging.getLogger().setLevel(logging.CRITICAL)
        logging.getLogger("crewai").setLevel(logging.CRITICAL)


@contextmanager
def suppress_stdout():
    """Context manager to suppress stdout (print output) temporarily."""
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout


def save_history(history):
    """Save the conversation history to a JSON file."""
    history_file = os.path.join(OUTPUT_DIR, "history.json")
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def save_responses(final_outputs):
    """Save the agent responses to a JSON file."""
    responses_file = os.path.join(OUTPUT_DIR, "responses.json")
    with open(responses_file, "w", encoding="utf-8") as f:
        json.dump(final_outputs, f, ensure_ascii=False, indent=2)


def end_and_save(history, final_outputs):
    """Save both history and responses at the end of the run."""
    save_history(history)
    save_responses(final_outputs)


def filter_output(final_outputs):
    """Filter the final outputs to only include relevant agent responses."""
    filtered_outputs = {}
    for agent_name, response in final_outputs.items():
        # Handle None responses
        if response is None:
            filtered_outputs[agent_name] = None
            continue

        if agent_name == "PageNavigatorAgent":
            filtered_outputs[agent_name] = response.get("navigation_link")
        elif agent_name == "SQLBuilderAgent":
            filtered_outputs[agent_name] = response.get("HTML_TABLE_DATA")
        else:
            filtered_outputs[agent_name] = response.get("response")
    return filtered_outputs
