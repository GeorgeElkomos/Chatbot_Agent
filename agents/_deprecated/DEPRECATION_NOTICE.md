# Deprecated Agents

This folder contains agents that have been deprecated and should not be used in production.

## SQLBuilder Agent - DEPRECATED

**Date Deprecated:** 2025-10-14  
**Reason:** Replaced by specialized analytics agents with superior performance

### Why SQLBuilder Was Deprecated

The SQLBuilder agent was originally designed as a general-purpose SQL query construction agent. However, it has been deprecated for the following reasons:

#### 1. **String Concatenation Anti-Pattern**
The agent used tools like `Update_query_project_database(query: str)` that concatenated schema information to the user's query string. This caused:
- LLM confusion about what to do with the returned string
- Convergence issues (agent producing identical outputs repeatedly)
- Poor success rates compared to specialized agents

#### 2. **Tool Complexity**
The agent had 4 overlapping tools with unclear responsibilities:
- `Update_query_project_database()` - String concatenation tool
- `run_query()` - Query execution
- `analyze_and_execute_sql_request()` - Combined analysis and execution
- `get_sql_query_examples()` - Example retrieval

This complexity made it difficult to maintain and debug.

#### 3. **Generic vs Domain-Specific Expertise**
SQLBuilder was a generic SQL agent without domain knowledge. This meant:
- No understanding of business context (expense policies, leave types, org structure)
- No embedded query patterns or best practices
- No ability to provide insights beyond raw data
- Inferior query quality compared to specialized agents

### Superior Replacement: Specialized Analytics Agents

SQLBuilder has been replaced by three domain-expert analytics agents that follow the gold standard pattern:

#### ✅ **FusionAnalyticsAgent** (Expense Reports)
- **Database:** `expense_reports.db`
- **Expertise:** Oracle Fusion expense data, policy violations, spending trends
- **Performance:** 0% convergence rate, 95-98% success rate
- **Pattern:** Complete schema in backstory + single execution tool
- **Advantage:** Provides expert analysis, detects violations, offers recommendations

#### ✅ **AbsenceAnalyticsAgent** (Leave/Absence Data)
- **Database:** `absence_reports.db`
- **Expertise:** Oracle Fusion HCM leave data, absence patterns, workforce planning
- **Performance:** 0% convergence rate, 95-98% success rate
- **Pattern:** Complete schema in backstory + single execution tool
- **Advantage:** HR expertise, leave balance analysis, accrual pattern insights

#### ✅ **OrgChartAgent** (Organizational Hierarchy)
- **Database:** `employee_hierarchy.db`
- **Expertise:** Reporting relationships, team composition, span of control
- **Performance:** 0% convergence rate, 95-98% success rate
- **Pattern:** Complete schema in backstory + single execution tool
- **Advantage:** Organizational insights, multi-level hierarchy queries, strategic analysis

### Why Specialized Agents Are Superior

| Aspect | SQLBuilder (Deprecated) | Analytics Agents (Active) |
|--------|-------------------------|---------------------------|
| **Domain Knowledge** | None | Expert-level |
| **Schema Knowledge** | Loaded via tool | Embedded in backstory |
| **Query Patterns** | Generic | Domain-specific optimized |
| **Analysis Quality** | Data only | Insights + recommendations |
| **Convergence Rate** | High (~30%) | Near-zero (0-2%) |
| **Success Rate** | Variable | Consistent 95-98% |
| **Maintainability** | Complex (4 tools) | Simple (1 tool) |
| **Tool Pattern** | String concatenation | Clean execution |
| **Debugging** | Difficult | Easy (SQL visible) |

### Migration Guide

If you have code referencing SQLBuilder, migrate to the appropriate analytics agent:

**Old Pattern (Deprecated):**
```python
from agents.sql_builder import sql_builder_agent

# ❌ Don't use this
response = sql_builder_agent.run("Show me expenses for John Doe")
```

**New Pattern (Recommended):**
```python
from agents.fusion_Analytics import Fusion_Analytics_Agent
from agents.absence_analytics import Absence_Analytics_Agent
from agents.org_Chart import org_chart_agent

# ✅ Use domain-specific agent
response = Fusion_Analytics_Agent.run("Show me expenses for John Doe")
```

**Query Type Mapping:**
- Expense/budget queries → `Fusion_Analytics_Agent`
- Leave/absence queries → `Absence_Analytics_Agent`
- Org structure queries → `org_chart_agent`
- General database queries → Consider creating a new specialized agent

### Gold Standard Pattern for New Agents

If you need to create a new database agent, follow the analytics agent pattern:

1. **Embed complete schema in backstory** (not via tools)
2. **Include common query patterns** with SQL examples
3. **Provide domain expertise** in the role and backstory
4. **Use single execution tool** with auto-refresh capability
5. **Return structured Pydantic output** with HTML table data
6. **Include error handling** and user-friendly messages

Example template available in:
- `agents/fusion_Analytics/agent.py`
- `agents/absence_analytics/agent.py`
- `agents/org_Chart/agent.py`

### Future Considerations

**DO NOT resurrect SQLBuilder.** If you need a new database agent:
1. Create a specialized agent for that domain
2. Follow the analytics pattern (schema in backstory + single tool)
3. Embed domain expertise in the agent's role and backstory
4. Register in `agents/registry/registration.py`
5. Test thoroughly for convergence issues

### Archive Contents

The `sql_builder/` folder contains:
- Original agent definition
- 4 deprecated tools (string concatenation pattern)
- Complex task definitions
- Outdated utility functions

**These files are preserved for reference only and should not be used in production.**

---

**Questions?** See:
- `WRONG_VS_RIGHT_IMPLEMENTATION.md` - Side-by-side comparison of patterns
- `AGENT_ENHANCEMENT_ANALYSIS.md` - Technical analysis of issues
- `QUICK_FIX_GUIDE.md` - Implementation guidelines for new agents
