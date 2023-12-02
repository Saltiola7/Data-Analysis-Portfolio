# Job Board Web Scraper
This automated web scraper ETL pipeline extracts data from 3 different websites. Tarjouspalvelu is a SPA (single page applicatino), which I navigate with Playwright and use JavaScript functions to mine the key data out from the page. Hankintailmoitukset only requires a CSV file to be loaded from the same URL and extracting the key data from it is much simpler. Kuntarekry is a static website that is handled simply with beautifulsoup.

For the automation I first setup Airflow in docker but swapped in the to Prefect as it seemed more modern way to orchestrate data and it also fitted better the budget of the project. However I did get the Airflow running perfectly fine before the transition and can provide the docker image for it.

# flow.py

Orchestrates and automates the whole ETL

# load.py

Does few last transformations that could be implemented into the extrators as well later on, after which it loads the data to parse server application database. 

# scraper_...py
These are the scraper orchestrators for each website.
Hankintailmoitukset and Tarjouspalvelu are modularized into their folders for better maintenance and readibility.

# utils.py
Commonly used functions are consolidated here, some of them are leftovers to be deleted.

# Other
after_search.png and dropdown.png are just screenshots that are taken at key moment in Tarjouspalvelu website as there is a banner complicating the process, which required additional handling. Ultimately I fixed the banner by also capturing html before timeout, which reveals the dynamically loaded banner element.

archive/combined_jobs.json
This is a sample of the kind of data that is outputted.

# Testing the script
Add your back4app credentials and target class to flow.py
Initialize Prefect.io in your environment
Run flow.py