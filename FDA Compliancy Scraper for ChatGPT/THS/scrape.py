import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Function to save HTML content to a file
def save_html_file(page_url, folder):
    print(f"Attempting to save {page_url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(page_url, headers=headers)
    
    if response.status_code == 200:
        print(f"Successfully retrieved {page_url}")
        content = response.text
        
        # Extract the last part of the URL to use as the file name
        parsed_url = urlparse(page_url)
        file_name = parsed_url.path.rstrip('/').split('/')[-1] or 'index'
        file_name += '.html'
        
        file_path = os.path.join(folder, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"Failed to retrieve {page_url}")
        print(f"HTTP Status Code: {response.status_code}")

# Recursive function to crawl the website
def crawl_website(start_url, folder, visited=None):
    if visited is None:
        visited = set()
    
    if start_url in visited:
        return
    
    visited.add(start_url)
    
    print(f"Crawling: {start_url}")
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    save_html_file(start_url, folder)
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(start_url, headers=headers)
    if response.status_code != 200:
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        next_url = urljoin(start_url, link)
        if next_url.startswith(start_url):
            time.sleep(1)  # Adding a 1-second delay between requests
            crawl_website(next_url, folder, visited)

# Starting URL and folder to save HTML files
start_url = "https://truehempscience.com/"
folder = "/Users/tis/Dendron/notes/dev/THS/Output"

# Start the crawl
crawl_website(start_url, folder)
