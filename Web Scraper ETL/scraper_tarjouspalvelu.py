from playwright.sync_api import sync_playwright
from tarjouspalvelu.browser_actions import initialize_browser, create_page, navigate_to_tarjouspalvelu, change_language, perform_search
from tarjouspalvelu.scraper import extract_job_listings

def main():
    try:
        with sync_playwright() as playwright:
            # Initialize browser and create a page
            browser, context = initialize_browser(playwright)
            page = create_page(context)

            # Navigate to the website and perform necessary actions
            navigate_to_tarjouspalvelu(page)
            change_language(page)
            perform_search(page)

            # Extract job listings from the page
            jobs = extract_job_listings(page)

            # Return the extracted job listings
            return jobs

    except Exception as e:
        print(f"An error occurred: {e}")
        return []  # Return an empty list in case of an error

# Context and browser are automatically closed when exiting the 'with' block

if __name__ == "__main__":
    main()
