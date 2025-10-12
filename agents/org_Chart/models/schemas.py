"""
Org Chart Response Schema
"""

from pydantic import BaseModel, Field
from typing import Optional


class OrgChartResponse(BaseModel):
    """Response model for org chart operations"""
    
    response: str = Field(
        ...,
        description="User-friendly response about the org chart operation or query"
    )
    
    HTML_TABLE_DATA: str = Field(
        ...,
        description="HTML formatted table with org chart/hierarchy data results"
    )
    
    statistics: Optional[dict] = Field(
        None,
        description="Optional statistics about the org chart data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Successfully updated employee hierarchy with 150 employees from 12 managers across 8 departments.",
                "HTML_TABLE_DATA": "<table><thead><tr><th>Manager</th><th>Employee</th><th>Department</th></tr></thead><tbody><tr><td>John Smith</td><td>Jane Doe</td><td>IT</td></tr></tbody></table>",
                "statistics": {
                    "total_employees": 150,
                    "unique_managers": 12,
                    "unique_departments": 8
                }
            }
        }
