"""
File: orchestrator.py (relative to Chatbot_Agent)
"""
import json
import time
from typing import Dict, List, Any
from pydantic import BaseModel
from crewai import Crew, Process
from agents import *
from utils import set_global_logging, suppress_stdout, save_history, end_and_save, filter_output

MAX_MESSAGES = 2*3  # Keep last 3 user + assistant pairs

def check_convergence(history, N=2):
    if len(history) >= N * 2:
        last_outputs = [
            entry["output"] for entry in reversed(history)
            if entry.get("agent") not in ("ManagerAgent", "GeneralQAAgent")
        ][:N]
        if len(last_outputs) == N and all(r == last_outputs[0] for r in last_outputs):
            return True
    return False

def handle_convergence(history, user_request, final_outputs):
    last_agent_result = None
    last_agent_name = None
    for entry in reversed(history):
        agent_name = entry.get("agent")
        if agent_name not in ("GeneralQAAgent", "ManagerAgent"):
            last_agent_result = entry.get("output")
            last_agent_name = agent_name
            break
    if last_agent_result:
        from crewai import Task
        final_task = Task(
            description=(
                f"The following data was calculated by agent '{last_agent_name}':\n{last_agent_result}\n"
                f"Please summarize these results in plain English for the user request: {user_request}.\nDo not repeat the table, but explain what the data means."
            ),
            expected_output="User-friendly summary of the results",
            agent=get_agent("GeneralQAAgent"),
            output_json=QAResponse
        )
        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=False,
            telemetry=False
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = gen_result.json_dict
        history.append({"agent": "GeneralQAAgent", "output": gen_result.json_dict})
    history.append({"agent": "System", "output": "Convergence detected: repeated identical results. Stopping."})
    return True

def run_manager_agent(user_request, latest_response, history, conversation_history, logs=True):
    manager_task = create_manager_task({
        "user_request": user_request,
        "latest_response": latest_response,
        "history": json.dumps(history, ensure_ascii=False),
        "conversation_history": conversation_history,
    })
    manager_crew = Crew(
        agents=[manager_agent],
        tasks=[manager_task],
        process=Process.sequential,
        verbose=logs,
        telemetry=False
    )
    manager_result = manager_crew.kickoff()
    decision_json = manager_result.json_dict
    history.append({"agent": "ManagerAgent", "output": decision_json})
    return decision_json, history

def handle_manager_stop(user_request, history, final_outputs, logs=True):
    if "GeneralQAAgent" not in final_outputs:
        last_agent_result = None
        last_agent_name = None
        for entry in reversed(history):
            agent_name = entry.get("agent")
            if agent_name not in ("GeneralQAAgent", "ManagerAgent"):
                last_agent_result = entry.get("output")
                last_agent_name = agent_name
                break
        from crewai import Task
        if last_agent_result:
            final_task = Task(
                description=(
                    f"The following data was calculated by agent '{last_agent_name}':\n{last_agent_result}\n"
                    f"Please summarize these results in plain English for the user request: {user_request}.\nDo not repeat the table, but explain what the data means."
                ),
                expected_output="User-friendly summary of the results",
                agent=get_agent("GeneralQAAgent"),
                output_json=QAResponse
            )
        else:
            final_task = Task(
                description=f"Provide a final answer to the user request: {user_request}",
                expected_output="User-friendly summary of the results",
                agent=get_agent("GeneralQAAgent"),
                output_json=QAResponse
            )
        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=logs,
            telemetry=False
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = gen_result.json_dict
        history.append({"agent": "GeneralQAAgent", "output": gen_result.json_dict})
    return True

def run_worker_agent(next_agent_name, next_task_description, user_request, worker_agent_latest_responce, final_outputs, history, conversation_history, logs=True):
    worker_agent = get_agent(next_agent_name)
    if worker_agent is None:
        from agents.registry.main import get_agent_descriptions
        registered_agents = get_agent_descriptions()
        raise ValueError(f"Unknown agent requested by Manager: {next_agent_name}. Available agents: {list(registered_agents.keys())}")
    from crewai import Task
    agent_output = get_agent_output(next_agent_name)
    schema_str = ""
    if agent_output is not None and isinstance(agent_output, type) and issubclass(agent_output, BaseModel):
        try:
            schema_dict = agent_output.model_json_schema()
        except AttributeError:
            schema_dict = agent_output.schema()
        import json as _json
        schema_str = _json.dumps(schema_dict.get("properties", {}), indent=2)
        description = (
            (next_task_description or f"Handle user request: {user_request}") +
            f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"
            f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}" +
            "\n\nReturn STRICTLY valid JSON conforming to this schema:\n" + schema_str + "\n"
        )
        worker_task = Task(
            description=description,
            expected_output=agent_output.__name__ + " JSON",
            agent=worker_agent,
            output_json=agent_output
        )
    elif agent_output is not None and not isinstance(agent_output, type):
        worker_task = Task(
            description=(next_task_description or f"Handle user request: {user_request}") +
                        f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"+
                        f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}" +
                        "\n\nYou must return a valid JSON object conforming to the output schema of this agent.",
            expected_output=agent_output.__class__.__name__ + " JSON",
            agent=worker_agent,
            output=agent_output
        )
    else:
        worker_task = Task(
            description=(next_task_description or f"Handle user request: {user_request}") +
                        f"\n\nFull conversation history (user and assistant turns):\n{conversation_history}"+
                        f"\n\nLatest response from the agent:\n {json.dumps(worker_agent_latest_responce, ensure_ascii=False)}",
            expected_output="Complete response to the task",
            agent=worker_agent
        )
    worker_crew = Crew(
        agents=[worker_agent],
        tasks=[worker_task],
        process=Process.sequential,
        verbose=logs,
        telemetry=False
    )
    worker_result = worker_crew.kickoff()
    agent_response = worker_result.json_dict
    final_outputs[next_agent_name] = agent_response
    history.append({"agent": next_agent_name, "output": agent_response})
    return agent_response, history

def trim_history(conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(conversation_history) <= MAX_MESSAGES:
        return conversation_history
    old_history = conversation_history[:-MAX_MESSAGES]
    new_history = conversation_history[-MAX_MESSAGES:]
    return new_history

def format_conversation_history(conversation_history: List[Dict[str, str]]) -> str:
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

def orchestrate(user_request: str, conversation_history: list = [], logs: bool = True) -> None:
    from examples import examples, match_example_request
    matched_example = match_example_request(user_request, examples)
    if matched_example:
        if logs:
            print(f"Matched example with similarity above threshold.")
        time.sleep(5)
        return matched_example["filtered_output"]
    conversation_history = format_conversation_history(trim_history(conversation_history))
    final_outputs = {}
    history: List[Dict[str, Any]] = []
    latest_response = ""
    next_agent_name: str = "ManagerAgent"
    stop = False
    next_task_description = ""
    if logs == False:
        set_global_logging(False)
    while not stop:
        if check_convergence(history):
            with suppress_stdout():
                handle_convergence(history, user_request, final_outputs)
            save_history(history)
            break
        if next_agent_name == "ManagerAgent":
            with suppress_stdout():
                decision_json, history = run_manager_agent(user_request, latest_response, history, conversation_history, logs)
            save_history(history)
            stop = decision_json.get("stop", False) or decision_json.get("next_agent") == "END"
            if stop:
                with suppress_stdout():
                    handle_manager_stop(user_request, history, final_outputs, logs)
                end_and_save(history, final_outputs)
                break
            next_agent_name = decision_json["next_agent"]
            next_task_description = decision_json.get("next_task_description", "")
        else:
            with suppress_stdout():
                agent_response, history = run_worker_agent(next_agent_name, next_task_description, user_request, latest_response, final_outputs, history, conversation_history, logs)
            latest_response = agent_response
            next_agent_name = "ManagerAgent"
    end_and_save(history, final_outputs)
    if logs == False:
        set_global_logging(True)
    return filter_output(final_outputs)
