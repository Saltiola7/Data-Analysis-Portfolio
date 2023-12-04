import csv
import json
from datetime import datetime
import re

# Define the URL schemas
procurement_url_schema = "https://www.hankintailmoitukset.fi/fi/public/procurement/{procurement}/notice/{objectId}/overview"
procedure_url_schema = "https://www.hankintailmoitukset.fi/fi/public/procedure/{procedure}/enotice/{objectId}/"

def generate_url(row):
    objectId, publish_date, procurement, procedure = row

    objectId_for_procedure = objectId.split('-')[-1]

    if procurement != '0':
        return procurement_url_schema.format(procurement=procurement, objectId=objectId)
    else:
        return procedure_url_schema.format(procedure=procedure, objectId=objectId_for_procedure)


def format_date(date_str):
    # Return None if date_str is empty
    if not date_str:
        return None

    # Extract the year, month, and day using a regex
    match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
    if match:
        date = datetime.strptime(match.group(1), '%Y-%m-%d')
        return date.strftime('%d%m%Y')
    else:
        raise ValueError(f"time data '{date_str}' does not start with a date in the format 'yyyy-mm-dd'")

def process_csv(file_path):
    job_listings = []
    encodings = ['utf-8', 'ISO-8859-1', 'Windows-1252']  # List of encodings to try

    for encoding in encodings:
        try:
            with open(file_path, newline='', encoding=encoding) as csvfile:
                # Specify the semicolon as the delimiter
                reader = csv.DictReader(csvfile, delimiter=';')
                
                for row in reader:
                    due_date = format_date(row["Määräaika (UTC)"].strip())
                    publish_date = format_date(row["Julkaistu (UTC)"].strip())
                    job_url = generate_url([row["Ilmoituksen Hilma-numero"].strip(), 
                                            publish_date, 
                                            row["Hankintaprojektin tunniste"].strip(), 
                                            row["Hankintamenettelyn tunniste"].strip()])
                    job_details = {
                        "publish_date": publish_date,
                        "due_date": due_date,
                        "job_title": row["Nimi (fi)"].strip(),
                        "organization_name": row["Organisaation nimi (fi)"].strip(),
                        "job_url": job_url,
                        "objectId": row["Ilmoituksen Hilma-numero"].strip(),
                        "source": "hankintailmoitukset"
                    }
                    job_listings.append(job_details)
            break  # Break the loop if no error was raised
        except UnicodeDecodeError:
            continue  # Try the next encoding in case of a UnicodeDecodeError
        except KeyError:
            # Print the available column names if KeyError is encountered
            print(f"Available columns in the CSV: {reader.fieldnames}")
            raise

    return job_listings
