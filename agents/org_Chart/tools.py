"""
Org Chart Tools - Tools for querying employee hierarchy data
"""

from crewai.tools import tool
import sqlite3
import json

# Import smart_db_updater from the org_Chart directory
from agents.org_Chart.smart_db_updater import (
    get_updater,
    trigger_update,
    get_update_status,
)

# ==================== CONFIGURATION ====================

DB_PATH = "System-Info/employee_hierarchy.db"
COOLDOWN_SECONDS = 10  # Check/update every 10 seconds max

# Initialize updater once (at module level)
db_updater = get_updater(cooldown_seconds=COOLDOWN_SECONDS)


def refresh_org_chart_data():
    """
    Custom refresh logic for Org Chart database
    Fetches latest data from Oracle Fusion and loads into SQLite
    """
    print(f"🔄 Refreshing Org Chart database from Oracle Fusion...")

    try:
        # Import the refresh function from get_data.py
        from agents.org_Chart.get_data import load_org_chart_to_database

        # Execute the refresh
        result = load_org_chart_to_database()

        if result["status"] == "success":
            stats = result.get("statistics", {})
            print(f"  ✅ Database refreshed successfully")
            print(f"     Inserted: {stats.get('inserted_new_records', 0)} records")
            print(f"     Total in DB: {stats.get('total_employees', 0)} employees")
            return result
        else:
            print(f"  ❌ Database refresh failed: {result['message']}")
            raise Exception(result["message"])

    except Exception as e:
        print(f"  ❌ Error refreshing database: {e}")
        raise


# Set the update function
db_updater.set_update_function(refresh_org_chart_data)


# ==================== SINGLE TOOL ====================


@tool
def execute_org_chart_query(sql_query: str, user_id: str = None) -> str:
    """
    Execute SQL query on the Employee Hierarchy (Org Chart) database.
    Automatically checks and updates database if needed before running query.

    Args:
        sql_query: The SQL query to execute (SELECT statements only for safety)
        user_id: Optional user ID who triggered this query

    Returns:
        JSON string with query results or status message

    Examples:
        - execute_org_chart_query("SELECT * FROM employee_hierarchy LIMIT 10")
        - execute_org_chart_query("SELECT COUNT(*) FROM employee_hierarchy WHERE MANAGER_PERSON_NUMBER = 10204")
        - execute_org_chart_query("SELECT MANAGER_NAME, COUNT(*) as team_size FROM employee_hierarchy GROUP BY MANAGER_NAME")
        - execute_org_chart_query("SELECT * FROM employee_hierarchy WHERE DEPARTMENT_NAME = 'Real Estate'")
    """
    # Track tool call at the very beginning
    from iteration_tracker import get_tracker
    tracker = get_tracker()
    tracker.log_tool_call("execute_org_chart_query", {"sql_query": sql_query, "user_id": user_id})
    
    user_id = user_id or "org_chart_agent"

    try:
        # Step 1: Check if database needs updating and update if needed
        print(f"📊 Executing SQL query for user: {user_id}")
        # Check update status
        status = get_update_status()
        print(f"  ⏱️  Last update: {status['last_update']}")
        print(f"  ⏰ Can update now: {status['can_update_now']}")

        updated = False
        # Only trigger update if cooldown period has passed
        if status["can_update_now"]:
            print(f"  🔄 Cooldown expired, updating database...")
            updated = trigger_update(user_id=user_id)
            refresh_org_chart_data()
            if updated:
                print(f"  ✅ Database was updated before query")
            else:
                print(f"  ⚠️  Update was triggered but returned False")
        else:
            print(f"  ⏭️  Database is fresh (within cooldown period, skipping update)")

        # Step 2: Execute the SQL query
        print(f"  🔍 Executing query: {sql_query[:100]}...")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        # Security: Only allow SELECT queries for safety
        if not sql_query.strip().upper().startswith("SELECT"):
            conn.close()
            return json.dumps(
                {
                    "error": "Only SELECT queries are allowed for safety",
                    "status": "rejected",
                }
            )

        # Execute query
        cursor.execute(sql_query)
        results = cursor.fetchall()

        # Convert to list of dicts
        results_list = [dict(row) for row in results]

        conn.close()

        print(f"  ✅ Query executed successfully: {len(results_list)} rows returned")

        # Return results as JSON
        result = json.dumps(
            {
                "status": "success",
                "row_count": len(results_list),
                "data": results_list,
                "updated_before_query": updated,
                "last_database_update": status["last_update"],
            },
            indent=2,
            default=str,
        )
        
        # Track tool output before returning
        tracker.log_tool_output(result)
        return result

    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        print(f"  ❌ {error_msg}")
        error_result = json.dumps({"status": "error", "error": error_msg})
        
        # Track tool output even for errors
        tracker.log_tool_output(error_result)
        return error_result
