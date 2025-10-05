"""
File: agents/fusion_Analytics/models/schemas.py (relative to Chatbot_Agent)
Output schema for Fusion Analytics Agent
"""

from pydantic import BaseModel, Field


class FusionAnalyticsResponse(BaseModel):
    """
    Structured response for Fusion Analytics queries
    """

    query_executed: str = Field(
        description="The actual SQL query that was executed against the expense_report_data table"
    )
    User_Frendly_response: str = Field(
        description="User-friendly explanation of the analytics results, insights, and recommendations in plain English"
    )
    HTML_TABLE_DATA: str = Field(
        description="Query results formatted as HTML table for display, or empty string if no tabular data"
    )
