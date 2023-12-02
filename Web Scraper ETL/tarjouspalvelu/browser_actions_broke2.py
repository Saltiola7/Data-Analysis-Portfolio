from playwright.sync_api import sync_playwright
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
    except TimeoutError:
        logging.error("TimeoutError occurred. Capturing screenshot and HTML...")
        page.screenshot(path='timeout_screenshot.png')
        html_content = page.content()
        with open('timeout_html.html', 'w') as f:
            f.write(html_content)
        raise
