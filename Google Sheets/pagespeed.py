import os
import time
from datetime import datetime
import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR) # This will set the logging level for googleapiclient.discovery_cache to ERROR, effectively suppressing warnings.
from dotenv import load_dotenv
from urllib.parse import urlparse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient import errors

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv('/Users/tis/Dendron/notes/dev/Sheets/.env')

# Use the environment variables
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv('SERVICE_ACCOUNT_KEY_PATH'), scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_url(os.getenv('SPREADSHEET_URL'))
worksheet = spreadsheet.get_worksheet(0)

# Read URLs from the third column of the worksheet, skipping the header
url_list = [url for url in worksheet.col_values(3)[1:] if url.strip() != 'N/A']

def is_valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])

def page_speed_test(url, strategy):
    logging.info(f"Testing URL: {url} with strategy: {strategy}")
    if not is_valid_url(url):
        logging.error(f"Invalid URL: {url}")
        return None

    # Build the service
    service = build('pagespeedonline', 'v5', developerKey=os.getenv('GOOGLE_API_KEY'))
    result = service.pagespeedapi().runpagespeed(url=url, strategy=strategy.upper()).execute()

    # Extract the scores
    performance_score = result['lighthouseResult']['categories']['performance']['score']
    speed_index = result['lighthouseResult']['audits']['speed-index']['numericValue'] / 1000
    return performance_score, speed_index

# Fetch all the data at once
data = worksheet.get_all_values()

for i, url in enumerate(url_list, start=2):  # start from 2 to match the row numbers in the worksheet
    if not url.strip():
        continue  # skip empty lines
    skip_mode = True

    # If skip mode is enabled and the cell for the test date is not empty, skip this row
    if 'skip_mode' in locals() and data[i-1][12]:  # -1 because list indices start at 0
        continue

    test_date = datetime.now().strftime('%Y-%m-%d')
    worksheet.update_cell(i, 13, test_date)

    for j, strategy in enumerate(['mobile', 'desktop'], start=0):  # start from 0 to match the column numbers in the worksheet
        try:
            scores = page_speed_test(url, strategy)
        except errors.HttpError as e:
            logging.error(f"An error occurred while testing URL: {url} with strategy: {strategy}. Error: {e}")
            continue
        if scores is not None:
            performance_score, speed_index = scores
            # Update the cell with the performance score
            worksheet.update_cell(i, 14 + j * 2, performance_score)
            # Update the cell with the speed index
            worksheet.update_cell(i, 15 + j * 2, speed_index)
            logging.info(f"Updated cell {chr(78 + j * 2)}{i} with {strategy} performance score {performance_score}")
            logging.info(f"Updated cell {chr(79 + j * 2)}{i} with {strategy} speed index {speed_index}")
        else:
            invalid_urls.append(url)
        logging.info(f"Sleeping for 1 second to respect rate limit")
        time.sleep(1)  # rate limit to 1 request per second

logging.info(f"Invalid URLs: {invalid_urls}")