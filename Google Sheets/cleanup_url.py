import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

# Use the correct path to your service account key file
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/tis/Dendron/notes/dev/Sheets/leadsgorilla333-bba6d85e58b9.json', scope)
client = gspread.authorize(creds)

# Open the Spreadsheet using its URL
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1SkrRjBeC7_r2yoT7LEWyIByjjmlwkHEfLvYWNdjadQI/edit#gid=762779400'
spreadsheet = client.open_by_url(spreadsheet_url)

print("Opened the spreadsheet.")

# Get all data from the Merged_Sheet
worksheet = spreadsheet.worksheet("Merged_Sheet")
data = worksheet.get_all_values()
df = pd.DataFrame(data)
df.columns = df.iloc[0]
df = df.iloc[1:]

print("Loaded the data from the Merged_Sheet into a DataFrame.")

# Add 'https://' to the beginning of each URL in 'Website' column, if it's not already present
df['Website'] = df['Website'].apply(lambda url: 'https://' + url if urlparse(url).scheme == '' and url != 'N/A' else url)

print("Added 'https://' to the beginning of each URL in the 'Website' column.")

# Create a list of cell objects to batch update
cell_list = []
for i, website in enumerate(df['Website'].values.tolist(), start=2):  # start=2 because rows are 1-indexed and we skip the header row
    cell = gspread.Cell(row=i, col=df.columns.get_loc('Website') + 1, value=website)  # columns are also 1-indexed
    cell_list.append(cell)

# Batch update the 'Website' column in the worksheet
worksheet.update_cells(cell_list)

print("Updated the 'Website' column in the worksheet with the updated URLs.")