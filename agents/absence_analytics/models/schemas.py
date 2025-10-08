"""
Absence Analytics Agent Models/Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AbsenceResponse(BaseModel):
    """Response model for absence analytics queries"""
    
    User_Friendly_response: str = Field(
        description="Human-readable explanation of the absence data analysis"
    )
    
    HTML_TABLE_DATA: str = Field(
        description="HTML formatted table with absence data results"
    )
    
    total_employees: Optional[int] = Field(
        default=None,
        description="Total number of employees in the result"
    )
    
    total_balance_days: Optional[float] = Field(
        default=None,
        description="Total leave balance in days"
    )


class AbsenceQueryRequest(BaseModel):
    """Request model for absence queries"""
    
    query: str = Field(
        description="Natural language query about absence/leave data"
    )
    
    employee_name: Optional[str] = Field(
        default=None,
        description="Specific employee name to filter"
    )
    
    department: Optional[str] = Field(
        default=None,
        description="Department name to filter"
    )
    
    absence_plan: Optional[str] = Field(
        default=None,
        description="Leave plan type (e.g., 'Annual Leave Plan')"
    )
