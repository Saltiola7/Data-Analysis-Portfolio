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

def save_to_postgres(data):
    db_url = os.getenv('AIRFLOW__DATABASE__SQL_ALCHEMY_CONN')
    if not db_url:
        logging.error("Database URL not found in environment variables.")
        return

    engine = create_engine(db_url)
    metadata = MetaData()
    job_data_table = Table('job_data', metadata,
                           Column('unique_id', String, primary_key=True),
                           Column('extraction_time', TIMESTAMP),
                           Column('title', String),
                           Column('location', String),
                           Column('url', String))
    metadata.create_all(engine)

    processed = 0
    duplicates = 0
    with engine.connect() as connection:
        for entry in data:
            stmt = insert(job_data_table).values(**entry)
            do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=['unique_id'])
            result = connection.execute(do_nothing_stmt)

            if result.rowcount == 0:
                duplicates += 1
            else:
                processed += 1

    logging.info(f"New records added: {processed}, Duplicates skipped: {duplicates}")

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

# Back4app connection

def save_to_back4app(data):
    app_id = os.getenv('BACK4APP_APP_ID')
    api_key = os.getenv('BACK4APP_API_KEY')
    if not app_id or not api_key:
        logging.error("Back4App credentials not found in environment variables.")
        return

    headers = {
        "X-Parse-Application-Id": app_id,
        "X-Parse-REST-API-Key": api_key,
        "Content-Type": "application/json"
    }

    base_url = "https://parseapi.back4app.com/classes/YourClassName"  # Replace with your class name
    processed = 0
    errors = 0

    for entry in data:
        try:
            response = requests.post(base_url, headers=headers, data=json.dumps(entry))
            if response.status_code == 201:
                processed += 1
            else:
                logging.error(f"Error saving data: {response.text}")
                errors += 1
        except Exception as e:
            logging.error(f"Exception occurred: {e}")
            errors += 1

    logging.info(f"Processed: {processed}, Errors: {errors}")