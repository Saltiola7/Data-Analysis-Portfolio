import requests
import csv

# Replace these with your actual credentials
API_KEY = "API_KEY"
PASSWORD = "PASSWORD"

# The URL to your specific Shopify store
API_URL = "https://gorillawearfi.myshopify.com/admin/api/2022-07/products.json"

AUTH = (API_KEY, PASSWORD)

params = {
    "fields": "id,title",  # Fetching only id and title
    "limit": 250
}

response = requests.get(API_URL, auth=AUTH, params=params)

if response.status_code == 200:
    products = response.json()["products"]

    # Initialize CSV file
    with open('shopify_products.csv', 'w', newline='') as csvfile:
        fieldnames = ['Product ID', 'Product Title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write header

        for product in products:
            writer.writerow({'Product ID': product['id'], 'Product Title': product['title']})

else:
    print("Failed to fetch data:", response.content)
