"""
Org Chart Tools - Tools for querying employee hierarchy data
"""

from crewai.tools import tool
import sqlite3
import json
import logging
from datetime import datetime

# Import smart_db_updater from the org_Chart directory
from agents.org_Chart.smart_db_updater import (
    get_updater,
    trigger_update,
    get_update_status,
)
from iteration_tracker import get_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

DB_PATH = "System-Info/employee_hierarchy.db"
COOLDOWN_SECONDS = 10  # Check/update every 10 seconds max

# Initialize updater once (at module level)
db_updater = get_updater(cooldown_seconds=COOLDOWN_SECONDS)


def refresh_org_chart_data(effective_date):
    """
    Custom refresh logic for Org Chart database
    Fetches latest data from Oracle Fusion and loads into SQLite
    
    Args:
        effective_date: Date string in format 'DD-MM-YYYY' or 'YYYY-MM-DD'
    """
    logger.info(f"🔄 Refreshing Org Chart database from Oracle Fusion...")

    try:
        # Import the refresh function from get_data.py
        from agents.org_Chart.get_data import load_org_chart_to_database

        # Execute the refresh with effective_date
        result = load_org_chart_to_database(effective_date=effective_date)

        if result["status"] == "success":
            stats = result.get("statistics", {})
            logger.info(f"  ✅ Database refreshed successfully")
            logger.info(f"     Inserted: {stats.get('inserted_new_records', 0)} records")
            logger.info(f"     Total in DB: {stats.get('total_employees', 0)} employees")
            return result
        else:
            logger.error(f"  ❌ Database refresh failed: {result['message']}")
            raise Exception(result["message"])

    except Exception as e:
        logger.error(f"  ❌ Error refreshing org chart database: {e}")
        raise


# Set the update function
db_updater.set_update_function(refresh_org_chart_data)


# ==================== SINGLE TOOL ====================


@tool
def execute_org_chart_query(sql_query: str, effective_date: str = None, user_id: str = None) -> str:
    """
    Execute SQL query on the Employee Hierarchy (Org Chart) database.
    Automatically checks and updates database if needed before running query.

    Args:
        sql_query: The SQL query to execute (SELECT statements only for safety)
        effective_date: Date string in format 'DD-MM-YYYY' or 'YYYY-MM-DD' (optional, defaults to today)
        user_id: Optional user ID who triggered this query

    Returns:
        JSON string with query results or status message

    Examples:
        - execute_org_chart_query("SELECT * FROM employee_hierarchy LIMIT 10")
        - execute_org_chart_query("SELECT * FROM employee_hierarchy WHERE MANAGER_PERSON_NUMBER = 10204", effective_date="31-12-2025")
        - execute_org_chart_query("SELECT MANAGER_NAME, COUNT(*) as team_size FROM employee_hierarchy GROUP BY MANAGER_NAME")
        - execute_org_chart_query("SELECT * FROM employee_hierarchy WHERE DEPARTMENT_NAME = 'Real Estate'", effective_date="2025-12-31")
    """
    # Track tool call
    tracker = get_tracker()
    tracker.log_tool_call(
        "execute_org_chart_query",
        {
            "sql_query": sql_query,
            "effective_date": effective_date,
            "user_id": user_id,
        },
    )

    user_id = user_id or "org_chart_agent"

    # Convert effective_date string to datetime object
    if effective_date:
        try:
            # Try parsing DD-MM-YYYY format first
            if len(effective_date) == 10 and effective_date[2] == '-' and effective_date[5] == '-':
                eff_date = datetime.strptime(effective_date, "%d-%m-%Y")
                logger.info(f"📅 Using provided date (DD-MM-YYYY): {eff_date.strftime('%d-%m-%Y')}")
            # Try YYYY-MM-DD format
            elif len(effective_date) == 10 and effective_date[4] == '-' and effective_date[7] == '-':
                eff_date = datetime.strptime(effective_date, "%Y-%m-%d")
                logger.info(f"📅 Using provided date (YYYY-MM-DD): {eff_date.strftime('%d-%m-%Y')}")
            else:
                logger.warning(f"⚠️  Invalid date format '{effective_date}', using today's date")
                eff_date = datetime.now()
        except ValueError:
            logger.warning(f"⚠️  Invalid date format '{effective_date}', using today's date")
            eff_date = datetime.now()
    else:
        # Default to today's date
        eff_date = datetime.now()
        logger.info(f"📅 No date provided, using today: {eff_date.strftime('%d-%m-%Y')}")

    # Convert to DD-MM-YYYY format for Oracle
    date_str = eff_date.strftime("%d-%m-%Y")

    try:
        # Step 1: Check if database needs updating and update if needed
        logger.info(f"📊 Executing org chart SQL query for user: {user_id}")
        logger.info(f"📅 Query date: {date_str}")

        # Check update status
        status = get_update_status()
        logger.info(f"  ⏱️  Last update: {status['last_update']}")
        logger.info(f"  ⏰ Can update now: {status['can_update_now']}")

        updated = False
        # Only trigger update if cooldown period has passed
        if status["can_update_now"]:
            logger.info(f"  🔄 Cooldown expired, updating org chart database...")
            refresh_org_chart_data(date_str)
            updated = True
            logger.info(f"  ✅ Org chart database was updated before query")
        else:
            logger.info(f"  ⏭️  Database is fresh (within cooldown period, skipping update)")

        # Step 2: Execute the SQL query
        logger.info(f"  🔍 Executing query: {sql_query[:100]}...")

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

        logger.info(f"  ✅ Query executed successfully: {len(results_list)} rows returned")

        # Return results as JSON
        result = json.dumps(
            {
                "status": "success",
                "row_count": len(results_list),
                "data": results_list,
                "effective_date": date_str,
                "updated_before_query": updated,
                "last_database_update": status["last_update"],
            },
            indent=2,
            default=str,
        )
        
        # Track tool output
        tracker.log_tool_output(result)
        return result

    except Exception as e:
        error_msg = f"Error executing org chart query: {str(e)}"
        logger.error(f"  ❌ {error_msg}")

        # Track error
        tracker.log_error(error_msg)

        error_result = json.dumps({"status": "error", "error": error_msg})
        
        # Track tool output
        tracker.log_tool_output(error_result)
        return error_result


# ==================== HELPER FUNCTIONS ====================


def get_org_chart_update_status():
    """Get the current update status of org chart database"""
    return get_update_status()


def force_org_chart_update(effective_date: str = None, user_id: str = "manual"):
    """Force an immediate update of org chart database (bypasses cooldown)"""
    if not effective_date:
        effective_date = datetime.now().strftime("%d-%m-%Y")
    return refresh_org_chart_data(effective_date)
