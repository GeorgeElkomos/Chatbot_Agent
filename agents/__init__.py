"""
File: agents/__init__.py (relative to Chatbot_Agent)

✅ ENHANCED: Removed deprecated sql_builder import
"""

# Agents package
from .manager import ManagerDecision, create_manager_task, manager_agent
from .page_navigator import NavigationResponse, page_navigator_agent
from .general_qa import QAResponse, general_qa_agent
# sql_builder DEPRECATED - moved to agents/_deprecated/
# Use specialized analytics agents instead: FusionAnalyticsAgent, AbsenceAnalyticsAgent, OrgChartAgent
from .fusion_Analytics import Fusion_Analytics_Agent, FusionAnalyticsResponse
from .absence_analytics import Absence_Analytics_Agent, AbsenceResponse
from .org_Chart import org_chart_agent, OrgChartResponse
from .registry import get_agent, get_agent_output, register

