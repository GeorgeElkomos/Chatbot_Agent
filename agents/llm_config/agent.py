"""
File: agents/llm_config/agent.py (relative to Chatbot_Agent)
"""

from crewai import LLM, BaseLLM
import os

OUTPUT_DIR = "./ai-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

basic_llm = LLM(
    name="BasicLLM",
    model="gemini/gemini-2.0-flash",
    api_key="AIzaSyB33PBwcjDf47uXtFwy2Szvz607TJSEkZY",  # 1st "AIzaSyCKDCXGcICdprCVkDnhaTPsq40vwRJ16RI", 2nd "AIzaSyDjb_bXvII_KxgJiJah8L9g9bOYY5SbscY", "AIzaSyB33PBwcjDf47uXtFwy2Szvz607TJSEkZY"
    output_dir=OUTPUT_DIR,
    max_tokens=8192,
    temperature=0.1,
    top_p=0.9,
)


# from .ollama_llm import OllamaLLM
# basic_llm = OllamaLLM(model="deepseek-r1:1.5b", temperature=0.1)
