import requests
import json
import logging
from bs4 import BeautifulSoup
from hashlib import md5

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_unique_id(title, location, link):
    """ Generate a unique ID based on job details """
    return md5(f"{title}{location}{link}".encode()).hexdigest()

def fetch_html(url):
    """ Fetch HTML content from the URL """
    logging.info("Fetching HTML content from the URL...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching the URL: {e}")
        return None

def parse_html(html_content):
    """ Parse the HTML content and extract job details """
    logging.info("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    errors = []

    job_sections = soup.find_all('li', class_='border-top mb-0')
    logging.info(f"Found {len(job_sections)} job sections.")

    for job_section in job_sections:
        try:
            link_tag = job_section.find('a', class_='anim anim--bg align-items-center d-flex py-16 px-8 px-md-16')
            if not link_tag:
                logging.warning("Link tag not found in job section.")
                continue

            title = link_tag.find('span', class_='subtitle-m text-matisse font-weight-bold d-block mb-0').get_text().strip()
            location = link_tag.find('span', class_='d-block text-zodiac body-m mb-0').get_text().strip()
            link = link_tag['href']

            logging.info(f"Processing job: {title} in {location}")

            job_id = generate_unique_id(title, location, link)
            job_data = {
                "objectId": job_id,
                "title": title,
                "Location": location,
                "Link": link,
                "IsNewLast7days": False, # Determine logic based on your criteria
                "createdat": "", # Add logic for timestamp
                "updatedat": "" # Add logic for timestamp
            }
            jobs.append(job_data)
        except Exception as e:
            errors.append(f"Error processing a job section: {e}")
            continue

    return jobs, errors

def save_to_json(data, file_path):
    """ Save the scraped data to a JSON file """
    logging.info("Saving data to JSON file...")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("Data saved to JSON file successfully.")
    except Exception as e:
        logging.error(f"Failed to save data to JSON: {e}")

def main():
    url = 'https://www.terveystalo.com/fi/yhtio/toihin-terveystaloon/avoimet-tyopaikat/avoimet-tyopaikat-laakarit'
    json_file_path = '/Users/tis/Dendron/notes/Vesa/scraped_data.json'

    html_content = fetch_html(url)
    if html_content:
        jobs, errors = parse_html(html_content)

        if jobs:
            save_to_json({"results": jobs}, json_file_path)
        else:
            logging.info("No jobs found to save.")

        if errors:
            logging.error("Errors encountered:")
            for error in errors:
                logging.error(error)

    # If pagination is needed in future, add logic here

if __name__ == "__main__":
    main()
