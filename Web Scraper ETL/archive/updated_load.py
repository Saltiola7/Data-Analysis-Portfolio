
import requests
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parse Server/Back4App API credentials
application_id = '2rujmsH23xhOQITWeCYY1OcxMMMPPUgf5c3T2g3j'
rest_api_key = 'BI4nuc2zD4gez1iQ5aqH03llfv2Pv7NXVwNii2LL'
base_url = 'https://parseapi.back4app.com/classes/testClass2'

headers = {
    "X-Parse-Application-Id": application_id,
    "X-Parse-REST-API-Key": rest_api_key,
    "Content-Type": "application/json"
}

# Initialize counters
jobs_loaded = 0
duplicates = 0
errors = 0

def convert_date(date_str):
    """Converts a date string in 'ddmmyyyy' format to ISO 8601 format."""
    if date_str in [None, 'Not specified']:
        return '2000-01-01T00:00:00Z'
    try:
        dt = datetime.strptime(date_str, '%d%m%Y')
        return dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    except ValueError as e:
        logging.error(f"Error converting date: {e}")
        return '2000-01-01T00:00:00Z'

def check_duplicate(uniqueId):
    """Check if a job with the same uniqueId already exists on the server."""
    try:
        response = requests.get(base_url, headers=headers, params={"where": json.dumps({"uniqueId": uniqueId})})
        response.raise_for_status()
        return response.json()['results']
    except requests.RequestException as e:
        logging.error(f"Error checking for duplicate job {uniqueId}: {e}, Response: {e.response.text}")
        return []

def upload_job(job):
    global jobs_loaded, duplicates, errors
    # Rename keys as per database schema
    job['title'] = job.pop('job_title', None)
    job['link'] = job.pop('job_url', None)
    job['location'] = job.pop('organization_name', 'Unknown')

    # Process date fields
    job['uniqueId'] = job.pop('objectId', None)
    job['publish_date'] = {"__type": "Date", "iso": convert_date(job.get('publish_date', ''))}
    job['due_date'] = {"__type": "Date", "iso": convert_date(job.get('due_date', ''))}

    # Check for duplicates
    if check_duplicate(job['uniqueId']):
        logging.info(f"Job {job['title']} already exists, skipping upload.")
        duplicates += 1
        return

    try:
        response = requests.post(base_url, headers=headers, data=json.dumps(job))
        response.raise_for_status()
        logging.info(f"Successfully uploaded job: {job['title']}")
        jobs_loaded += 1
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error uploading job {job['title']}: {e}, Response: {e.response.text}")
        errors += 1

def process_and_upload_jobs(jobs):
    global jobs_loaded, duplicates, errors
    for job in jobs:
        upload_job(job)
    # Print summaries
    print(f"Jobs loaded: {jobs_loaded}")
    print(f"Duplicates: {duplicates}")
    print(f"Errors: {errors}")
