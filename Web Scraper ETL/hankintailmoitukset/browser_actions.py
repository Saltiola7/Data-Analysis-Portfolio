import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def go_to_page_and_download_csv(url, button_selector, download_path, file_name):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Create a new context with accept_downloads enabled
        context = await browser.new_context(accept_downloads=True)

        page = await context.new_page()
        await page.goto(url, wait_until="load")
        await page.click(button_selector)

        # Wait for the download to start and complete
        download = await page.wait_for_event('download')
        download_path = Path(download_path) / file_name
        await download.save_as(download_path)

        await browser.close()

        # Return the complete path of the downloaded file
        return str(download_path)

def download_csv_from_hankintailmoitukset():
    url = "https://www.hankintailmoitukset.fi/fi/search?q=&top=75&cpv=75000000&cpv=79000000&cpv=79611000&cpv=79620000&cpv=85000000&cpv=85121000&cpv=85121200&cpv=03000000&cpv=85121231&cpv=85141000&of=datePublished&od=desc&m=0&eformNr&oldNr&c"
    button_selector = 'button#downloadCsv'
    
    # Use the current directory of the script for the download path
    current_directory = os.path.dirname(os.path.realpath(__file__))
    download_path = current_directory
    file_name = 'hankintailmoitukset.csv'

    return asyncio.run(go_to_page_and_download_csv(url, button_selector, download_path, file_name))
