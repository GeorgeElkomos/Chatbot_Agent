"""
File: agents/llm_config/utils.py (relative to Chatbot_Agent)
Utility functions for API key management and monitoring
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

USAGE_LOG_FILE = "./ai-output/api_usage.json"

def log_api_usage(key_index: int, status: str, error: str = None):
    """Log API key usage for monitoring"""
    usage_data = {
        "timestamp": datetime.now().isoformat(),
        "key_index": key_index,
        "status": status,
        "error": error
    }
    
    # Read existing logs
    logs = []
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs = []
    
    logs.append(usage_data)
    
    # Keep only last 1000 entries
    logs = logs[-1000:]
    
    # Write back to file
    os.makedirs(os.path.dirname(USAGE_LOG_FILE), exist_ok=True)
    with open(USAGE_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def get_api_usage_stats() -> Dict[str, Any]:
    """Get statistics about API key usage"""
    if not os.path.exists(USAGE_LOG_FILE):
        return {"total_requests": 0, "errors": 0, "success_rate": 0}
    
    try:
        with open(USAGE_LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        total_requests = len(logs)
        errors = sum(1 for log in logs if log["status"] == "error")
        success_rate = ((total_requests - errors) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "errors": errors,
            "success_rate": round(success_rate, 2),
            "latest_errors": [log for log in logs if log["status"] == "error"][-5:]  # Last 5 errors
        }
    except (json.JSONDecodeError, FileNotFoundError):
        return {"total_requests": 0, "errors": 0, "success_rate": 0}

def reset_api_usage_stats():
    """Reset API usage statistics"""
    if os.path.exists(USAGE_LOG_FILE):
        os.remove(USAGE_LOG_FILE)
