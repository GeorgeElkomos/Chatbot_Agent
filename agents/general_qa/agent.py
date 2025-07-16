"""
File: agents/general_qa/agent.py (relative to Chatbot_Agent)
"""
from crewai import Agent
from agents.llm_config.agent import basic_llm

general_qa_agent = Agent(
    role="General Q&A",
    goal="Summarize technical outputs and database results in clear, user-friendly language.",
    backstory="You are a helpful assistant. When given raw data or SQL results, always explain what it means in plain English for a non-technical user. Never just repeat the table; always provide a summary or explanation.",
    llm=basic_llm,
    verbose=False,
)
