"""SQL Tool for executing database queries."""
 
import oracledb
import os
from typing import Any
 
 
class SQLTool:
    """A tool for executing Oracle database queries."""
   
    def __init__(self):
        """Initialize with Oracle database credentials."""
        self.host = '185.197.251.203'
        self.port = 1521
        self.service_name = 'PROD'
        self.username = 'BUDGET_TRANSFER'
        self.password = 'KgJyrx3$1'

    def execute(self, query: str) -> str:
        """Execute a SQL query on Oracle and return results as a formatted string."""
        try:
            # Only allow SELECT queries for safety
            if not query.strip().upper().startswith('SELECT'):
                return "Error: Only SELECT queries are allowed."
               
            # Connect to Oracle database
            connection = oracledb.connect(
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                service_name=self.service_name
            )
           
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
               
                if not rows:
                    return "No results found."
                   
                # Format results as a table-like string
                output_lines = [" | ".join(columns)]
                output_lines.append("-" * len(output_lines[0]))
               
                for row in rows:
                    formatted_row = []
                    for i, value in enumerate(row):
                        if hasattr(value, 'read'):
                            formatted_row.append(str(value.read()))
                        else:
                            formatted_row.append(str(value) if value is not None else "NULL")
                    output_lines.append(" | ".join(formatted_row))
                   
            connection.close()
            return "\n".join(output_lines)
           
        except oracledb.Error as e:
            return f"Oracle Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
 