import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Use the correct path to your service account key file
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/tis/Dendron/notes/dev/Sheets/leadsgorilla333-bba6d85e58b9.json', scope)
client = gspread.authorize(creds)

# Open the Spreadsheet using its URL
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1SkrRjBeC7_r2yoT7LEWyIByjjmlwkHEfLvYWNdjadQI/edit#gid=762779400'
spreadsheet = client.open_by_url(spreadsheet_url)

# Initialize an empty DataFrame
all_data = pd.DataFrame()

# Loop through each worksheet in the spreadsheet
for i, worksheet in enumerate(spreadsheet.worksheets()):
    print(f"Processing worksheet {i+1} out of {len(spreadsheet.worksheets())}: {worksheet.title}")

    # Get all values from the worksheet
    data = worksheet.get_all_values()

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Set the column names to the first row of data
    df.columns = df.iloc[0]

    # Drop the first row of data since it's now the column names
    df = df.iloc[1:]

    # Add a new column with the original sheet name
    df['Original Sheet'] = worksheet.title

    # Append the DataFrame to the all_data DataFrame
    all_data = pd.concat([all_data, df], axis=0, ignore_index=True)

# Create a new worksheet and add all the data to it
new_worksheet = spreadsheet.add_worksheet(title="Merged_Sheet", rows="1000", cols="20")
new_worksheet.insert_rows(all_data.values.tolist())

print("All worksheets have been successfully merged into a new worksheet.")