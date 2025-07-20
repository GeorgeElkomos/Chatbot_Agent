"""
Configuration file for API keys and settings
"""

# API Keys Configuration
API_KEYS = [
    "AIzaSyCKDCXGcICdprCVkDnhaTPsq40vwRJ16RI",
    "AIzaSyDjb_bXvII_KxgJiJah8L9g9bOYY5SbscY", 
    "AIzaSyDxohgaPOsVNPwA4mRmJuLvR4cuED574Ro",
    "AIzaSyD24gLGwO02yB1UdbdB9iFeCCqbVmZyczs",
    "AIzaSyBjXNpbdonVetkUb_-w9lF000pU-SU0O04",
    "AIzaSyC_KnVBkeBIMbokzGOn_OeglItJo9B8CuI",
    "AIzaSyDlY_PpNNWm7IHEfjJ3A0N6SCiSRxrne44"
]

# API Key Rotation Settings
API_KEY_SETTINGS = {
    "cooldown_duration": 300,  # 5 minutes in seconds
    "max_retries": 3,  # Maximum retries before giving up
    "retry_delay": 2,  # Delay between retries in seconds
}

# LLM Configuration
LLM_CONFIG = {
    "name": "BasicLLM",
    "model": "gemini/gemini-2.0-flash",
    "max_tokens": 8192,
    "temperature": 0.1,
    "top_p": 0.9,
}

# Rate limit error patterns to detect
RATE_LIMIT_PATTERNS = [
    'rate limit',
    'quota exceeded',
    'too many requests',
    'limit exceeded',
    'rate exceeded',
    'throttled',
    'resource exhausted',
    'requests per minute',
    'daily limit',
    'per minute limit',
    'per day limit'
]
