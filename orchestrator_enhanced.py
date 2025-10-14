"""
Enhanced Orchestrator with Conversation History and User Interaction
Allows agents to ask for missing information and maintains rich conversation context
"""

import json
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from crewai import Crew, Process, Task
from agents import *
from utils import (
    set_global_logging,
    suppress_stdout,
    save_history,
    end_and_save,
    filter_output,
)
from agents.fusion_Analytics.smart_db_updater import get_updater, trigger_update
from iteration_tracker import get_tracker

MAX_MESSAGES = 2 * 10  # Keep last 10 user + assistant pairs (was 3)
ENABLE_USER_INTERACTION = True  # Set to False to disable asking user


class UserInteractionNeeded(Exception):
    """Raised when agent needs information from user"""
    def __init__(self, question: str, context: Dict[str, Any] = None):
        self.question = question
        self.context = context or {}
        super().__init__(question)


def initialize_app():
    updater = get_updater(cooldown_seconds=5)
    updater.set_update_function(refresh_expense_database)
    print("[OK] Database updater initialized")


def refresh_expense_database(db_path: str):
    """Refresh the expense database"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expense_report_data")
    print(f"Refreshed: {cursor.fetchone()[0]} records")
    conn.close()


initialize_app()


def detect_missing_information(agent_response: Dict[str, Any], agent_name: str) -> Optional[str]:
    """
    Detect if agent is asking for missing information
    Returns the question if found, None otherwise
    """
    response_str = json.dumps(agent_response, ensure_ascii=False).lower()
    
    # Check for common patterns indicating missing information
    asking_patterns = [
        "please provide",
        "please specify",
        "which employee",
        "which department",
        "what date",
        "what period",
        "need to know",
        "can you specify",
        "could you provide",
        "what is the",
        "missing",
        "clarify",
        "more information",
        "need more details",
        "<",  # Placeholder like <employee_name>
    ]
    
    # Check response field for questions
    response_text = agent_response.get("response", "") or \
                   agent_response.get("User_Frendly_response", "") or \
                   agent_response.get("User_Friendly_response", "") or \
                   str(agent_response)
    
    if any(pattern in response_text.lower() for pattern in asking_patterns):
        # Extract the question
        if "?" in response_text:
            # Find the question
            lines = response_text.split("\n")
            for line in lines:
                if "?" in line and any(pattern in line.lower() for pattern in asking_patterns):
                    return line.strip()
        return response_text
    
    return None


def check_convergence(history, N=2):
    """Check if agents are producing identical outputs (stuck in loop)"""
    if len(history) >= N * 2:
        last_outputs = [
            entry["output"]
            for entry in reversed(history)
            if entry.get("agent") not in ("ManagerAgent", "GeneralQAAgent")
        ][:N]
        if len(last_outputs) == N and all(r == last_outputs[0] for r in last_outputs):
            return True
    return False


def handle_convergence(history, user_request, final_outputs):
    """Handle when agents are stuck in a loop"""
    last_agent_result = None
    last_agent_name = None
    for entry in reversed(history):
        agent_name = entry.get("agent")
        if agent_name not in ("GeneralQAAgent", "ManagerAgent"):
            last_agent_result = entry.get("output")
            last_agent_name = agent_name
            break
    if last_agent_result:
        final_task = Task(
            description=(
                f"The following data was calculated by agent '{last_agent_name}':\n{last_agent_result}\n"
                f"Please summarize these results in plain English for the user request: {user_request}.\nDo not repeat the table, but explain what the data means."
            ),
            expected_output="User-friendly summary of the results",
            agent=get_agent("GeneralQAAgent"),
            output_json=QAResponse,
        )
        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=False,
            telemetry=False,
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = gen_result.json_dict
        history.append({"agent": "GeneralQAAgent", "output": gen_result.json_dict})
    history.append(
        {
            "agent": "System",
            "output": "Convergence detected: repeated identical results. Stopping.",
        }
    )
    return True


def run_manager_agent(
    user_request, latest_response, history, conversation_history, logs=True
):
    """Run the manager agent to decide which worker agent should handle the request"""
    manager_task = create_manager_task(
        {
            "user_request": user_request,
            "latest_response": latest_response,
            "history": json.dumps(history, ensure_ascii=False),
            "conversation_history": conversation_history,
        }
    )

    tracker = get_tracker()
    tracker.start_agent_execution("ManagerAgent")

    manager_crew = Crew(
        agents=[manager_agent],
        tasks=[manager_task],
        process=Process.sequential,
        verbose=logs,
        telemetry=False,
    )
    manager_result = manager_crew.kickoff()
    decision_json = manager_result.json_dict

    track_internal = tracker.end_agent_execution()

    history.append(
        {
            "agent": "ManagerAgent",
            "output": decision_json,
            "track_internal": track_internal,
        }
    )

    save_history(history)

    return decision_json, history


def handle_manager_stop(user_request, history, final_outputs, logs=True):
    """Handle when manager decides to stop"""
    if "GeneralQAAgent" not in final_outputs:
        last_agent_result = None
        last_agent_name = None
        for entry in reversed(history):
            agent_name = entry.get("agent")
            if agent_name not in ("GeneralQAAgent", "ManagerAgent"):
                last_agent_result = entry.get("output")
                last_agent_name = agent_name
                break

        if last_agent_result:
            final_task = Task(
                description=(
                    f"The following data was calculated by agent '{last_agent_name}':\n{last_agent_result}\n"
                    f"Please summarize these results in plain English for the user request: {user_request}.\nDo not repeat the table, but explain what the data means."
                ),
                expected_output="User-friendly summary of the results",
                agent=get_agent("GeneralQAAgent"),
                output_json=QAResponse,
            )
        else:
            final_task = Task(
                description=f"Provide a final answer to the user request: {user_request}",
                expected_output="User-friendly summary of the results",
                agent=get_agent("GeneralQAAgent"),
                output_json=QAResponse,
            )

        tracker = get_tracker()
        tracker.start_agent_execution("GeneralQAAgent")

        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=logs,
            telemetry=False,
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = gen_result.json_dict

        track_internal = tracker.end_agent_execution()

        history.append(
            {
                "agent": "GeneralQAAgent",
                "output": gen_result.json_dict,
                "track_internal": track_internal,
            }
        )

        save_history(history)

    return True


def run_worker_agent(
    next_agent_name,
    next_task_description,
    user_request,
    worker_agent_latest_responce,
    final_outputs,
    history,
    conversation_history,
    logs=True,
):
    """Run a worker agent to handle specific task"""
    worker_agent = get_agent(next_agent_name)
    if worker_agent is None:
        from agents.registry.main import get_agent_descriptions
        registered_agents = get_agent_descriptions()
        raise ValueError(
            f"Unknown agent requested by Manager: {next_agent_name}. Available agents: {list(registered_agents.keys())}"
        )

    agent_output = get_agent_output(next_agent_name)
    schema_str = ""
    if (
        agent_output is not None
        and isinstance(agent_output, type)
        and issubclass(agent_output, BaseModel)
    ):
        try:
            schema_dict = agent_output.model_json_schema()
        except AttributeError:
            schema_dict = agent_output.schema()
        import json as _json
        schema_str = _json.dumps(schema_dict.get("properties", {}), indent=2)
        description = (
            (next_task_description or f"Handle user request: {user_request}")
            + f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"
            f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}"
            + "\n\nReturn STRICTLY valid JSON conforming to this schema:\n"
            + schema_str
            + "\n"
        )
        worker_task = Task(
            description=description,
            expected_output=agent_output.__name__ + " JSON",
            agent=worker_agent,
            output_json=agent_output,
        )
    elif agent_output is not None and not isinstance(agent_output, type):
        worker_task = Task(
            description=(
                next_task_description or f"Handle user request: {user_request}"
            )
            + f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"
            + f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}"
            + "\n\nYou must return a valid JSON object conforming to the output schema of this agent.",
            expected_output=agent_output.__class__.__name__ + " JSON",
            agent=worker_agent,
            output=agent_output,
        )
    else:
        worker_task = Task(
            description=(
                next_task_description or f"Handle user request: {user_request}"
            )
            + f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"
            + f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}",
            expected_output="Complete response to the task",
            agent=worker_agent,
        )

    tracker = get_tracker()
    tracker.start_agent_execution(next_agent_name)

    worker_crew = Crew(
        agents=[worker_agent],
        tasks=[worker_task],
        process=Process.sequential,
        verbose=logs,
        telemetry=False,
    )
    worker_result = worker_crew.kickoff()
    agent_response = worker_result.json_dict

    track_internal = tracker.end_agent_execution()

    final_outputs[next_agent_name] = agent_response
    history.append(
        {
            "agent": next_agent_name,
            "output": agent_response,
            "track_internal": track_internal,
        }
    )

    save_history(history)

    # ✅ Check if agent is asking for more information
    if ENABLE_USER_INTERACTION:
        question = detect_missing_information(agent_response, next_agent_name)
        if question:
            raise UserInteractionNeeded(question, {
                "agent": next_agent_name,
                "response": agent_response,
                "history": history
            })

    return agent_response, history


def trim_history(conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Trim conversation history to last MAX_MESSAGES"""
    if len(conversation_history) <= MAX_MESSAGES:
        return conversation_history
    return conversation_history[-MAX_MESSAGES:]


def format_conversation_history(conversation_history: List[Dict[str, str]]) -> str:
    """Format conversation history for agent consumption"""
    formatted = []
    for turn in conversation_history:
        role = turn.get("role", "").lower()
        content = turn.get("content", "")
        if role == "user":
            formatted.append(f"User: {content}")
        elif role == "assistant":
            formatted.append(f"Assistant: {content}")
        elif role == "summary":
            formatted.append(f"Summary of earlier conversation:\n{content}")
        else:
            formatted.append(f"{role.capitalize()}: {content}")
    return "\n".join(formatted)


def orchestrate(
    user_request: str, 
    conversation_history: list = [], 
    logs: bool = True,
    interactive: bool = True
) -> Dict[str, Any]:
    """
    Main orchestration function with conversation history and user interaction support
    
    Args:
        user_request: The user's current request
        conversation_history: List of previous conversation turns
        logs: Whether to show verbose logs
        interactive: Whether to enable asking user for missing information
    
    Returns:
        Dictionary with filtered outputs, or dict with 'needs_input' if user interaction needed
    """
    global ENABLE_USER_INTERACTION
    ENABLE_USER_INTERACTION = interactive
    
    conversation_history_formatted = format_conversation_history(
        trim_history(conversation_history)
    )
    final_outputs = {}
    history: List[Dict[str, Any]] = []
    latest_response = ""
    next_agent_name: str = "ManagerAgent"
    stop = False
    next_task_description = ""
    
    if logs == False:
        set_global_logging(False)
    
    try:
        while not stop:
            if check_convergence(history):
                with suppress_stdout():
                    handle_convergence(history, user_request, final_outputs)
                save_history(history)
                break
            
            if next_agent_name == "ManagerAgent":
                with suppress_stdout():
                    decision_json, history = run_manager_agent(
                        user_request, latest_response, history, conversation_history_formatted, logs
                    )
                save_history(history)
                stop = (
                    decision_json.get("stop", False)
                    or decision_json.get("next_agent") == "END"
                )
                if stop:
                    with suppress_stdout():
                        handle_manager_stop(user_request, history, final_outputs, logs)
                    end_and_save(history, final_outputs)
                    break
                next_agent_name = decision_json["next_agent"]
                next_task_description = decision_json.get("next_task_description", "")
            else:
                with suppress_stdout():
                    agent_response, history = run_worker_agent(
                        next_agent_name,
                        next_task_description,
                        user_request,
                        latest_response,
                        final_outputs,
                        history,
                        conversation_history_formatted,
                        logs,
                    )
                latest_response = agent_response
                next_agent_name = "ManagerAgent"
        
        end_and_save(history, final_outputs)
        
    except UserInteractionNeeded as e:
        # Agent needs more information from user
        return {
            "status": "needs_input",
            "question": e.question,
            "context": e.context,
            "partial_outputs": final_outputs,
            "message": "Agent needs more information to continue"
        }
    finally:
        if logs == False:
            set_global_logging(True)
    
    return filter_output(final_outputs)
