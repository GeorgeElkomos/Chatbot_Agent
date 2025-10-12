"""
Org Chart Agent - Get employee hierarchy data from Oracle Fusion
"""

import requests
import base64
import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "System-Info/employee_hierarchy.db"


def get_org_chart_data(effective_date=None):
    """
    Download employee hierarchy report from Oracle service and return as Excel bytes
    
    Args:
        effective_date: Date string in format 'DD-MM-YYYY' (optional, defaults to today)
    
    Returns: Excel file bytes or None if failed
    """
    # Default to today if no date provided
    if effective_date is None:
        effective_date = datetime.now().strftime('%d-%m-%Y')
        logger.info(f"📅 No date provided, using today: {effective_date}")
    
    # Ensure date is in DD-MM-YYYY format for Oracle
    try:
        # If input is YYYY-MM-DD, convert to DD-MM-YYYY
        if len(effective_date) == 10 and effective_date[4] == '-' and effective_date[7] == '-':
            dt = datetime.strptime(effective_date, '%Y-%m-%d')
            effective_date = dt.strftime('%d-%m-%Y')
            logger.info(f"📅 Converted date to Oracle format: {effective_date}")
    except Exception as e:
        logger.warning(f"⚠️ Could not parse date format, using as-is: {effective_date}")
    
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
                    <pub:reportAbsolutePath>API/Org_Chart_Report.xdo</pub:reportAbsolutePath>
                    <pub:attributeFormat>xlsx</pub:attributeFormat>
                    <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                    <pub:parameterNameValues>
                           <pub:item>
                                 <pub:name>P_EFF_DATE</pub:name>
                                 <pub:values>
                                    <pub:item>{effective_date}</pub:item>
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

        logger.info("🔄 Fetching org chart data from Oracle Fusion...")
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
              logger.info("✅ Org chart data received successfully")
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
        logger.error(f"❌ Error downloading org chart: {str(e)}")
        return None


def load_org_chart_to_database(excel_data_bytes=None, db_path=DB_PATH, effective_date=None):
    """
    Load employee hierarchy data from Excel to database
    
    Args:
        excel_data_bytes: Excel file as bytes (if None, will fetch from Oracle)
        db_path: Path to SQLite database
        effective_date: Date for the org chart snapshot
    
    Returns:
        Dictionary with status and statistics
    """
    try:
        # Step 1: Get Excel data if not provided
        if excel_data_bytes is None:
            logger.info("📥 Fetching org chart data from Oracle Fusion...")
            excel_data_bytes = get_org_chart_data(effective_date)
            if excel_data_bytes is None:
                return {"status": "error", "message": "Failed to fetch org chart from Oracle"}
        
        # Step 2: Read Excel data into pandas DataFrame
        logger.info("📊 Reading Excel data...")
        df = pd.read_excel(BytesIO(excel_data_bytes))
        
        logger.info(f"  Found {len(df)} rows in Excel file (before cleaning)")
        logger.info(f"  Initial columns: {list(df.columns)}")
        
        # Check if first row contains the actual column names
        first_row = df.iloc[0]
        if 'MANAGER_PERSON_NUMBER' in str(first_row.values).upper():
            logger.info("  Detected header row in first data row, adjusting...")
            df.columns = df.iloc[0]
            df = df[1:]
            df.reset_index(drop=True, inplace=True)
            logger.info(f"  Adjusted columns: {list(df.columns)}")
        
        logger.info(f"  Final row count: {len(df)}")
        logger.info(f"  Final columns: {list(df.columns)}")
        
        # Step 3: Map Excel columns to database columns
        column_mapping = {
            'MANAGER_PERSON_NUMBER': 'MANAGER_PERSON_NUMBER',
            'MANAGER_NAME': 'MANAGER_NAME',
            'PERSON_NUMBER': 'PERSON_NUMBER',
            'EMPLOYEE_NAME': 'EMPLOYEE_NAME',
            'DEPARTMENT_NAME': 'DEPARTMENT_NAME'
        }
        
        # Rename columns to match database schema
        df = df.rename(columns=column_mapping)
        
        # Keep only the columns we need
        required_columns = ['MANAGER_PERSON_NUMBER', 'MANAGER_NAME', 'PERSON_NUMBER', 'EMPLOYEE_NAME', 'DEPARTMENT_NAME']
        df = df[required_columns]
        
        # Step 4: Clean and transform data
        logger.info("🧹 Cleaning data...")
        
        # Convert person numbers to integers
        df['MANAGER_PERSON_NUMBER'] = pd.to_numeric(df['MANAGER_PERSON_NUMBER'], errors='coerce').astype('Int64')
        df['PERSON_NUMBER'] = pd.to_numeric(df['PERSON_NUMBER'], errors='coerce').astype('Int64')
        
        # Clean string fields - remove extra whitespace
        for col in ['MANAGER_NAME', 'EMPLOYEE_NAME', 'DEPARTMENT_NAME']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['PERSON_NUMBER', 'EMPLOYEE_NAME'])
        
        # Replace NaN with None for proper NULL handling in SQLite
        df = df.where(pd.notna(df), None)
        
        logger.info(f"  Cleaned {len(df)} rows")
        
        # Step 5: Connect to database
        logger.info(f"💾 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 6: Clear existing data
        logger.info("🗑️  Clearing old data...")
        cursor.execute("DELETE FROM employee_hierarchy")
        deleted_count = cursor.rowcount
        logger.info(f"  Deleted {deleted_count} old records")
        
        # Step 7: Insert new data
        logger.info("📝 Inserting new data...")
        
        insert_query = """
        INSERT INTO employee_hierarchy 
        (MANAGER_PERSON_NUMBER, MANAGER_NAME, PERSON_NUMBER, EMPLOYEE_NAME, DEPARTMENT_NAME)
        VALUES (?, ?, ?, ?, ?)
        """
        
        records = df.to_records(index=False).tolist()
        cursor.executemany(insert_query, records)
        
        inserted_count = cursor.rowcount
        logger.info(f"  Inserted {inserted_count} new records")
        
        # Step 8: Commit and close
        conn.commit()
        
        # Step 9: Get statistics
        cursor.execute("SELECT COUNT(*) FROM employee_hierarchy")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT MANAGER_PERSON_NUMBER) FROM employee_hierarchy")
        manager_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT DEPARTMENT_NAME) FROM employee_hierarchy")
        department_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("✅ Data loaded successfully!")
        logger.info(f"  Total employees: {total_count}")
        logger.info(f"  Unique managers: {manager_count}")
        logger.info(f"  Unique departments: {department_count}")
        
        return {
            "status": "success",
            "message": f"Successfully loaded {inserted_count} employee records",
            "statistics": {
                "total_employees": total_count,
                "unique_managers": manager_count,
                "unique_departments": department_count,
                "deleted_old_records": deleted_count,
                "inserted_new_records": inserted_count
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading data to database: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load data: {str(e)}"
        }


if __name__ == "__main__":
    # Test the functions
    print("Testing org chart data download and database load...")
    result = load_org_chart_to_database()
    print(f"\nResult: {result}")
