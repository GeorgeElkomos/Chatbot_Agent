"""
File: agents/__init__.py (relative to Chatbot_Agent)
"""

# Agents package
from .manager import ManagerDecision, create_manager_task, manager_agent
from .page_navigator import NavigationResponse, page_navigator_agent
from .general_qa import QAResponse, general_qa_agent
from .sql_builder import DatabaseResponse, sql_builder_agent
from .fusion_Analytics import Fusion_Analytics_Agent, FusionAnalyticsResponse
from .absence_analytics import Absence_Analytics_Agent, AbsenceResponse
from .registry import get_agent, get_agent_output, register
