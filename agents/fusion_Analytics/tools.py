from crewai.tools import tool
import sqlite3
import json

# Import smart_db_updater from the fusion_Analytics directory
from agents.fusion_Analytics.smart_db_updater import (
    get_updater,
    trigger_update,
    get_update_status,
)

# ==================== CONFIGURATION ====================

DB_PATH = "System-Info/expense_reports.db"
COOLDOWN_SECONDS = 10  # Check/update every 10 seconds max

# Initialize updater once (at module level)
db_updater = get_updater(cooldown_seconds=COOLDOWN_SECONDS)


def refresh_fusion_analytics_data():
    """
    Custom refresh logic for Fusion Analytics database
    Fetches latest data from Oracle Fusion and loads into SQLite
    """
    print(f"🔄 Refreshing Fusion Analytics database from Oracle Fusion...")

    try:
        # Import the refresh function from get_data.py
        from agents.fusion_Analytics.get_data import refresh_database_from_oracle

        # Execute the refresh
        result = refresh_database_from_oracle()

        if result["status"] == "success":
            print(f"  ✅ Database refreshed successfully")
            print(f"     Inserted: {result['inserted_count']} records")
            print(f"     Total in DB: {result['final_count']} records")
            return result
        else:
            print(f"  ❌ Database refresh failed: {result['message']}")
            raise Exception(result["message"])

    except Exception as e:
        print(f"  ❌ Error refreshing database: {e}")
        raise


# Set the update function
db_updater.set_update_function(refresh_fusion_analytics_data)


# ==================== SINGLE TOOL ====================


@tool
def execute_sql_query(sql_query: str, user_id: str = None) -> str:
    """
    Execute SQL query on the Fusion Analytics database.
    Automatically checks and updates database if needed before running query.

    Args:
        sql_query: The SQL query to execute (SELECT statements only for safety)
        user_id: Optional user ID who triggered this query

    Returns:
        JSON string with query results or status message

    Examples:
        - execute_sql_query("SELECT * FROM expense_report_data LIMIT 10")
        - execute_sql_query("SELECT COUNT(*) FROM expense_report_data WHERE expense_status_code = 'APPROVED'")
        - execute_sql_query("SELECT employee_name, SUM(reimbursable_amount) FROM expense_report_data GROUP BY employee_name")
    """
    user_id = user_id or "fusion_analytics_agent"

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
            refresh_fusion_analytics_data()
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
        return json.dumps(
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

    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        print(f"  ❌ {error_msg}")
        return json.dumps({"status": "error", "error": error_msg})
