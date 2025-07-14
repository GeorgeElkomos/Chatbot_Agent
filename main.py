import os
import json
import sys
from contextlib import contextmanager
from typing import Dict, List, Any
from pydantic import BaseModel
from agents.manager.models.schemas import ManagerDecision
from agents.page_navigator.models.schemas import NavigationResponse
from agents.general_qa.models.schemas import QAResponse
from agents.sql_builder.models.schemas import DatabaseResponse
from crewai import Crew, Process
from agents.manager.agent import manager_agent
from agents.registry.agent import get_agent, get_agent_output, register
from agents.page_navigator.agent import page_navigator_agent
from agents.sql_builder.agent import sql_builder_agent
from agents.general_qa.agent import general_qa_agent
from agents.manager.tasks.manager_task import create_manager_task
from remove_emoji import remove_emoji
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Pydantic models for request/response
class ChatbotRequest(BaseModel):
    user_input: str
 
class ChatbotResponse(BaseModel):
    status: str
    response: Dict[str, Any]
    message: str = None
 
class HealthResponse(BaseModel):
    status: str
    message: str

remove_emoji()

OUTPUT_DIR = "./ai-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Register agents (if not already registered in their modules)
register(
    page_navigator_agent, 
    NavigationResponse,
    "PageNavigatorAgent",
    (
        "Handles navigation requests and provides appropriate page links and user-friendly information. "
        "Use when user wants to move to different pages or sections of the application, or requests a summary of available pages. "
        "Final output must be a valid JSON object: {'navigation_link': '<link or empty string>', 'response': '<user-friendly description>'}. "
        "The { navigation_link } field should be the navigation link (e.g., '/', '/register', '/admin/user-management') or an empty string if no navigation is needed. "
        "The { response } field should contain instructions, a summary, or user-friendly information about the link or requested pages."
    )
)
register(
    sql_builder_agent, 
    DatabaseResponse,
    "SQLBuilderAgent",
    (
        "Constructs and executes complex SQL queries with proper JOINs. Specializes in database operations, order calculations, and data analysis. Always loads schema first and returns actual query results."
        "- Always instruct them to 'Load database schema, construct the appropriate SQL query with proper JOINs if needed, execute it, and return the actual results'\n"
        "- For order total calculations: Specifically mention 'Calculate using JOIN across Orders, OrderItems, and Products tables'\n"
        "- Never assign just 'build a query' - always require execution and results\n\n"
    )
)
register(
    general_qa_agent, 
    QAResponse,
    "GeneralQAAgent",
    "Summarizes technical outputs and database results in user-friendly language. Use for explaining complex data or providing final summaries to users."
)
register(
    manager_agent, 
    ManagerDecision,
    "ManagerAgent",
    "Orchestrates the conversation flow and decides which agent should handle each request based on user input and conversation context."
)
# register(function_caller_agent, "FunctionCallerAgent")


def set_global_logging(logs: bool):
    """Globally suppress or enable logging for CrewAI and Python, but not print()."""
    import logging
    if not logs:
        # Only suppress logging, not sys.stdout
        logging.getLogger().setLevel(logging.CRITICAL)
        logging.getLogger("crewai").setLevel(logging.CRITICAL)
    # else:
    #     # Restore logging level if needed (optional, not implemented here)
    #     pass

def check_convergence(history, N=2):
    """Check if the last N non-manager, non-GQA agent responses are identical."""
    if len(history) >= N * 2:
        last_outputs = [
            entry["output"] for entry in reversed(history)
            if entry.get("agent") not in ("ManagerAgent", "GeneralQAAgent")
        ][:N]
        if len(last_outputs) == N and all(r == last_outputs[0] for r in last_outputs):
            return True
    return False

def handle_convergence(history, user_request, final_outputs):
    """Handle the case when convergence is detected and trigger GeneralQAAgent summary."""
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
        )
        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=True,
            telemetry=False
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = str(gen_result)
        history.append({"agent": "GeneralQAAgent", "output": str(gen_result)})
    history.append({"agent": "System", "output": "Convergence detected: repeated identical results. Stopping."})
    return True

def run_manager_agent(user_request, latest_response, history, conversation_history, logs=True):
    """Run the manager agent and return the decision json and updated history.
    Passes both in-history (agent mapping for this request) and out-history (full chat) to the agent.
    """
    manager_task = create_manager_task({
        "user_request": user_request,
        "latest_response": latest_response,
        "history": json.dumps(history, ensure_ascii=False),
        "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
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
    """Handle the case when the manager agent decides to stop and trigger GeneralQAAgent if needed."""
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
            )
        else:
            final_task = Task(
                description=f"Provide a final answer to the user request: {user_request}",
                expected_output="User-friendly summary of the results",
                agent=get_agent("GeneralQAAgent"),
            )
        final_crew = Crew(
            agents=[get_agent("GeneralQAAgent")],
            tasks=[final_task],
            process=Process.sequential,
            verbose=logs,
            telemetry=False
        )
        gen_result = final_crew.kickoff()
        final_outputs["GeneralQAAgent"] = str(gen_result)
    return True

def run_worker_agent(next_agent_name, next_task_description, user_request, final_outputs, history, conversation_history, logs=True):
    """Run the worker agent and update outputs and history.
    Passes both in-history (agent mapping for this request) and out-history (full chat) to the agent.
    """
    worker_agent = get_agent(next_agent_name)
    
    if worker_agent is None:
        from agents.registry.agent import get_agent_descriptions
        registered_agents = get_agent_descriptions()
        raise ValueError(f"Unknown agent requested by Manager: {next_agent_name}. Available agents: {list(registered_agents.keys())}")
    
    from crewai import Task
    # Add conversation_history to the task description for context
    agent_output = get_agent_output(next_agent_name)
    # If agent_output is a Pydantic model type, generate schema string
    schema_str = ""
    if agent_output is not None and isinstance(agent_output, type) and issubclass(agent_output, BaseModel):
        # Use model_json_schema for Pydantic v2, fallback to schema for v1
        try:
            schema_dict = agent_output.model_json_schema()  # Pydantic v2
        except AttributeError:
            schema_dict = agent_output.schema()  # Pydantic v1
        import json as _json
        schema_str = _json.dumps(schema_dict.get("properties", {}), indent=2)
        description = (
            (next_task_description or f"Handle user request: {user_request}") +
            f"\n\nFull conversation history (user and assistant turns):\n{json.dumps(conversation_history, ensure_ascii=False)}"
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
                        f"\n\nFull conversation history (user and assistant turns):\n{json.dumps(conversation_history, ensure_ascii=False)}"+
                        "\n\nYou must return a valid JSON object conforming to the output schema of this agent.",
            expected_output=agent_output.__class__.__name__ + " JSON",
            agent=worker_agent,
            output=agent_output
        )
    else:
        worker_task = Task(
            description=(next_task_description or f"Handle user request: {user_request}") +
                        f"\n\nFull conversation history (user and assistant turns):\n{json.dumps(conversation_history, ensure_ascii=False)}",
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

@contextmanager
def suppress_stdout():
    """Context manager to suppress stdout (print output) temporarily."""
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout


def filter_output(final_outputs):
    """Filter the final outputs to only include relevant agent responses."""
    filtered_outputs = {}
    for agent_name, response in final_outputs.items():
        if agent_name == "PageNavigatorAgent":
            # Only keep PageNavigatorAgent responses
            filtered_outputs[agent_name] = response.get("navigation_link")
        elif agent_name == "SQLBuilderAgent":
            continue  # Skip SQLBuilderAgent for now, as it may return complex data
        else:
            # For other agents, keep the full response
            filtered_outputs[agent_name] = response
    return filtered_outputs

def orchestrate(user_request: str, conversation_history: list = None, logs: bool = True) -> None:
    """Run a full conversation, letting the Manager steer between agents.
    Set logs=False to suppress verbose output from CrewAI agents and crews.
    conversation_history: the out-history (full chat history, user/assistant turns)
    """
    if conversation_history is None:
        conversation_history = []
    # Limit the total character length of the conversation history for context window management
    MAX_HISTORY_CHARS = 6000  # You can adjust this value as needed
    def history_length(hist):
        return sum(len(str(turn.get('content', ''))) for turn in hist)
    # Remove oldest messages until under the limit
    while history_length(conversation_history) > MAX_HISTORY_CHARS and len(conversation_history) > 2:
        # Remove the oldest user+assistant pair (if possible)
        conversation_history.pop(0)
        # Optionally, also pop the next if it's an assistant (to keep pairs)
        if conversation_history and conversation_history[0]['role'] == 'assistant':
            conversation_history.pop(0)
    final_outputs = {}
    history: List[Dict[str, Any]] = []  # in-history: agent mapping for this request
    latest_response = ""
    next_agent_name: str = "ManagerAgent"
    stop = False
    next_task_description = ""
    if logs == False:
        set_global_logging(False)  # Set to False to suppress all output
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
                agent_response, history = run_worker_agent(next_agent_name, next_task_description, user_request, final_outputs, history, conversation_history, logs)
            latest_response = agent_response
            next_agent_name = "ManagerAgent"
    end_and_save(history, final_outputs)
    if logs == False:
        set_global_logging(True)  # Set to False to suppress all output
    return filter_output(final_outputs)



# FastAPI Endpoints
@app.post("/chatbot/public", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    """
    Process user input through the multi-agent system.
    """
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="user_input cannot be empty")
       
        # Run the orchestration with logging disabled for API
        final_outputs = orchestrate(request.user_input, logs=False)
       
        return ChatbotResponse(
            status="success",
            response=final_outputs,
            message="Request processed successfully"
        )
   
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
 
 
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        message="Chatbot API is running successfully"
    )


# Run the FastAPI server with uvicorn 3l4an ana bnsa
# uvicorn chatbot_api:app --host 0.0.0.0 --port 8080 --reload
if __name__ == "__main__":
    import sys    
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        _user_request = "I need to create a FAD transder, please help me with that."
        print("User Input:", _user_request)
        response = orchestrate(_user_request, logs=False)
        print("Final outputs:", response)