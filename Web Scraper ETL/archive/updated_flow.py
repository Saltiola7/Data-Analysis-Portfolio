
from prefect import flow, task
import requests
import json
import scraper_kuntarekry
import scraper_tarjouspalvelu
import scraper_hankintailmoitukset
from load import process_and_upload_jobs  # Importing the new module

# Parse Server/Back4App API credentials
application_id = '2rujmsH23xhOQITWeCYY1OcxMMMPPUgf5c3T2g3j'
rest_api_key = 'BI4nuc2zD4gez1iQ5aqH03llfv2Pv7NXVwNii2LL'
base_url = 'https://parseapi.back4app.com/classes/testClass'

headers = {
    "X-Parse-Application-Id": application_id,
    "X-Parse-REST-API-Key": rest_api_key,
    "Content-Type": "application/json"
}

# Assuming there are functions or tasks that scrape data and return it in a suitable format
# Example function call to scrape data
@task
def get_scraped_data():
    # Example of how scraped data might be gathered
    scraped_data = []
    # Add data from each scraper to the list
    scraped_data.extend(scraper_kuntarekry.scrape())
    scraped_data.extend(scraper_tarjouspalvelu.scrape())
    scraped_data.extend(scraper_hankintailmoitukset.scrape())
    return scraped_data

@flow
def main_flow():
    scraped_data = get_scraped_data()  # Get scraped data
    process_and_upload_jobs(scraped_data)  # Process and upload data using the new module

if __name__ == "__main__":
    main_flow()
