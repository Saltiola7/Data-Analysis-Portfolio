from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
import asyncio
import logging

# Initialize the browser and context
def initialize_browser(playwright):
    browser = playwright.chromium.launch()
    context = browser.new_context(viewport={"width": 3840, "height": 2160})
    return browser, context

def attempt_close_banner(page):
    close_button_selector = ".leadinModal-close"
    try:
        # Wait for the close button to be visible and enabled
        page.wait_for_selector(close_button_selector, state="visible", timeout=5000)
        page.wait_for_selector(close_button_selector, state="enabled", timeout=5000)
        print("Banner detected, attempting to click the close button...")
        page.click(close_button_selector)
        print("Banner close button clicked.")
        page.wait_for_timeout(2000)
        print("Continuing after waiting for 2 seconds.")
    except TimeoutError:
        print("No banner detected.")

# Create a new page in the browser context
def create_page(context):
    return context.new_page()

# Navigate to the Tarjouspalvelu website
def navigate_to_tarjouspalvelu(page):
    page.goto("https://tarjouspalvelu.fi/", timeout=60000)
    page.wait_for_load_state('networkidle', timeout=60000)
    attempt_close_banner(page)

# Change the language of the website
def change_language(page):
    page.click("button.language-dropdown")
    page.is_visible('button[data-test-key="languageDropdown.finnish"]', timeout=60000)
    page.click('button[data-test-key="languageDropdown.finnish"]')

# Perform a search on the website

def perform_search(page):
    logging.info("Starting search...")
    try:
        logging.info("Clicking 'Lisää hakuehtoja' button...")
        page.click("button.btn:has-text('Lisää hakuehtoja')") # Lisää hakuehtoja
        logging.info("Checking visibility of '#hankintalaji-cb'...")
        page.is_visible('#hankintalaji-cb')
        logging.info("Clicking '#hankintalaji-cb'...")
        page.click('#hankintalaji-cb') # Hankintalaji
        dropdown_selector = 'div#hankintalajilista' 
        logging.info("Clicking dropdown selector...")
        page.click(dropdown_selector)
        logging.info("Navigating dropdown...")
        page.press(dropdown_selector, 'ArrowDown')
        page.press(dropdown_selector, 'ArrowDown')
        page.press(dropdown_selector, 'Enter')
        logging.info("Double clicking submit button...")
        page.dblclick('button[data-test-key="etusivuhaku.submitbtn"]')
        logging.info("Waiting for page to load...")
        page.wait_for_load_state('networkidle', timeout=10000)
        attempt_close_banner(page)
    except TimeoutError:
        logging.error("TimeoutError occurred. Capturing screenshot and HTML...")
        # Capture a screenshot when a TimeoutError occurs
        page.screenshot(path='timeout_screenshot.png')
        # Capture the HTML of the page
        html_content = page.content()
        with open('timeout_html.html', 'w') as f:
            f.write(html_content)
        raise  # Re-raise the exception after capturing the screenshot and HTML