# API Key Rotation System

This system automatically manages multiple Google Gemini API keys to prevent rate limiting issues and ensure uninterrupted service for your chatbot.

## How It Works

### 1. Automatic Key Rotation
- The system starts with the first API key
- When a rate limit or quota exceeded error occurs, it automatically switches to the next available key
- Failed keys are temporarily blacklisted with a cooldown period (default: 5 minutes)

### 2. Error Detection
The system detects various rate limit patterns:
- `rate limit`
- `quota exceeded`
- `too many requests`
- `limit exceeded`
- `throttled`
- `resource exhausted`
- And more...

### 3. Key Management
- **Cooldown System**: Failed keys are put on cooldown for 5 minutes before being retried
- **Rotation Logic**: Automatically cycles through available keys
- **Logging**: All usage and errors are logged for monitoring

## Configuration

### API Keys
Edit `agents/llm_config/config.py` to add or remove API keys:
```python
API_KEYS = [
    "your-api-key-1",
    "your-api-key-2",
    # ... more keys
]
```

### Settings
Customize rotation behavior:
```python
API_KEY_SETTINGS = {
    "cooldown_duration": 300,  # 5 minutes in seconds
    "max_retries": 3,
    "retry_delay": 2,
}
```

## Usage

The system is transparent to your existing code. Simply import and use `basic_llm` as before:

```python
from agents.llm_config.agent import basic_llm

# Use normally - rotation happens automatically
response = basic_llm.generate("Your prompt here")
```

## Monitoring

### API Usage Endpoints
- `GET /api/usage` - Get usage statistics
- `POST /api/usage/reset` - Reset usage statistics

### Usage Statistics
The system tracks:
- Total requests
- Success rate
- Error count
- Recent errors

### Log Files
- API usage is logged to `./ai-output/api_usage.json`
- Console logs show key rotation events

## Testing

Run the test script to verify the rotation system:
```bash
python test_api_rotation.py
```

## Features

1. **Seamless Integration**: Works with existing CrewAI LLM code
2. **Automatic Failover**: Switches keys immediately on rate limit errors
3. **Smart Cooldown**: Temporarily blacklists failed keys
4. **Comprehensive Logging**: Tracks all usage and errors
5. **Configurable**: Easy to customize behavior
6. **Monitoring**: Built-in usage statistics and endpoints

## Benefits

- **Uninterrupted Service**: No more rate limit errors affecting users
- **Better Resource Utilization**: Spreads load across multiple keys
- **Easy Maintenance**: Simple configuration and monitoring
- **Scalable**: Easy to add more API keys as needed

## Error Handling

The system handles various scenarios:
- **Rate Limits**: Automatic key rotation
- **Quota Exceeded**: Key blacklisting with cooldown
- **Network Errors**: Retries with same key
- **API Changes**: Graceful degradation

## Best Practices

1. **Monitor Usage**: Check `/api/usage` endpoint regularly
2. **Rotate Keys**: Periodically update API keys for security
3. **Log Monitoring**: Watch console logs for rotation events
4. **Key Distribution**: Spread usage across multiple Google accounts if possible
5. **Backup Keys**: Keep spare keys for emergency use
