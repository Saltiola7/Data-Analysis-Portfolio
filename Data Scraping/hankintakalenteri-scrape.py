import requests
import json
import logging
from bs4 import BeautifulSoup
from hashlib import md5

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_unique_id(date, unit, link):
    """ Generate a unique ID based on procurement details """
    return md5(f"{date}{unit}{link}".encode()).hexdigest()

def fetch_html(url, timeout=60):
    """ Fetch HTML content from the URL """
    logging.info("Fetching HTML content from the URL...")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching the URL: {e}")
        return None

def parse_html(html_content):
    """ Parse the HTML content and extract procurement details """
    logging.info("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    procurements = []
    errors = []

    for h3 in soup.find_all('h3'):
        try:
            title_link = h3.find('a')
            if not title_link:
                logging.warning("Title link not found in section.")
                continue

            link = 'https://www.hankintakalenteri.fi' + title_link['href']
            form_rows = h3.find_all_next('div', class_='form-row-input', limit=2)

            if len(form_rows) != 2:
                logging.warning("Not enough form rows found.")
                continue

            date = form_rows[0].get_text().strip()
            unit = form_rows[1].get_text().strip()

            logging.info(f"Processing procurement: {unit} on {date}")

            procurement_id = generate_unique_id(date, unit, link)
            procurement_data = {
                "objectId": procurement_id,
                "Julkaisupäivä": date,
                "Hankintayksikkö": unit,
                "Link": link
            }
            procurements.append(procurement_data)
        except Exception as e:
            errors.append(f"Error processing a procurement section: {e}")
            continue

    return procurements, errors

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
    url = 'https://www.hankintakalenteri.fi/Hankintapaatos/Hankintapaatokset'
    json_file_path = '/Users/tis/Dendron/notes/Vesa/scraped_data.json'

    html_content = fetch_html(url)
    if html_content:
        procurements, errors = parse_html(html_content)

        if procurements:
            save_to_json({"results": procurements}, json_file_path)
        else:
            logging.info("No procurements found to save.")

        if errors:
            logging.error("Errors encountered:")
            for error in errors:
                logging.error(error)

if __name__ == "__main__":
    main()
