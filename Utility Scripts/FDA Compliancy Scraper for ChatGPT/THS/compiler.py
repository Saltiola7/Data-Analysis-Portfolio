from bs4 import BeautifulSoup
import os
import pandas as pd

# Function to extract visible text from HTML file
def extract_text_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(['script', 'style']):
        # Remove all javascript and stylesheet code
        script.extract()
    return " ".join(soup.stripped_strings)

# Directory containing HTML files
html_folder = "/Users/tis/Downloads/markwhen"  # Replace with the actual path
output_csv = "compiled.csv"

# List to hold data
data_list = []

# Loop through each HTML file in the directory
for filename in os.listdir(html_folder):
    if filename.endswith(".html"):
        html_path = os.path.join(html_folder, filename)
        text_content = extract_text_from_html(html_path)
        
        # Append to data list
        data_list.append({
            'Filename': filename[:-5],  # Remove .html extension
            'TextContent': text_content
        })

# Convert list to DataFrame
df = pd.DataFrame(data_list)

# Save DataFrame to CSV
csv_path = os.path.join(html_folder, output_csv)
df.to_csv(csv_path, index=False)

# Displaying the head of the DataFrame for quick inspection
df.head()
