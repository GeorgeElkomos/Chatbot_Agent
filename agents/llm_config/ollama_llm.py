# File: agents/llm_config/ollama_llm.py

import json
from typing import Any, Dict, List, Optional, Union

from crewai.llms.base_llm import BaseLLM
from crewai.utilities.events.llm_events import (
    LLMCallStartedEvent,
    LLMCallCompletedEvent,
    LLMCallFailedEvent,
    LLMCallType,
)
from crewai.utilities.events.tool_usage_events import (
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageErrorEvent,
)
from crewai.utilities.events import crewai_event_bus
from ollama import chat


def chat_ollama(model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    f = open("ollama.log", "a")
    f.write(f"Calling model {model} with messages: {messages}\n")
    f.close()
    responce = chat(model=model, messages=messages)
    content = responce["message"]["content"]
    result = content[content.index("</think>")+9:]
    f = open("ollama.log", "a")
    f.write(f"Model response: {result}\n")
    f.close()
    return result
class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "deepseek-r1:1.5b", temperature: Optional[float] = None):
        super().__init__(model=model, temperature=temperature)
        self.stream = False  # streaming unsupported for now
    def supports_function_calling(self) -> bool:
        return True
    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Any]:
        # 1) Emit start event
        crewai_event_bus.emit(self, LLMCallStartedEvent(
            messages=messages,
            tools=tools,
            callbacks=callbacks,
            available_functions=available_functions,
        ))

        # 2) Normalize messages
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        if tools:
            tool_specs = json.dumps(tools, indent=2)
            system_msg = {
                "role": "system",
                "content": (
                    "You have access to the following tools.  "
                    "Call a tool by returning JSON exactly of the form:\n"
                    "{\"tool\": <tool_name>, \"args\": {…}}\n\n"
                    f"{tool_specs}"
                )
            }
            messages = [system_msg] + messages
        # 3) Call the model
        try:
            content = chat_ollama(
                model=self.model,
                messages=messages,
                # temperature=self.temperature,
            )
        except Exception as e:
            crewai_event_bus.emit(self, LLMCallFailedEvent(error=str(e)))
            raise

        # 4) Check for a tool‐call candidate (we expect JSON like {"tool": "...", "args": { ... }})
        if available_functions and content.strip().startswith("{"):
            try:
                payload = json.loads(content)
                tool_name = payload.get("tool")
                tool_args = payload.get("args", {})
            except json.JSONDecodeError:
                payload = None
            else:
                if tool_name in available_functions:
                    # 4a) Emit tool started
                    crewai_event_bus.emit(self, ToolUsageStartedEvent(
                        tool_name=tool_name,
                        tool_args=tool_args,
                    ))
                    try:
                        result = available_functions[tool_name](**tool_args)
                        # 4b) Emit tool finished
                        crewai_event_bus.emit(self, ToolUsageFinishedEvent(
                            output=result,
                            tool_name=tool_name,
                            tool_args=tool_args,
                        ))
                    except Exception as tool_err:
                        crewai_event_bus.emit(self, ToolUsageErrorEvent(
                            tool_name=tool_name,
                            tool_args=tool_args,
                            error=str(tool_err),
                        ))
                        raise

                    # 4c) Hand back the tool result into a second chat turn
                    followup = messages + [
                        {"role": "assistant", "content": content},               # original suggestion
                        {"role": "tool",      "name": tool_name, "content": result},
                    ]
                    
                    content = chat_ollama(model=self.model, messages=followup)
                    

        # 5) Emit completion event
        crewai_event_bus.emit(self, LLMCallCompletedEvent(response=content, call_type=LLMCallType.LLM_CALL))
        # 5a) Fire any success callbacks so they record usage, etc.
        if callbacks:
            for cb in callbacks:
                if hasattr(cb, "log_success_event"):
                    # mimic LiteLLM’s callback signature
                    cb.log_success_event(
                        kwargs={
                            "model": self.model,
                            "messages": messages,
                            "temperature": self.temperature,
                        },
                        response_obj={"response": content},
                        start_time=0,
                        end_time=0,
                    )
        return content
