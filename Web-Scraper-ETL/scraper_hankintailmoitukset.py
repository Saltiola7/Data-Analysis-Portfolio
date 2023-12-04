import os
from hankintailmoitukset import browser_actions
from hankintailmoitukset import csv_manipulation

def main():
    # Download CSV file
    csv_file_path = browser_actions.download_csv_from_hankintailmoitukset()

    # Process the CSV file and generate URLs
    job_listings = csv_manipulation.process_csv(csv_file_path)

    # Return the processed job listings
    return job_listings

if __name__ == "__main__":
    main()
