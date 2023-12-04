import os
import time
import requests
import pandas as pd
from urllib.parse import urlparse

# Function to save HTML content to a file
def save_html_file(page_url, folder):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    if page_url.lower().endswith('.pdf'):
        print(f"Skipping PDF file: {page_url}")
        return
    
    try:
        print(f"Attempting to save {page_url}...")
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        
        content = response.text
        
        # Extract the URL slug for the filename
        parsed_url = urlparse(page_url)
        file_name = os.path.basename(parsed_url.path)
        
        if not file_name:
            file_name = os.path.basename(parsed_url.path.rstrip('/'))
        
        if not file_name:
            file_name = "index"
        
        file_name += ".html"
        
        file_path = os.path.join(folder, file_name)
        print(f"Saving to {file_path}...")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Saved successfully.")
        
    except Exception as e:
        print(f"Failed to retrieve or save {page_url}")
        print(e)
    
    # Adding a 3-second delay between requests
    time.sleep(3)


# Main function to crawl URLs from the CSV
def main():
    csv_path = "/Users/tis/Downloads/sitedocs.markwhen.com.csv"  # <--- Replace with the actual path to your CSV file
    folder = "/Users/tis/Downloads/markwhen"
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    try:
        urls_df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Failed to read CSV file: {e}")
        return
    
    for i, row in urls_df.iterrows():
        page_url = row['url']
        print(f"Processing URL {i+1}/{len(urls_df)}: {page_url}")
        save_html_file(page_url, folder)

if __name__ == "__main__":
    main()
