# Dynamic Google Sheets Uploader for AudiencePulse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger("audiencepulse")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_client(key_file: str = "service_account.json"):
    """Authenticate and return gspread client."""
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"Service account key not found: {key_file}")
    creds = ServiceAccountCredentials.from_json_keyfile_name(key_file, SCOPES)
    return gspread.authorize(creds), creds.service_account_email

def upload_dataframes(
    dataframes: Dict[str, pd.DataFrame],
    spreadsheet_name: str = "YouTube Analysis Data",
    key_file: str = "service_account.json"
) -> str:
    """
    Upload multiple DataFrames to Google Sheets dynamically.
    Each key in dataframes becomes a worksheet name.
    Returns the spreadsheet URL.
    """
    client, sa_email = get_client(key_file)
    
    # Open or create spreadsheet
    try:
        sheet = client.open(spreadsheet_name)
        logger.info(f"Opened existing sheet: '{spreadsheet_name}'")
    except gspread.SpreadsheetNotFound:
        logger.warning(f"Sheet '{spreadsheet_name}' not found.")
        logger.info("Attempting to create it...")
        try:
            sheet = client.create(spreadsheet_name)
            logger.info(f"Created new sheet: '{spreadsheet_name}'")
        except Exception as e:
            logger.error(f"Failed to create sheet: {e}")
            logger.info(f"\n💡 SOLUTION:")
            logger.info(f"1. Create a blank Google Sheet named: {spreadsheet_name}")
            logger.info(f"2. Share it with: {sa_email}")
            logger.info(f"3. Run this script again.\n")
            raise

    # Upload each DataFrame as a separate worksheet
    for ws_name, df in dataframes.items():
        # Sanitize worksheet name (max 100 chars, no special chars)
        ws_title = ws_name[:100].replace("/", "_").replace("\\", "_")
        
        # Replace NaN with empty string
        df = df.fillna("")
        
        try:
            # Try to get existing worksheet
            try:
                worksheet = sheet.worksheet(ws_title)
                worksheet.clear()
                logger.info(f"Cleared existing worksheet: '{ws_title}'")
            except gspread.WorksheetNotFound:
                worksheet = sheet.add_worksheet(
                    title=ws_title, 
                    rows=max(len(df) + 10, 100), 
                    cols=max(len(df.columns), 10)
                )
                logger.info(f"Created new worksheet: '{ws_title}'")
            
            # Prepare data
            data = [df.columns.values.tolist()] + df.values.tolist()
            
            # Upload
            worksheet.update(values=data, range_name="A1")
            logger.info(f"Uploaded {len(df)} rows to '{ws_title}'")
            
        except Exception as e:
            logger.error(f"Error uploading '{ws_title}': {e}")
    
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.id}"
    logger.info(f"✅ Upload complete! URL: {spreadsheet_url}")
    return spreadsheet_url
