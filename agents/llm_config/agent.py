"""
File: agents/llm_config/agent.py (relative to Chatbot_Agent)
"""
from crewai import LLM
import os
import random
import logging
from typing import List, Optional
import time
from functools import wraps
from .config import API_KEYS, API_KEY_SETTINGS, LLM_CONFIG, RATE_LIMIT_PATTERNS

OUTPUT_DIR = "./ai-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import logging utility
try:
    from .utils import log_api_usage
except ImportError:
    # Create a simple fallback if utils import fails
    def log_api_usage(key_index: int, status: str, error: str = None):
        logger.info(f"API Key #{key_index + 1}: {status}" + (f" - {error}" if error else ""))

class APIKeyManager:
    """Manages multiple API keys with automatic rotation on rate limits"""
    
    def __init__(self, api_keys: List[str], cooldown_duration: int = 300):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.failed_keys = set()
        self.key_cooldown = {}  # Track cooldown times for failed keys
        self.cooldown_duration = cooldown_duration
        
    def get_current_key(self) -> str:
        """Get the current API key, skipping failed ones"""
        self._cleanup_cooldowns()
        
        # Try to find a working key
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_key_index]
            if key not in self.failed_keys:
                return key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        # If all keys are failed, use the current one anyway (maybe cooldown expired)
        return self.api_keys[self.current_key_index]
    
    def mark_key_as_failed(self, key: str):
        """Mark a key as failed and set cooldown"""
        self.failed_keys.add(key)
        self.key_cooldown[key] = time.time()
        logger.warning(f"API key ending with ...{key[-4:]} marked as failed. Switching to next key.")
        log_api_usage(self.current_key_index, "failed", f"Rate limit exceeded for key ...{key[-4:]}")
        self.rotate_key()
    
    def rotate_key(self):
        """Rotate to the next API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to API key #{self.current_key_index + 1}")
    
    def _cleanup_cooldowns(self):
        """Remove keys from failed list if cooldown period has passed"""
        current_time = time.time()
        keys_to_remove = []
        
        for key in self.failed_keys:
            if current_time - self.key_cooldown.get(key, 0) > self.cooldown_duration:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.failed_keys.remove(key)
            if key in self.key_cooldown:
                del self.key_cooldown[key]
            logger.info(f"API key ending with ...{key[-4:]} restored after cooldown")

class RobustLLM:
    """Wrapper around CrewAI LLM with automatic API key rotation"""
    
    def __init__(self, api_keys: List[str], **llm_config):
        self.api_manager = APIKeyManager(api_keys, API_KEY_SETTINGS["cooldown_duration"])
        self.llm_config = llm_config
        self._current_llm = None
        self._create_llm()
    
    def _create_llm(self):
        """Create a new LLM instance with current API key"""
        current_key = self.api_manager.get_current_key()
        self._current_llm = LLM(
            api_key=current_key,
            **self.llm_config
        )
    
    def _is_rate_limit_error(self, error) -> bool:
        """Check if the error is related to rate limiting or quota exceeded"""
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in RATE_LIMIT_PATTERNS)
    
    def _handle_api_error(self, error):
        """Handle API errors and rotate key if needed"""
        if self._is_rate_limit_error(error):
            current_key = self.api_manager.get_current_key()
            self.api_manager.mark_key_as_failed(current_key)
            self._create_llm()  # Create new LLM with rotated key
            return True
        return False
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying LLM with error handling"""
        # For method calls, wrap with error handling
        if hasattr(self._current_llm, name) and callable(getattr(self._current_llm, name)):
            def wrapper(*args, **kwargs):
                max_retries = len(self.api_manager.api_keys)
                
                for attempt in range(max_retries):
                    try:
                        method = getattr(self._current_llm, name)
                        result = method(*args, **kwargs)
                        # Log successful usage
                        log_api_usage(self.api_manager.current_key_index, "success")
                        return result
                    except Exception as e:
                        logger.error(f"Error with API key #{self.api_manager.current_key_index + 1}: {e}")
                        
                        if self._handle_api_error(e):
                            logger.info(f"Retrying with API key #{self.api_manager.current_key_index + 1} (attempt {attempt + 1}/{max_retries})")
                            continue
                        else:
                            # Log error for non-rate-limit errors
                            log_api_usage(self.api_manager.current_key_index, "error", str(e))
                            # If it's not a rate limit error, re-raise immediately
                            raise e
                
                # If all retries failed, raise the last error
                log_api_usage(self.api_manager.current_key_index, "error", f"All API keys exhausted: {e}")
                raise Exception(f"All API keys exhausted. Last error: {e}")
            
            return wrapper
        else:
            # For properties/attributes, return directly
            return getattr(self._current_llm, name)

# Create the robust LLM instance
basic_llm = RobustLLM(
    api_keys=API_KEYS,
    output_dir=OUTPUT_DIR,
    **LLM_CONFIG
)