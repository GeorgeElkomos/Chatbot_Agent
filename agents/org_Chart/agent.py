"""
Org Chart Agent - Manages employee hierarchy data from Oracle Fusion
"""

from crewai import Agent
from agents.llm_config.agent import basic_llm
from .tools import execute_org_chart_query


org_chart_agent = Agent(
    role="Employee Hierarchy Data Analyst",
    goal="""Query and analyze employee organizational hierarchy data.
    Provide insights about reporting relationships, managers, and department structures.""",
    
    backstory="""You are an expert in organizational structure and employee hierarchy analysis.
    You can query the employee hierarchy database to answer questions about manager-employee relationships,
    team sizes, department structures, and organizational charts.
    The database is automatically kept up-to-date with the latest data from Oracle Fusion.""",
    
    verbose=True,
    allow_delegation=False,
    llm=basic_llm,
    tools=[
        execute_org_chart_query
    ]
)
