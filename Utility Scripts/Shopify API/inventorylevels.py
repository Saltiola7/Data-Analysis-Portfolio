import requests
import csv

# Your Shopify store details and access token
SHOPIFY_STORE = "SHOPIFY_STORE"
ACCESS_TOKEN = "ACCESS_TOKEN"  # Reset and put your new token here

GRAPHQL_URL = f"https://{SHOPIFY_STORE}/admin/api/2022-07/graphql.json"

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

# Define the GraphQL query
query = """
{
  products(first: 250) {
    pageInfo {
      hasNextPage
    }
    edges {
      node {
        title
        variants(first: 250) {
          edges {
            node {
              title
              inventoryQuantity
            }
          }
        }
      }
    }
  }
}
"""

# Request data and write to CSV
with open('products_inventory.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Product Title", "Variant Title", "Inventory Quantity"])

    while True:
        response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if 'data' in data:
                for product_edge in data['data']['products']['edges']:
                    product_title = product_edge['node']['title']
                    for variant_edge in product_edge['node']['variants']['edges']:
                        variant_title = variant_edge['node']['title']
                        inventory_quantity = variant_edge['node']['inventoryQuantity']

                        writer.writerow([product_title, variant_title, inventory_quantity])

                if not data['data']['products']['pageInfo']['hasNextPage']:
                    break

print("Data extracted to products_inventory.csv")
