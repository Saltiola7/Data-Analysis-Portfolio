import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from utils import generate_objectId, setup_logging

BASE_URL = "https://www.kuntarekry.fi"

def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching HTML: {e}")
        return None

def parse_html(html_content):
    return BeautifulSoup(html_content, 'html.parser')

def format_date(date):
    return date.strftime('%d%m%Y')

def extract_date_from_string(date_string):
    try:
        return datetime.strptime(date_string[:10], "%d.%m.%Y")
    except ValueError:
        return None

def parse_due_date(due_date_string):
    due_date = extract_date_from_string(due_date_string)
    if due_date:
        return format_date(due_date)
    return "Not specified"

def extract_job_data(job_entry):
    try:
        job_organization = job_entry.find('p', class_='job-organization').get_text(strip=True)
        job_title = job_entry.find('h3', class_='job-title').get_text(strip=True)
        job_url = job_entry['href']

        job_details = job_entry.find('p', class_='job-details')
        due_date_span = job_details.find('span', class_='text-blue') if job_details else None
        due_date = parse_due_date(due_date_span.get_text(strip=True)) if due_date_span else "Not specified"

        return {
            "objectId": generate_objectId(job_title, job_url),
            "publish_date": format_date(datetime.now()),
            "job_title": job_title,
            "organization_name": job_organization,
            "due_date": due_date,
            "job_url": BASE_URL + job_url,
            "source": "kuntarekry"
        }
    except Exception as e:
        logging.error(f"Error extracting job data: {e}")
        return None

def extract_jobs_from_page(soup):
    jobs = []
    for job_entry in soup.find_all('a', class_='link no-prefetch'):
        job_data = extract_job_data(job_entry)
        if job_data:
            jobs.append(job_data)
    return jobs

def find_next_page(soup):
    pagination_div = soup.find('div', class_='paginate sticky sticky-b0')
    next_page_link = pagination_div.find('a', class_='next') if pagination_div else None
    return next_page_link['href'] if next_page_link else None

def scrape_jobs(url):
    html_content = fetch_html(url)
    if html_content:
        soup = parse_html(html_content)
        jobs = extract_jobs_from_page(soup)
        next_page = find_next_page(soup)
        return jobs, next_page
    else:
        return [], None

def main():
    setup_logging()
    all_jobs = []
    next_page = "/fi/tyopaikat/laakarit"
    while next_page:
        jobs, next_page = scrape_jobs(BASE_URL + next_page)
        all_jobs.extend(jobs)
    return all_jobs  # Return the collected job data

if __name__ == "__main__":
    main()
