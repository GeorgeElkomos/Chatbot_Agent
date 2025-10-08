"""
File: iteration_tracker.py
Custom iteration tracker for CrewAI agents to capture detailed execution traces
"""

import json
import time
from typing import List, Dict, Any, Optional
from threading import Lock


class IterationTracker:
    """Tracks detailed iteration-level execution for agents"""

    def __init__(self):
        self.agent_tracks: Dict[str, List[Dict[str, Any]]] = {}
        self.current_agent: Optional[str] = None
        self.current_iteration: int = 0
        self.current_iteration_data: Dict[str, Any] = {}
        self.last_saved_iteration: Optional[Dict[str, Any]] = (
            None  # Keep reference to last iteration
        )
        self.lock = Lock()

    def start_agent_execution(self, agent_name: str):
        """Initialize tracking for a new agent execution"""
        with self.lock:
            self.current_agent = agent_name
            self.current_iteration = 0
            self.last_saved_iteration = None  # Reset for new agent
            if agent_name not in self.agent_tracks:
                self.agent_tracks[agent_name] = []
            else:
                # Clear previous tracking for this agent
                self.agent_tracks[agent_name] = []

    def start_iteration(self):
        """Start tracking a new iteration"""
        with self.lock:
            if self.current_agent is None:
                return

            self.current_iteration += 1
            self.current_iteration_data = {
                "iteration_number": self.current_iteration,
                "timestamp": time.time(),
                "llm_input_message": None,
                "llm_output": None,
                "tool_called": None,
                "tool_args": None,
                "tool_output": None,
                "error": None,
                "trace": [],
            }

    def log_llm_input(self, messages: Any):
        """Log the input sent to the LLM"""
        with self.lock:
            if not self.current_iteration_data:
                return

            # Convert messages to readable format
            if isinstance(messages, str):
                self.current_iteration_data["llm_input_message"] = messages
            elif isinstance(messages, list):
                # Format message list nicely
                formatted_msgs = []
                for msg in messages:
                    if isinstance(msg, dict):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        formatted_msgs.append(f"[{role}]: {content}")
                    else:
                        formatted_msgs.append(str(msg))
                self.current_iteration_data["llm_input_message"] = "\n".join(
                    formatted_msgs
                )
            else:
                self.current_iteration_data["llm_input_message"] = str(messages)

            self.current_iteration_data["trace"].append(
                {
                    "step": "llm_input",
                    "timestamp": time.time(),
                    "content": self.current_iteration_data["llm_input_message"][
                        :500
                    ],  # Truncate for trace
                }
            )

    def log_llm_output(self, output: str):
        """Log the output from the LLM"""
        with self.lock:
            if not self.current_iteration_data:
                return

            self.current_iteration_data["llm_output"] = output
            self.current_iteration_data["trace"].append(
                {
                    "step": "llm_output",
                    "timestamp": time.time(),
                    "content": output[:500],  # Truncate for trace
                }
            )

    def log_tool_call(self, tool_name: str, tool_args: Dict[str, Any]):
        """Log a tool being called - works even without active iteration"""
        with self.lock:
            # If no active iteration but we have a saved one, update it
            if not self.current_iteration_data and self.last_saved_iteration:
                # This tool belongs to the previous iteration that just ended
                self.last_saved_iteration["tool_called"] = tool_name
                self.last_saved_iteration["tool_args"] = tool_args
                self.last_saved_iteration["tool_execution_timing"] = (
                    "after_iteration_end"
                )
                if "trace" not in self.last_saved_iteration:
                    self.last_saved_iteration["trace"] = []
                self.last_saved_iteration["trace"].append(
                    {
                        "step": "tool_call",
                        "timestamp": time.time(),
                        "tool": tool_name,
                        "args": tool_args,
                        "note": "Executed after LLM iteration ended",
                    }
                )
                # Print for debugging
                print(f"  🔧 [TOOL TRACKED] {tool_name} (post-iteration)")
                return

            # Normal case: active iteration exists
            if self.current_iteration_data:
                self.current_iteration_data["tool_called"] = tool_name
                self.current_iteration_data["tool_args"] = tool_args
                self.current_iteration_data["trace"].append(
                    {
                        "step": "tool_call",
                        "timestamp": time.time(),
                        "tool": tool_name,
                        "args": tool_args,
                    }
                )
                # Print for debugging
                print(f"  🔧 [TOOL TRACKED] {tool_name} (during iteration)")

    def log_tool_output(self, output: Any):
        """Log the output from a tool - works even without active iteration"""
        with self.lock:
            # Truncate large outputs
            output_str = str(output)
            if len(output_str) > 1000:
                output_str = output_str[:1000] + "... [truncated]"

            # If no active iteration but we have a saved one, update it
            if not self.current_iteration_data and self.last_saved_iteration:
                # This tool output belongs to the previous iteration
                self.last_saved_iteration["tool_output"] = output_str
                print(f"  ✅ [TOOL OUTPUT TRACKED] (post-iteration - {len(output_str)} chars)")
                if "trace" not in self.last_saved_iteration:
                    self.last_saved_iteration["trace"] = []
                self.last_saved_iteration["trace"].append(
                    {
                        "step": "tool_output",
                        "timestamp": time.time(),
                        "content": output_str[:500],
                        "note": "Received after LLM iteration ended",
                    }
                )
                return
                
            # Normal case: active iteration exists
            if self.current_iteration_data:
                self.current_iteration_data["tool_output"] = output_str
                self.current_iteration_data["trace"].append(
                    {
                        "step": "tool_output",
                        "timestamp": time.time(),
                        "content": output_str[:500],  # Truncate for trace
                    }
                )
                print(f"  ✅ [TOOL OUTPUT TRACKED] (during iteration - {len(output_str)} chars)")

    def log_error(self, error: str):
        """Log an error that occurred"""
        with self.lock:
            if not self.current_iteration_data:
                return

            self.current_iteration_data["error"] = error
            self.current_iteration_data["trace"].append(
                {"step": "error", "timestamp": time.time(), "error": error}
            )

    def end_iteration(self):
        """Finalize the current iteration and save it"""
        with self.lock:
            if self.current_agent is None or not self.current_iteration_data:
                return

            # Add duration
            if self.current_iteration_data.get("timestamp"):
                self.current_iteration_data["duration_seconds"] = round(
                    time.time() - self.current_iteration_data["timestamp"], 3
                )

            # Save to agent's track list (max 5 iterations per agent as per max_iter)
            if len(self.agent_tracks[self.current_agent]) < 5:
                self.agent_tracks[self.current_agent].append(
                    self.current_iteration_data.copy()
                )

                # Keep reference to this iteration so tools can update it later
                self.last_saved_iteration = self.agent_tracks[self.current_agent][-1]

            # Clear current iteration data
            self.current_iteration_data = {}

    def end_agent_execution(self) -> List[Dict[str, Any]]:
        """End tracking for current agent and return the full track"""
        with self.lock:
            if self.current_agent is None:
                return []

            # If there's an active iteration, end it first
            if self.current_iteration_data:
                self.end_iteration()

            track = self.agent_tracks.get(self.current_agent, [])

            # Reset current agent
            self.current_agent = None
            self.current_iteration = 0

            return track

    def get_agent_track(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get the track for a specific agent"""
        with self.lock:
            return self.agent_tracks.get(agent_name, [])

    def clear_all(self):
        """Clear all tracking data"""
        with self.lock:
            self.agent_tracks.clear()
            self.current_agent = None
            self.current_iteration = 0
            self.current_iteration_data = {}


# Global singleton tracker
_global_tracker = IterationTracker()


def get_tracker() -> IterationTracker:
    """Get the global iteration tracker instance"""
    return _global_tracker
