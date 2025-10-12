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
    
    statistics: Optional[dict] = Field(
        None,
        description="Optional statistics about the org chart data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Successfully updated employee hierarchy with 150 employees from 12 managers across 8 departments.",
                "statistics": {
                    "total_employees": 150,
                    "unique_managers": 12,
                    "unique_departments": 8
                }
            }
        }
