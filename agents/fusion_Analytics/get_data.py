import requests
import base64
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "System-Info/expense_reports.db"


def get_report_data():
    """
    Download report from Oracle service and return as Excel bytes
    Returns: Excel file bytes or None if failed
    """
    try:
        url = "https://hcbg-dev4.fa.ocs.oraclecloud.com:443/xmlpserver/services/ExternalReportWSSService"
        username = "AFarghaly"
        password = "Mubadala345"

        soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:pub="http://xmlns.oracle.com/oxp/service/PublicReportService">
           <soap12:Header/>
           <soap12:Body>
              <pub:runReport>
                 <pub:reportRequest>
                    <pub:reportAbsolutePath>API/Expensess_Report.xdo</pub:reportAbsolutePath>
                    <pub:attributeFormat>xlsx</pub:attributeFormat>
                    <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                    <pub:parameterNameValues>
                    </pub:parameterNameValues>
                 </pub:reportRequest>
              </pub:runReport>
           </soap12:Body>
        </soap12:Envelope>
        """

        headers = {
           "Content-Type": "application/soap+xml;charset=UTF-8"
        }

        logger.info("🔄 Fetching report from Oracle Fusion...")
        response = requests.post(url, data=soap_body, headers=headers, auth=(username, password))

        if response.status_code == 200:
           ns = {
              "soap12": "http://www.w3.org/2003/05/soap-envelope",
              "pub": "http://xmlns.oracle.com/oxp/service/PublicReportService"
           }
           root = ET.fromstring(response.text)
           report_bytes_element = root.find(".//pub:reportBytes", ns)
           
           if report_bytes_element is not None and report_bytes_element.text:
              excel_data = base64.b64decode(report_bytes_element.text)
              logger.info("✅ Report data received successfully")
              return excel_data
           else:
              logger.error("❌ No <reportBytes> found in response")
              logger.error(response.text)
              return None
        else:
           logger.error(f"❌ HTTP Error {response.status_code}")
           logger.error(response.text)
           return None
           
    except Exception as e:
        logger.error(f"❌ Error downloading report: {str(e)}")
        return None


def load_data_to_database(excel_data_bytes=None, db_path=DB_PATH):
    """
    Load expense report data from Excel to database
    
    Args:
        excel_data_bytes: Excel file as bytes (if None, will fetch from Oracle)
        db_path: Path to SQLite database
    
    Returns:
        Dictionary with status and statistics
    """
    try:
        # Step 1: Get Excel data if not provided
        if excel_data_bytes is None:
            logger.info("📥 Fetching data from Oracle Fusion...")
            excel_data_bytes = get_report_data()
            if excel_data_bytes is None:
                return {"status": "error", "message": "Failed to fetch report from Oracle"}
        
        # Step 2: Read Excel data into pandas DataFrame
        logger.info("📊 Reading Excel data...")
        df = pd.read_excel(BytesIO(excel_data_bytes))
        
        logger.info(f"  Found {len(df)} rows in Excel file (before cleaning)")
        logger.info(f"  Initial columns: {list(df.columns)}")
        
        # Check if first row contains the actual column names (common with Oracle reports)
        first_row = df.iloc[0]
        if 'EXPENSE_REPORT_ID' in str(first_row.values).upper():
            logger.info("  Detected header row in first data row, adjusting...")
            # Use first row as header
            df.columns = df.iloc[0]
            df = df[1:]  # Remove the header row from data
            df.reset_index(drop=True, inplace=True)
            logger.info(f"  Adjusted columns: {list(df.columns)}")
        
        logger.info(f"  Final row count: {len(df)}")
        logger.info(f"  Final columns: {list(df.columns)}")
        
        # Step 3: Map Excel columns to database columns
        # Expected Excel columns from your example:
        column_mapping = {
            'EXPENSE_REPORT_ID': 'expense_report_id',
            'REPORT_SUBMIT_DATE': 'report_submit_date',
            'EXPENSE_REPORT_NUM': 'expense_report_num',
            'REPORT_PURPOSE': 'report_purpose',
            'EXPENSE_STATUS_CODE': 'expense_status_code',
            'EXPENSE_REPORT_TOTAL': 'expense_report_total',
            'REIMBURSEMENT_CURRENCY_CODE': 'reimbursement_currency_code',
            'BUSINESS_UNIT_NAME': 'business_unit_name',
            'EMPLOYEE_NAME': 'employee_name',
            'EXPENSE_LINE_ID': 'expense_line_id',
            'EXPENSE_TYPE_NAME': 'expense_type_name',
            'MERCHANT_NAME': 'merchant_name',
            'REIMBURSABLE_AMOUNT': 'reimbursable_amount',
            'RECEIPT_AMOUNT': 'receipt_amount',
            'RECEIPT_CURRENCY_CODE': 'receipt_currency_code',
            'EXPENSE_DATE': 'expense_date',
            'DESCRIPTION': 'description',
            'JUSTIFICATION': 'justification',
            'SELECTED_FOR_AUDIT': 'selected_for_audit',
            'VIOLATION_TYPE': 'violation_type',
            'EXCEEDED_AMOUNT': 'exceeded_amount',
            'ALLOWABLE_AMOUNT': 'allowable_amount'
        }
        
        # Rename columns to match database schema
        df = df.rename(columns=column_mapping)
        
        # Step 4: Clean and transform data
        logger.info("🧹 Cleaning data...")
        
        # Convert expense_report_id and expense_line_id from scientific notation
        if 'expense_report_id' in df.columns:
            df['expense_report_id'] = df['expense_report_id'].apply(
                lambda x: int(float(x)) if pd.notna(x) else None
            )
        
        if 'expense_line_id' in df.columns:
            df['expense_line_id'] = df['expense_line_id'].apply(
                lambda x: int(float(x)) if pd.notna(x) else None
            )
        
        # Convert date fields to string format (SQLite-compatible)
        if 'report_submit_date' in df.columns:
            df['report_submit_date'] = pd.to_datetime(df['report_submit_date'], errors='coerce')
            df['report_submit_date'] = df['report_submit_date'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
            )
        
        if 'expense_date' in df.columns:
            df['expense_date'] = pd.to_datetime(df['expense_date'], errors='coerce')
            df['expense_date'] = df['expense_date'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
            )
        
        # Convert numeric fields
        numeric_fields = ['expense_report_total', 'reimbursable_amount', 'receipt_amount', 
                         'exceeded_amount', 'allowable_amount']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # Replace NaN/NaT with None for proper NULL handling in SQLite
        # This is critical - pandas NaN and NaT are not compatible with SQLite
        df = df.where(pd.notna(df), None)
        
        # Also replace any numpy.nan explicitly
        df = df.replace({pd.NA: None, float('nan'): None})
        
        logger.info(f"  Cleaned {len(df)} rows")
        
        # Step 5: Connect to database
        logger.info(f"💾 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 6: Clear existing data (optional - remove if you want to append)
        logger.info("🗑️  Clearing old data...")
        cursor.execute("DELETE FROM expense_report_data")
        deleted_count = cursor.rowcount
        logger.info(f"  Deleted {deleted_count} old records")
        
        # Step 7: Insert new data
        logger.info("📝 Inserting new data...")
        
        # Get actual database columns (excluding 'id' which is auto-increment)
        cursor.execute("PRAGMA table_info(expense_report_data)")
        db_table_info = cursor.fetchall()
        db_columns = [col[1] for col in db_table_info if col[1] != 'id']
        
        logger.info(f"  Database columns: {db_columns}")
        logger.info(f"  DataFrame columns: {list(df.columns)}")
        
        # Filter to only columns that exist in both DataFrame and database
        available_columns = [col for col in db_columns if col in df.columns]
        
        if not available_columns:
            logger.error("❌ No matching columns found between DataFrame and database!")
            conn.close()
            return {
                "status": "error",
                "message": "No matching columns between Excel data and database schema"
            }
        
        logger.info(f"  Matched columns: {available_columns}")
        
        # Prepare insert statement
        placeholders = ','.join(['?' for _ in available_columns])
        columns_str = ','.join(available_columns)
        insert_sql = f"INSERT INTO expense_report_data ({columns_str}) VALUES ({placeholders})"
        
        logger.info(f"  Insert SQL: {insert_sql}")
        
        # Insert rows
        inserted_count = 0
        failed_count = 0
        
        for index, row in df.iterrows():
            try:
                values = [row[col] for col in available_columns]
                cursor.execute(insert_sql, values)
                inserted_count += 1
            except Exception as e:
                logger.error(f"  ❌ Error inserting row {index}: {str(e)}")
                # Log first few errors with more detail
                if failed_count < 5:
                    logger.error(f"     Values: {[row[col] for col in available_columns]}")
                failed_count += 1
        
        # Commit changes
        conn.commit()
        
        # Step 8: Verify insertion
        cursor.execute("SELECT COUNT(*) FROM expense_report_data")
        final_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("✅ Data load completed successfully!")
        logger.info(f"  Inserted: {inserted_count} records")
        logger.info(f"  Failed: {failed_count} records")
        logger.info(f"  Total in DB: {final_count} records")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "inserted_count": inserted_count,
            "failed_count": failed_count,
            "final_count": final_count,
            "message": f"Successfully loaded {inserted_count} records into database"
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading data to database: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def refresh_database_from_oracle():
    """
    Main function to refresh database with latest data from Oracle Fusion
    This is the function you should call from your tools.py
    
    Returns:
        Dictionary with status and statistics
    """
    logger.info("="*70)
    logger.info("🔄 REFRESHING DATABASE FROM ORACLE FUSION")
    logger.info("="*70)
    
    result = load_data_to_database()
    
    if result["status"] == "success":
        logger.info("="*70)
        logger.info("✅ DATABASE REFRESH COMPLETED")
        logger.info(f"   Inserted: {result['inserted_count']} records")
        logger.info(f"   Total in DB: {result['final_count']} records")
        logger.info("="*70)
    else:
        logger.error("="*70)
        logger.error("❌ DATABASE REFRESH FAILED")
        logger.error(f"   Error: {result['message']}")
        logger.error("="*70)
    
    return result


# For backward compatibility - keeps the old function but doesn't save file
def get_report():
    """Download report from Oracle service (legacy function)"""
    excel_data = get_report_data()
    if excel_data:
        # Save file for debugging if needed
        with open("report.xlsx", "wb") as f:
            f.write(excel_data)
        logger.info("✅ Report saved as report.xlsx (for debugging)")
        return True
    return False


if __name__ == "__main__":
    # Test the data loading
    result = refresh_database_from_oracle()
    print("\nResult:")
    print(result)