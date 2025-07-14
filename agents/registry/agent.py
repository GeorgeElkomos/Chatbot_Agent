from crewai import Agent
from typing import Dict, NamedTuple
from agents.llm_config.agent import basic_llm
from pydantic import BaseModel

class AgentInfo(NamedTuple):
    """Container for agent and its description."""
    agent: Agent
    description: str
    output: type

AGENT_REGISTRY: Dict[str, AgentInfo] = {}

def register(agent: Agent, output: BaseModel, agent_name: str = None, description: str = "") -> Agent:
    """Register an agent with an optional description.
    
    Args:
        agent: The CrewAI agent to register
        agent_name: Optional custom name (defaults to agent.role)
        description: Brief description of what this agent does
    """
    name = agent_name or agent.role
    AGENT_REGISTRY[name] = AgentInfo(agent=agent, description=description, output=output)
    return agent

def get_agent_descriptions() -> Dict[str, str]:
    """Get all agent names and their descriptions."""
    return {name: info.description for name, info in AGENT_REGISTRY.items() if name not in ("Manager")}

def get_agent(name: str) -> Agent:
    """Get an agent by name."""
    agent_info = AGENT_REGISTRY.get(name)
    return agent_info.agent if agent_info else None

def get_agent_output(name: str) -> BaseModel | None:
    """Get the output of an agent by name."""
    agent_info = AGENT_REGISTRY.get(name)
    if agent_info:
        return agent_info.output
    return None
