"""
File: agents/registry/registration.py (relative to Chatbot_Agent)

✅ ENHANCED: SQLBuilder agent deprecated and removed from imports
"""

from agents import (
    page_navigator_agent,
    NavigationResponse,
    # sql_builder_agent, DatabaseResponse - DEPRECATED, moved to _deprecated/
    general_qa_agent,
    QAResponse,
    manager_agent,
    ManagerDecision,
    Fusion_Analytics_Agent,
    FusionAnalyticsResponse,
    Absence_Analytics_Agent,
    AbsenceResponse,
    org_chart_agent,
    OrgChartResponse,
    register,
)


def register_agents():
    register(
        page_navigator_agent,
        NavigationResponse,
        "PageNavigatorAgent",
        (
            "Handles navigation requests and provides appropriate page links and user-friendly information. "
            "Use when user wants to move to different pages or sections of the application, or requests a summary of available pages. "
            "Final output must be a valid JSON object: {'navigation_link': '<link or empty string>', 'response': '<user-friendly description>'}. "
            "The { navigation_link } field should be the navigation link (e.g., '/', '/register', '/admin/user-management') or an empty string if no navigation is needed. "
            "The { response } field should contain instructions, a summary, or user-friendly information about the link or requested pages."
        ),
    )
    # register(
    #     sql_builder_agent,
    #     DatabaseResponse,
    #     "SQLBuilderAgent",
    #     (
    #         "Constructs and executes complex SQL queries with proper JOINs. Specializes in database operations, order calculations, and data analysis. Always loads schema first and returns actual query results."
    #         "- Always instruct them to 'Load database schema, construct the appropriate SQL query with proper JOINs if needed, execute it, and return the actual results'\n"
    #         "- For order total calculations: Specifically mention 'Calculate using JOIN across Orders, OrderItems, and Products tables'\n"
    #         "- Never assign just 'build a query' - always require execution and results\n\n"
    #         "Final output must be a valid JSON object: {'User_Frendly_response': '<user-friendly description>', 'HTML_TABLE_DATA': '<table data IN HTML FORMAT or empty string>'}."
    #     ),
    # )
    register(
        general_qa_agent,
        QAResponse,
        "GeneralQAAgent",
        "Summarizes technical outputs and database results in user-friendly language. Use for explaining complex data or providing final summaries to users.",
    )
    register(
        Fusion_Analytics_Agent,
        FusionAnalyticsResponse,
        "FusionAnalyticsAgent",
        (
            "Analyzes Oracle Fusion expense report data from the expense_report_data table. Specializes in: "
            "- Employee spending patterns and profiles "
            "- Policy violation detection and analysis (DAILY_LIMIT, MONTHLY_LIMIT, INDIVIDUAL_LIMIT, RECEIPT_MISSING) "
            "- Audit compliance tracking and risk assessment "
            "- Merchant spending analysis and preferences "
            "- Financial trends and spending patterns over time "
            "- Receipt compliance and amount verification "
            "- Multi-currency expense analysis "
            "- Expense category breakdowns (Travel, Education, Food, etc.) "
            "Use for questions about: expense reports, spending analytics, violation patterns, audit flags, "
            "employee expense behavior, merchant relationships, or any financial analysis from expense data. "
            "Always executes actual SQL queries and returns real data with insights. "
            "Final output: {'query_executed': '<SQL query>', 'User_Frendly_response': '<insights>', 'HTML_TABLE_DATA': '<table>'}"
        ),
    )
    register(
        Absence_Analytics_Agent,
        AbsenceResponse,
        "AbsenceAnalyticsAgent",
        (
            "HCM for Analyzes Oracle Fusion employee absence and leave data from the absence_report_data table. Specializes in: "
            "- Employee leave balance tracking and analysis "
            "- Leave plan utilization patterns (Annual Leave, Day in Lieu, etc.) "
            "- Workforce availability and leave trends "
            "- Department-level leave analysis "
            "- High balance employees (potential leave liability) "
            "- Zero balance employees (leave exhaustion monitoring) "
            "- Leave accrual period tracking "
            "- Business unit leave distribution "
            "- Grade/job level leave patterns "
            "Use for questions about: leave balances, absence patterns, leave plans, workforce availability, "
            "employee time-off analysis, department leave trends, or any HR analytics related to employee absence. "
            "Always executes actual SQL queries and returns real data with insights. "
            "Final output: {'User_Friendly_response': '<insights>', 'HTML_TABLE_DATA': '<table>'}"
        ),
    )
    register(
        org_chart_agent,
        OrgChartResponse,
        "OrgChartAgent",
        (
            "Analyzes employee organizational hierarchy from the employee_hierarchy table. Specializes in: "
            "- Manager-employee relationships and reporting lines "
            "- Team structures and composition "
            "- Department organization and headcount "
            "- Organizational hierarchy and reporting chains "
            "- Manager span of control analysis "
            "- Employee lookup by name or person number "
            "- Direct reports and indirect reports mapping "
            "- Cross-department organizational analysis "
            "Use for questions about: who reports to whom, team sizes, manager assignments, department structures, "
            "organizational hierarchy, reporting relationships, org charts, team composition, or any queries about "
            "the organizational structure and employee-manager relationships. "
            "Always executes actual SQL queries with smart auto-updates from Oracle Fusion. "
            "Final output: {'response': '<insights>', 'statistics': {'total_employees': N, 'unique_managers': M, 'unique_departments': D}}"
        ),
    )
    register(
        manager_agent,
        ManagerDecision,
        "ManagerAgent",
        "Orchestrates the conversation flow and decides which agent should handle each request based on user input and conversation context.",
    )
