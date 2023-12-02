import requests
import json
from datetime import datetime
from prefect import get_run_logger

# Parse Server/Back4App API credentials
application_id = '2rujmsH23xhOQITWeCYY1OcxMMMPPUgf5c3T2g3j'
rest_api_key = 'BI4nuc2zD4gez1iQ5aqH03llfv2Pv7NXVwNii2LL'
base_url = 'https://parseapi.back4app.com/classes/ExternalJob'

headers = {
    "X-Parse-Application-Id": application_id,
    "X-Parse-REST-API-Key": rest_api_key,
    "Content-Type": "application/json"
}

# Initialize counters
jobs_loaded = 0
duplicates = 0
errors = 0

def load_jobs(jobs):
    """Load jobs to the server."""
    global jobs_loaded, duplicates, errors
    logger = get_run_logger()
    if jobs:
        for job in jobs:
            upload_job(job, logger)
    else:
        logger.warning("No jobs found in the scraped data.")

def convert_date(date_str):
    """Converts a date string in 'ddmmyyyy' format to ISO 8601 format."""
    if date_str in [None, 'Not specified']:
        return '2000-01-01T00:00:00Z'
    try:
        dt = datetime.strptime(date_str, '%d%m%Y')
        return dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    except ValueError as e:
        logger = get_run_logger()
        logger.error(f"Error converting date: {e}")
        return '2000-01-01T00:00:00Z'
    
def check_duplicate(uniqueId, logger):
    """Check if a job with the same uniqueId already exists on the server."""
    try:
        response = requests.get(base_url, headers=headers, params={"where": json.dumps({"uniqueId": uniqueId})})
        response.raise_for_status()
        return response.json()['results']
    except requests.RequestException as e:
        logger.error(f"Error checking for duplicate job {uniqueId}: {e}, Response: {e.response.text}")
        return []

def upload_job(job, logger):
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
    if check_duplicate(job['uniqueId'], logger):
        logger.info(f"Job {job['title']} already exists, skipping upload.")
        duplicates += 1
        return

    try:
        response = requests.post(base_url, headers=headers, data=json.dumps(job))
        response.raise_for_status()
        logger.info(f"Successfully uploaded job: {job['title']}")
        jobs_loaded += 1
    except requests.RequestException as e:
        logger.error(f"Error uploading job {job['title']}: {e}, Response: {e.response.text}")
        errors += 1

def main():
    global jobs_loaded, duplicates, errors
    logger = get_run_logger()
    jobs = [] # Replace with actual job data loading logic
    load_jobs(jobs)

    # Log summaries
    logger.info(f"Jobs loaded: {jobs_loaded}")
    logger.info(f"Duplicates: {duplicates}")
    logger.info(f"Errors: {errors}")

if __name__ == "__main__":
    main()
