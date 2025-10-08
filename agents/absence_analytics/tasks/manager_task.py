"""
Task definitions for Absence Analytics Agent
"""

def get_absence_analysis_task(agent, query: str):
    """
    Create a task for analyzing absence/leave data
    
    Args:
        agent: The Absence_Analytics_Agent instance
        query: The user's query about absence data
    
    Returns:
        Task object configured for absence analysis
    """
    from crewai import Task
    
    return Task(
        description=f"""
        Analyze absence and leave data based on the following query:
        
        Query: {query}
        
        Steps:
        1. Parse the query to understand what information is needed
        2. Construct appropriate SQL query for absence_report_data table
        3. Execute the query using execute_absence_query tool
        4. Analyze the results and provide insights
        5. Format the response in a clear, professional manner
        
        Return a comprehensive analysis with:
        - Direct answer to the question
        - Key statistics and metrics
        - Any notable patterns or insights
        - Recommendations if applicable
        """,
        agent=agent,
        expected_output="""
        A detailed absence analytics report containing:
        - Clear answer to the user's question
        - Relevant statistics (employee counts, leave balances, etc.)
        - Data presented in organized format (tables/lists)
        - Insights and recommendations based on the data
        """
    )
