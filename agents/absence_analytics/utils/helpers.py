"""
Helper utilities for Absence Analytics Agent
"""

def format_balance(balance: float) -> str:
    """Format leave balance for display"""
    if balance is None:
        return "N/A"
    return f"{balance:.2f} days"


def format_employee_summary(data: dict) -> str:
    """Format employee absence summary"""
    summary = []
    summary.append(f"Employee: {data.get('employee_name', 'Unknown')}")
    summary.append(f"Person Number: {data.get('person_number', 'N/A')}")
    summary.append(f"Department: {data.get('department_name', 'N/A')}")
    summary.append(f"Job: {data.get('job_name', 'N/A')}")
    summary.append(f"Leave Balance: {format_balance(data.get('balance'))}")
    
    return "\n".join(summary)


def calculate_total_balance(results: list) -> float:
    """Calculate total balance from query results"""
    return sum(row.get('balance', 0) for row in results if row.get('balance') is not None)
