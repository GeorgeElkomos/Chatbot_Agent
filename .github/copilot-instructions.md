# Chatbot Agent - AI Assistant Instructions

## Architecture Overview

This is a **multi-agent orchestration system** built with CrewAI, managing a chatbot that handles navigation, database queries, and Q&A for a budget transfer web application (Tanfeez App).

### Core Components

1. **Orchestrator** (`orchestrator.py`): Central control loop implementing convergence detection and agent routing
2. **Manager Agent**: Routes user requests to specialized worker agents based on intent
3. **Worker Agents** (registered in `agents/registry/registration.py`):
   - `PageNavigatorAgent`: Returns navigation links and page info
   - `SQLBuilderAgent`: Constructs/executes SQL queries with JOINs
   - `GeneralQAAgent`: Translates technical outputs to user-friendly language
4. **FastAPI Server** (`main.py`): Exposes `/chatbot/public` endpoint for chat interactions

### Data Flow Pattern

```
User Request → orchestrate() → ManagerAgent (decides) → Worker Agent (executes) → ManagerAgent (evaluates) → [loop or stop]
```

- **Convergence detection**: If same output repeats 2+ times, trigger GeneralQA summary and stop
- **History tracking**: All agent outputs saved to `ai-output/history.json` and `responses.json`
- **Output filtering**: `filter_output()` extracts only relevant fields per agent type

## Agent Registration System

**Critical Pattern**: All agents MUST be registered in `agents/registry/registration.py` with:

```python
register(agent_instance, OutputModel, "AgentName", "Description for manager")
```

- `OutputModel`: Pydantic schema in `agents/{agent}/models/schemas.py` (e.g., `DatabaseResponse`, `NavigationResponse`)
- Manager uses descriptions to decide routing
- Agents accessed via `get_agent("AgentName")` from registry

## LLM Configuration

**Default**: Gemini 2.0 Flash via `agents/llm_config/agent.py` (`basic_llm`)

- API key rotation managed in `agents/llm_config/config.py` (7 keys with 5min cooldown)
- **Alternative**: Ollama support exists (`agents/llm_config/ollama_llm.py`) but commented out
- Rate limit handling built into key rotation system

## Database Patterns

### Schema Loading

All SQL agents MUST call `Update_query_project_database()` tool FIRST to load schema from `System-Info/Database Tables.json`

### JOIN Query Template (Orders System)

```sql
SELECT SUM(p.price * oi.quantity) AS total_amount
FROM Orders o
JOIN OrderItems oi ON o.order_id = oi.order_id
JOIN Products p ON oi.product_id = p.product_id
WHERE o.order_date = 'YYYY-MM-DD HH:MM:SS'
```

Key relationships: `Orders.order_id → OrderItems.order_id`, `OrderItems.product_id → Products.product_id`

### Database Updater

`agents/fusion_Analytics/smart_db_updater.py` implements cooldown-based refresh (5s default) to prevent redundant updates. Initialized in orchestrator startup.

## Tool Creation Convention

Tools live in `agents/{agent}/tools/` and use `@tool` decorator from crewai:

```python
from crewai.tools import tool

@tool
def tool_name(param: str) -> str:
    """Clear description for LLM."""
    # Implementation
    return result
```

Tools are assigned to agents via `tools=[...]` parameter in Agent constructor.

## Output Schemas

All worker agents return **strictly typed Pydantic models**:

- `NavigationResponse`: `{navigation_link: str, response: str}`
- `DatabaseResponse`: `{User_Frendly_response: str, HTML_TABLE_DATA: str}`
- `QAResponse`: `{response: str}`
- `ManagerDecision`: `{next_agent: str, next_task_description: str, stop: bool}`

Task descriptions include schema JSON to enforce structure.

## Running the System

### Development Mode (Direct Test)

```powershell
python main.py  # Runs test query: "Navigate me to Dashboard."
```

### Server Mode

```powershell
python main.py --server  # Starts FastAPI on 0.0.0.0:8080
```

### Testing Specific Queries

Edit `main.py` line 68: `_user_request = "Your test query here"`

## Key Files Reference

- **System Info**: `System-Info/` contains database schemas, page definitions, API functions as JSON
- **Conversation History**: `ai-output/history.json` logs all agent interactions
- **Examples Cache**: `examples.py` stores pre-computed responses for common queries (currently disabled in orchestrator)
- **Utils**: `utils.py` handles logging suppression, output saving, and response filtering

## Common Patterns

### Adding a New Agent

1. Create `agents/new_agent/agent.py` with Agent definition
2. Define Pydantic output in `agents/new_agent/models/schemas.py`
3. Register in `agents/registry/registration.py` with clear description
4. Export from `agents/__init__.py`

### Debugging Agent Behavior

- Set `logs=True` in `orchestrate()` for verbose CrewAI output
- Check `ai-output/history.json` for agent decision chain
- Review `ollama.log` if using Ollama (logs reasoning traces)

### Conversation History

Orchestrator trims history to last 6 messages (3 user+assistant pairs) via `trim_history()` to manage context size. Full history passed to manager for decision-making.
