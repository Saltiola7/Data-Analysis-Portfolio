from utils import generate_objectId

# Extract job listings from the page
def extract_job_listings(page):
    job_listings = page.query_selector_all('a.tp-list__row')
    jobs = []
    for job_listing in job_listings:
        job = extract_job_details(page, job_listing)
        jobs.append(job)
    return jobs

# Extract details of a single job listing
def extract_job_details(page, job_listing):
    ### Publish date
    extract_publish_date_js = """
    (element) => {
    let dateDivs = Array.from(element.querySelectorAll('.xl-order-3'));
    for (let div of dateDivs) {
        if (div.textContent.includes('Julkaisuaika')) {
            let dateSpan = div.querySelector('span');
            if (dateSpan) {
                let date = dateSpan.textContent.trim();
                let dateParts = date.split('.');
                if (dateParts.length !== 3) {
                    console.error(`Unexpected date format: ${date}`);
                    return null;
                }
                let [day, month, year] = dateParts;
                day = day.padStart(2, '0');
                month = month.padStart(2, '0');
                return `${day}${month}${year}`;
            }
        }
    }
    return null;
}

    """
    extract_due_date_js = """
    (element) => {
        let dateDivs = Array.from(element.querySelectorAll('.xl-order-3'));
        for (let div of dateDivs) {
            if (div.textContent.includes('Määräaika')) {
                let dateSpan = div.querySelector('span');
                if (dateSpan) {
                    let date = dateSpan.textContent.trim();
                    let dateParts = date.split('.');
                    if (dateParts.length !== 3) {
                        console.error(`Unexpected date format: ${date}`);
                        return null;
                    }
                    let [day, month, year] = dateParts;
                    day = day.padStart(2, '0');
                    month = month.padStart(2, '0');
                    return `${day}${month}${year}`;
                }
            }
        }
        return null;
    }

    """
    extract_job_description_js = """
    (element) => {
        let descriptionSpan = element.querySelector('.xl-order-3 span[title]');
        if (descriptionSpan) {
            return descriptionSpan.getAttribute('title').trim();
        }
        return null;
    }
    """
    extract_job_title_js = """
    (element) => {
        let titleSpan = element.querySelector('.tp-list__column--name .text-bold');
        if (titleSpan) {
            return titleSpan.textContent.trim();
        }
        return null;
    }
    """
    extract_organization_js = """
    (element) => {
        let label = element.querySelector('.tp-list__column--hy div.label-xl-aria');
        if (label && label.nextSibling && label.nextSibling.nodeType === Node.TEXT_NODE) {
            return label.nextSibling.textContent.trim();
        }
        return null;
    }
    """
    extract_job_url_js = """
        (element) => {
            const baseUrl = 'https://tarjouspalvelu.fi';
            let slug = element.getAttribute('href').trim();
            return baseUrl + slug;
        }
    """
    
## Extraction
    publish_date = page.evaluate(extract_publish_date_js, job_listing)
    due_date = page.evaluate(extract_due_date_js, job_listing)  # Extract the due date
#    job_description = page.evaluate(extract_job_description_js, job_listing)
    job_title = page.evaluate(extract_job_title_js, job_listing)
    organization_name = page.evaluate(extract_organization_js, job_listing)
    job_url = page.evaluate(extract_job_url_js, job_listing)

## Generate objectId
    objectId = generate_objectId(job_title, job_url)

## Return job details
    return {
        "publish_date": publish_date,
        "due_date": due_date,  # Include the due date in the returned dictionary
#        "job_description": job_description,
        "job_title": job_title,
        "organization_name": organization_name,
        "job_url": job_url,
        "objectId": objectId,
        "source": "tarjouspalvelu"
    }