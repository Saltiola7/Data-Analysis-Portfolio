from prefect import flow, task
import scraper_kuntarekry
import scraper_tarjouspalvelu
import scraper_hankintailmoitukset
import load

@task
def scrape_kuntarekry_task():
    return scraper_kuntarekry.main()

@task
def scrape_tarjouspalvelu_task():
    return scraper_tarjouspalvelu.main()

@task
def scrape_hankintailmoitukset_task():
    return scraper_hankintailmoitukset.main()

@task
def load_jobs_task(combined_data):
    load.load_jobs(combined_data)

@flow(name="polqoy_scraper")
def scraper_flow():
    kuntarekry_result = scrape_kuntarekry_task()
    tarjouspalvelu_result = scrape_tarjouspalvelu_task()
    hankintailmoitukset_result = scrape_hankintailmoitukset_task()

    combined_data = kuntarekry_result + tarjouspalvelu_result + hankintailmoitukset_result

    load_jobs_task(combined_data)

if __name__ == "__main__":
    scraper_flow()
