import requests
import logging
import json
import os
from bs4 import BeautifulSoup
from hashlib import md5
from sqlalchemy import create_engine, Table, Column, String, TIMESTAMP, MetaData
from sqlalchemy.dialects.postgresql import insert

# Logging unused currently. Only in the main file.
def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_html(url, timeout=60):
    logging.info(f"Fetching HTML content from {url}...")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching the URL: {e}")
        return None

def parse_html(html_content):
    logging.info("Parsing HTML content...")
    return BeautifulSoup(html_content, 'html.parser')

# New utility functions
def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def check_environment_variable(var_name):
    """Check if an environment variable is set and return its value."""
    value = os.getenv(var_name)
    if value is None:
        log_error(f"Environment variable {var_name} not found.")
    return value

def generate_objectId(title, url):
    concatenated = title + url
    return md5(concatenated.encode()).hexdigest()

# Tarjouspalvelu

def save_job_listings_to_file(jobs, file_path='jobs.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=4, ensure_ascii=False)
        log_info(f"Job listings successfully saved to {file_path}")
    except Exception as e:
        log_error(f"Error saving job listings to file: {e}")

# hankintailmoitukset

def log_info(message):
    print(f"INFO: {message}")

def log_error(message):
    print(f"ERROR: {message}")
