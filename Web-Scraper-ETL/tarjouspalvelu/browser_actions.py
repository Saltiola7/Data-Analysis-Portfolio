from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
import asyncio
import logging

# Initialize the browser and context
def initialize_browser(playwright):
    browser = playwright.chromium.launch()
    context = browser.new_context(viewport={"width": 3840, "height": 2160})
    return browser, context

# Create a new page in the browser context
def create_page(context):
    return context.new_page()

# Navigate to the Tarjouspalvelu website
def navigate_to_tarjouspalvelu(page):
    page.goto("https://tarjouspalvelu.fi/", timeout=60000)
    page.wait_for_load_state('networkidle', timeout=60000)

# Change the language of the website
def change_language(page):
    page.click("button.language-dropdown")
    page.is_visible('button[data-test-key="languageDropdown.finnish"]', timeout=60000)
    page.click('button[data-test-key="languageDropdown.finnish"]')

# Perform a search on the website
def perform_search(page):
    print("Starting the search process...")

    def attempt_close_banner():
        close_button_selector = ".leadinModal-close"
        if page.is_visible(close_button_selector, timeout=5000):
            print("Banner detected, attempting to click the close button...")
            page.click(close_button_selector)
            print("Banner close button clicked.")
            page.wait_for_timeout(2000)
            print("Continuing after waiting for 2 seconds.")

#    print("Injecting mutation observer to detect the banner...")
#    page.evaluate("""() => {
#        try {
#            const observer = new MutationObserver((mutations) => {
#                mutations.forEach(({ addedNodes }) => {
#                    addedNodes.forEach(node => {
#                        if (node.querySelector && node.querySelector('.leadinModal-close')) {
#                            node.querySelector('.leadinModal-close').click();
#                            console.log('Banner closed via mutation observer.');
#                        }
#                    });
#                });
#            });
#            observer.observe(document.body, { childList: true, subtree: true });
#        } catch (error) {
#            console.error('Error in mutation observer:', error.message);
#        }
#    }""")

    try:
        # Wait for the 'Lisää hakuehtoja' button and then click it
        page.wait_for_selector("button.btn:has-text('Lisää hakuehtoja')", timeout=10000)
        page.click("button.btn:has-text('Lisää hakuehtoja')")
        attempt_close_banner()



        # Ensure the dropdown is ready for interaction
        print("Checking if '#hankintalaji-cb' is visible...")
        if not page.wait_for_selector('#hankintalaji-cb', timeout=10000):
            raise Exception("'#hankintalaji-cb' not visible after 10 seconds")

        # Capture a screenshot
        print("Capturing screenshot...")
        page.screenshot(path='dropdown.png')

        # Check the checkbox
        print("Checking '#hankintalaji-cb' checkbox...")
        page.check('#hankintalaji-cb')
        # Select the dropdown option
        print("Selecting 'Terveydenhoito- ja sosiaalipalvelut' from the dropdown...")
        page.select_option('#hankintalajit-multiselect', '3')




        # Submit the search
        print("Submitting the search...")
        if not page.wait_for_selector('button[data-test-key="etusivuhaku.submitbtn"]', timeout=10000):
            raise Exception("'Submit' button not visible after 10 seconds")
        page.click('button[data-test-key="etusivuhaku.submitbtn"]')

        print("Waiting for the network to be idle...")
        print("Capturing screenshot...")
        page.screenshot(path='after_search.png')
        page.wait_for_load_state('networkidle', timeout=30000)
        print("Search completed.")
    except TimeoutError as e:
        print(f"An error occurred: {str(e)}")
        attempt_close_banner()
        print("Capturing a screenshot due to the timeout...")
        page.screenshot(path='timeout_screenshot.png')
        print("Saving the page HTML due to the timeout...")
        with open('timeout_page.html', 'w') as f:
            f.write(page.content())
        print("Raising the exception after handling the timeout...")
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Additional error handling for specific steps
