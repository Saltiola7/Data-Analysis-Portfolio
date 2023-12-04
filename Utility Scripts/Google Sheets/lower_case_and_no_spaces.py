import os
from dotenv import load_dotenv
import gspread

# Load environment variables
load_dotenv('/Users/tis/Dendron/notes/dev/Sheets/.env')

# Authenticate with the Google Sheets API
gc = gspread.service_account(filename=os.getenv('SERVICE_ACCOUNT_KEY_PATH'))

# Open the spreadsheet
spreadsheet = gc.open_by_url(os.getenv('SPREADSHEET_URL'))

# Select the first worksheet
worksheet = spreadsheet.get_worksheet(0)

# Read the first row to get the column headers
headers = worksheet.row_values(1)

# Convert headers to lowercase and replace spaces with underscores
new_headers = [header.lower().replace(' ', '_') for header in headers]

# Update the first row with the new headers
worksheet.update('A1:L1', [new_headers])