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
DB_PATH = "System-Info/absence_reports.db"


def get_absence_report_data(DATE_OF_ABSENCE=None):
    """
    Download absence report from Oracle service and return as Excel bytes
    
    Args:
        DATE_OF_ABSENCE: Date string in format 'DD-MM-YYYY' (optional, defaults to today)
    
    Returns: Excel file bytes or None if failed
    """
    # Default to today if no date provided
    if DATE_OF_ABSENCE is None:
        DATE_OF_ABSENCE = datetime.now().strftime('%d-%m-%Y')
        logger.info(f"📅 No date provided, using today: {DATE_OF_ABSENCE}")
    
    # Ensure date is in DD-MM-YYYY format for Oracle
    # Try to parse various input formats and convert to DD-MM-YYYY
    try:
        # If input is YYYY-MM-DD, convert to DD-MM-YYYY
        if len(DATE_OF_ABSENCE) == 10 and DATE_OF_ABSENCE[4] == '-' and DATE_OF_ABSENCE[7] == '-':
            dt = datetime.strptime(DATE_OF_ABSENCE, '%Y-%m-%d')
            DATE_OF_ABSENCE = dt.strftime('%d-%m-%Y')
            logger.info(f"📅 Converted date to Oracle format: {DATE_OF_ABSENCE}")
    except Exception as e:
        logger.warning(f"⚠️ Could not parse date format, using as-is: {DATE_OF_ABSENCE}")
    
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
                    <pub:reportAbsolutePath>API/Absence_report.xdo</pub:reportAbsolutePath>
                    <pub:attributeFormat>xlsx</pub:attributeFormat>
                    <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                    <pub:parameterNameValues>
                           <pub:item>
                                 <pub:name>P_EFF_DATE</pub:name>
                                 <pub:values>
                                    <pub:item>{DATE_OF_ABSENCE}</pub:item>
                                 </pub:values>
                           </pub:item>
                           <pub:item>
                                 <pub:name>P_ASOF_DATE</pub:name>
                                 <pub:values>
                                    <pub:item>{DATE_OF_ABSENCE}</pub:item>
                                 </pub:values>
                           </pub:item>
                    </pub:parameterNameValues>
                 </pub:reportRequest>
              </pub:runReport>
           </soap12:Body>
        </soap12:Envelope>
        """

        headers = {
           "Content-Type": "application/soap+xml;charset=UTF-8"
        }

        logger.info("🔄 Fetching absence report from Oracle Fusion...")
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
              logger.info("✅ Absence report data received successfully")
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
        logger.error(f"❌ Error downloading absence report: {str(e)}")
        return None


def load_absence_data_to_database(excel_data_bytes=None, db_path=DB_PATH,date_of_absence=None):
    """
    Load absence report data from Excel to database
    
    Args:
        excel_data_bytes: Excel file as bytes (if None, will fetch from Oracle)
        db_path: Path to SQLite database
    
    Returns:
        Dictionary with status and statistics
    """
    try:
        # Step 1: Get Excel data if not provided
        if excel_data_bytes is None:
            logger.info("📥 Fetching absence data from Oracle Fusion...")
            excel_data_bytes = get_absence_report_data(date_of_absence)
            if excel_data_bytes is None:
                return {"status": "error", "message": "Failed to fetch absence report from Oracle"}
        
        # Step 2: Read Excel data into pandas DataFrame
        logger.info("📊 Reading Excel data...")
        df = pd.read_excel(BytesIO(excel_data_bytes))
        
        logger.info(f"  Found {len(df)} rows in Excel file (before cleaning)")
        logger.info(f"  Initial columns: {list(df.columns)}")
        
        # Check if first row contains the actual column names (common with Oracle reports)
        first_row = df.iloc[0]
        if 'PERSON_NUMBER' in str(first_row.values).upper():
            logger.info("  Detected header row in first data row, adjusting...")
            # Use first row as header
            df.columns = df.iloc[0]
            df = df[1:]  # Remove the header row from data
            df.reset_index(drop=True, inplace=True)
            logger.info(f"  Adjusted columns: {list(df.columns)}")
        
        logger.info(f"  Final row count: {len(df)}")
        logger.info(f"  Final columns: {list(df.columns)}")
        
        # Step 3: Map Excel columns to database columns
        column_mapping = {
            'PERSON_NUMBER': 'person_number',
            'ABSENCE_PLAN_NAME': 'absence_plan_name',
            'BALANCE': 'balance',
            'ACCRUAL_PERIOD': 'accrual_period',
            'JOB_NAME': 'job_name',
            'GRADE_NAME': 'grade_name',
            'BUSINESS_UNIT': 'business_unit',
            'EMPLOYEE_NAME': 'employee_name',
            'DEPARTMENT_NAME': 'department_name'
        }
        
        # Rename columns to match database schema
        df = df.rename(columns=column_mapping)
        
        # Step 4: Clean and transform data
        logger.info("🧹 Cleaning data...")
        
        # Convert balance to numeric
        if 'balance' in df.columns:
            df['balance'] = pd.to_numeric(df['balance'], errors='coerce')
        
        # Convert date fields to string format (SQLite-compatible)
        if 'accrual_period' in df.columns:
            df['accrual_period'] = pd.to_datetime(df['accrual_period'], errors='coerce')
            df['accrual_period'] = df['accrual_period'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
            )
        
        # Replace NaN/NaT with None for proper NULL handling in SQLite
        df = df.where(pd.notna(df), None)
        df = df.replace({pd.NA: None, float('nan'): None})
        
        logger.info(f"  Cleaned {len(df)} rows")
        
        # Step 5: Connect to database
        logger.info(f"💾 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 6: Clear existing data
        logger.info("🗑️  Clearing old data...")
        cursor.execute("DELETE FROM absence_report_data")
        deleted_count = cursor.rowcount
        logger.info(f"  Deleted {deleted_count} old records")
        
        # Step 7: Insert new data
        logger.info("📝 Inserting new data...")
        
        # Get actual database columns (excluding 'id' which is auto-increment)
        cursor.execute("PRAGMA table_info(absence_report_data)")
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
        insert_sql = f"INSERT INTO absence_report_data ({columns_str}) VALUES ({placeholders})"
        
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
                if failed_count < 5:
                    logger.error(f"     Values: {[row[col] for col in available_columns]}")
                failed_count += 1
        
        # Commit changes
        conn.commit()
        
        # Step 8: Verify insertion
        cursor.execute("SELECT COUNT(*) FROM absence_report_data")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(balance) FROM absence_report_data")
        total_balance = cursor.fetchone()[0] or 0
        
        conn.close()
        
        logger.info("✅ Data load completed successfully!")
        logger.info(f"  Inserted: {inserted_count} records")
        logger.info(f"  Failed: {failed_count} records")
        logger.info(f"  Total in DB: {final_count} records")
        logger.info(f"  Total balance: {total_balance:.2f} days")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "inserted_count": inserted_count,
            "failed_count": failed_count,
            "final_count": final_count,
            "total_balance": total_balance,
            "message": f"Successfully loaded {inserted_count} absence records into database"
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading absence data to database: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def refresh_absence_database_from_oracle(date_of_absence):
    """
    Main function to refresh absence database with latest data from Oracle Fusion
    This is the function you should call from your tools.py
    
    Returns:
        Dictionary with status and statistics
    """
    logger.info("="*70)
    logger.info("🔄 REFRESHING ABSENCE DATABASE FROM ORACLE FUSION")
    logger.info("="*70)
    
    result = load_absence_data_to_database(date_of_absence=date_of_absence)
    
    if result["status"] == "success":
        logger.info("="*70)
        logger.info("✅ ABSENCE DATABASE REFRESH COMPLETED")
        logger.info(f"   Inserted: {result['inserted_count']} records")
        logger.info(f"   Total in DB: {result['final_count']} records")
        logger.info(f"   Total balance: {result.get('total_balance', 0):.2f} days")
        logger.info("="*70)
    else:
        logger.error("="*70)
        logger.error("❌ ABSENCE DATABASE REFRESH FAILED")
        logger.error(f"   Error: {result['message']}")
        logger.error("="*70)
    
    return result


# For backward compatibility
def get_report():
    """Download absence report from Oracle service (legacy function)"""
    excel_data = get_absence_report_data()
    if excel_data:
        with open("absence_report.xlsx", "wb") as f:
            f.write(excel_data)
        logger.info("✅ Absence report saved as absence_report.xlsx (for debugging)")
        return True
    return False


if __name__ == "__main__":
    # Test the data loading
    result = refresh_absence_database_from_oracle()
    print("\nResult:")
    print(result)
