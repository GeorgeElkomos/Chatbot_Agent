"""
File: agents/manager/tasks/manager_task.py (relative to Chatbot_Agent)
"""
from crewai import Task
from agents.manager.agent import manager_agent
from agents.registry.main import AGENT_REGISTRY, get_agent_descriptions
from agents.manager.models.schemas import ManagerDecision

def create_manager_task(context):
    agent_descriptions = get_agent_descriptions()
    agent_info_text = "\n".join([
        f"- **{name}**: {description.replace('{', '{{').replace('}', '}}')}" 
        for name, description in agent_descriptions.items()
    ])
    description = (
        "# Manager Decision\n\n"
        "## Available Agents and Their Capabilities\n"
        f"{agent_info_text}\n\n"
        "## Full conversation history (user and assistant turns, JSON)\n{conversation_history}\n\n"
        "## Latest user request\n{user_request}\n\n"
        "## Latest agent response\n{latest_response}\n\n"
        "## Per-request agent mapping history (JSON)\n{history}\n\n"
        "Decide which agent should be called next. Or the task is completed by the latest responce.\n\n"
        "Return STRICTLY valid JSON conforming to this schema:\n"
        "{{\"next_agent\": \"<AgentName or END>\", \"next_task_description\": \"<description>\", \"stop\": <true|false>}}"
    ).format(**context)
    return Task(
        description=description,
        expected_output="ManagerDecision JSON",
        agent=manager_agent,
        output_json=ManagerDecision,
    )
