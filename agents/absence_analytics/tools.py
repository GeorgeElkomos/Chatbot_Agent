from crewai.tools import tool
import sqlite3
import json
import logging
from datetime import datetime

# Import smart_db_updater from the fusion_Analytics directory (reuse existing implementation)
from agents.fusion_Analytics.smart_db_updater import SmartDBUpdater
from iteration_tracker import get_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================

DB_PATH = "System-Info/absence_reports.db"
COOLDOWN_SECONDS = 10  # Check/update every 10 seconds max

# Initialize updater for absence database
absence_updater = SmartDBUpdater(db_path=DB_PATH, cooldown_seconds=COOLDOWN_SECONDS)


def refresh_absence_analytics_data(date_of_absence):
    """
    Custom refresh logic for Absence Analytics database
    Fetches latest data from Oracle Fusion and loads into SQLite
    """
    logger.info(f"🔄 Refreshing Absence Analytics database from Oracle Fusion...")

    try:
        # Import the refresh function from get_data.py
        from agents.absence_analytics.get_data import (
            refresh_absence_database_from_oracle,
        )

        # Execute the refresh
        result = refresh_absence_database_from_oracle(date_of_absence)

        if result["status"] == "success":
            logger.info(f"  ✅ Database refreshed successfully")
            logger.info(f"     Inserted: {result['inserted_count']} records")
            logger.info(f"     Total in DB: {result['final_count']} records")
            logger.info(
                f"     Total balance: {result.get('total_balance', 0):.2f} days"
            )
            return result
        else:
            logger.error(f"  ❌ Database refresh failed: {result['message']}")
            raise Exception(result["message"])

    except Exception as e:
        logger.error(f"  ❌ Error refreshing absence database: {e}")
        raise


# Set the update function
absence_updater.set_update_function(refresh_absence_analytics_data)


# ==================== SINGLE TOOL ====================


@tool
def execute_absence_query(
    sql_query: str, date_of_absence: str = None, user_id: str = None
) -> str:
    """
    Execute SQL query on the Absence Analytics database.
    Automatically checks and updates database if needed before running query.

    Args:
        sql_query: The SQL query to execute (SELECT statements only for safety)
        date_of_absence: Date string in format 'MM-DD-YYYY' (optional, defaults to today)
        user_id: Optional user ID who triggered this query

    Returns:
        JSON string with query results or status message

    Examples:
        - execute_absence_query("SELECT * FROM absence_report_data LIMIT 10")
        - execute_absence_query("SELECT * FROM absence_report_data WHERE accrual_period >= '12-31-2025'", date_of_absence="12-31-2025")
        - execute_absence_query("SELECT employee_name, SUM(balance) FROM absence_report_data GROUP BY employee_name")
    """
    # Track tool call
    tracker = get_tracker()
    tracker.log_tool_call(
        "execute_absence_query",
        {
            "sql_query": sql_query,
            "date_of_absence": date_of_absence,
            "user_id": user_id,
        },
    )

    user_id = user_id or "absence_analytics_agent"

    # Convert date_of_absence string to datetime object
    if date_of_absence:
        try:
            # Parse the date string to datetime object
            absence_date = datetime.strptime(date_of_absence, "%m-%d-%Y")
            logger.info(f"📅 Using provided date: {absence_date.strftime('%m-%d-%Y')}")
        except ValueError:
            # If invalid format, use today's date
            logger.warning(
                f"⚠️  Invalid date format '{date_of_absence}', using today's date"
            )
            absence_date = datetime.now()
    else:
        # Default to today's date
        absence_date = datetime.now()
        logger.info(
            f"📅 No date provided, using today: {absence_date.strftime('%m-%d-%Y')}"
        )

    # Convert back to string for logging/usage
    date_str = absence_date.strftime("%m-%d-%Y")

    try:
        # Step 1: Check if database needs updating and update if needed
        logger.info(f"📊 Executing absence SQL query for user: {user_id}")
        logger.info(f"📅 Query date: {date_str}")

        # Check update status
        status = absence_updater.get_status()
        logger.info(f"  ⏱️  Last update: {status['last_update']}")
        logger.info(f"  ⏰ Can update now: {status['can_update_now']}")

        updated = False
        # Only trigger update if cooldown period has passed
        if status["can_update_now"]:
            logger.info(f"  🔄 Cooldown expired, updating absence database...")
            refresh_absence_analytics_data(date_of_absence)
            updated = True
            logger.info(f"  ✅ Absence database was updated before query")
        else:
            logger.info(
                f"  ⏭️  Database is fresh (within cooldown period, skipping update)"
            )

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

        logger.info(
            f"  ✅ Query executed successfully: {len(results_list)} rows returned"
        )

        # Return results as JSON
        result = json.dumps(
            {
                "status": "success",
                "row_count": len(results_list),
                "data": results_list,
                "query_date": date_str,
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
        error_msg = f"Error executing absence query: {str(e)}"
        logger.error(f"  ❌ {error_msg}")

        # Track error
        tracker.log_error(error_msg)

        result = json.dumps({"status": "error", "error": error_msg})

        # Track tool output
        tracker.log_tool_output(result)

        return result


# ==================== HELPER FUNCTIONS ====================


def get_absence_update_status():
    """Get the current update status of absence database"""
    return absence_updater.get_status()


def force_absence_update(user_id: str = "manual"):
    """Force an immediate update of absence database (bypasses cooldown)"""
    return absence_updater.update_now(user_id=user_id, force=True)
