import sqlite3
import pandas as pd
import numpy as np

# Database connection
DB_PATH = "System-Info/expense_reports.db"


def get_categorical_values(conn, table_name, column_name):
    query = f"""
    SELECT DISTINCT {column_name} 
    FROM {table_name} 
    WHERE {column_name} IS NOT NULL
    ORDER BY {column_name}
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        return [str(val) for val in df[column_name].tolist()]
    return []


def get_column_info(cursor, conn, table_name):
    # Get basic column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {col[1]: {"type": col[2]} for col in cursor.fetchall()}

    # Check for categorical values in TEXT columns
    for col_name, info in columns.items():
        if info["type"] == "TEXT":
            unique_values = get_categorical_values(conn, table_name, col_name)
            if (
                len(unique_values) > 0 and len(unique_values) <= 10
            ):  # Consider columns with ≤10 unique values as categorical
                info["categorical_values"] = unique_values

    return columns


def get_sample_data(conn, table_name):
    # Get sample data prioritizing non-null values
    query = f"""
    WITH RankedRows AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY CASE 
                    WHEN report_submit_date IS NOT NULL THEN 1
                    WHEN violation_type IS NOT NULL THEN 2
                    WHEN justification IS NOT NULL THEN 3
                    WHEN selected_for_audit = 'Y' THEN 4
                    ELSE 5 
                END
            ) as rn
        FROM {table_name}
    )
    SELECT * FROM RankedRows 
    WHERE rn = 1
    LIMIT 5
    """
    return pd.read_sql_query(query, conn)


def read_table_sample():
    try:
        # Create a connection to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # First, let's get the list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database!")
            return

        print("Available tables:", [table[0] for table in tables])

        # Use the first table
        table_name = tables[1][0]
        print(f"Reading from table: {table_name}")

        # Get column information with categorical values
        column_info = get_column_info(cursor, conn, table_name)

        # Get sample data
        df = get_sample_data(conn, table_name)

        # Write to output file
        output_file = "db_sample_output.txt"
        with open(output_file, "w") as f:
            f.write(f"Table Name: {table_name}\n")
            f.write("=" * 50 + "\n\n")

            # Write column names with their types and categorical values
            f.write("Column Names and Types:\n")
            f.write("-" * 30 + "\n")
            max_col_length = max(len(col) for col in column_info.keys())

            for col, info in column_info.items():
                base_type = f"{col:<{max_col_length}} : {info['type']}"
                if "categorical_values" in info:
                    categorical_values = (
                        f" (Values: {', '.join(info['categorical_values'])})"
                    )
                    f.write(f"{base_type}{categorical_values}\n")
                else:
                    f.write(f"{base_type}\n")
            f.write("\n")

            # Write sample rows
            f.write("Sample Rows (selected for diversity):\n")
            f.write("-" * 30 + "\n")
            f.write(df.to_string(index=False))

        print(f"Output has been written to {output_file}")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    read_table_sample()
