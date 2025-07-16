from agents import (
    page_navigator_agent, NavigationResponse,
    sql_builder_agent, DatabaseResponse,
    general_qa_agent, QAResponse,
    manager_agent, ManagerDecision,
    register
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
        )
    )
    register(
        sql_builder_agent,
        DatabaseResponse,
        "SQLBuilderAgent",
        (
            "Constructs and executes complex SQL queries with proper JOINs. Specializes in database operations, order calculations, and data analysis. Always loads schema first and returns actual query results."
            "- Always instruct them to 'Load database schema, construct the appropriate SQL query with proper JOINs if needed, execute it, and return the actual results'\n"
            "- For order total calculations: Specifically mention 'Calculate using JOIN across Orders, OrderItems, and Products tables'\n"
            "- Never assign just 'build a query' - always require execution and results\n\n"
            "Final output must be a valid JSON object: {'User_Frendly_response': '<user-friendly description>', 'HTML_TABLE_DATA': '<table data IN HTML FORMAT or empty string>'}."
        )
    )
    register(
        general_qa_agent,
        QAResponse,
        "GeneralQAAgent",
        "Summarizes technical outputs and database results in user-friendly language. Use for explaining complex data or providing final summaries to users."
    )
    register(
        manager_agent,
        ManagerDecision,
        "ManagerAgent",
        "Orchestrates the conversation flow and decides which agent should handle each request based on user input and conversation context."
    )
