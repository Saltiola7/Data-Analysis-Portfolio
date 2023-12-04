import requests
import csv
import time  # to timestamp our logs

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

    print(f"{time.ctime()}: Starting product extraction...")

    while True:
        print(f"{time.ctime()}: Sending request to Shopify API...")
        response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)

        print(f"{time.ctime()}: Received response. Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'data' in data:
                print(f"{time.ctime()}: Processing products...")

                for product_edge in data['data']['products']['edges']:
                    product_title = product_edge['node']['title']

                    for variant_edge in product_edge['node']['variants']['edges']:
                        variant_title = variant_edge['node']['title']
                        inventory_quantity = variant_edge['node']['inventoryQuantity']

                        writer.writerow([product_title, variant_title, inventory_quantity])

                print(f"{time.ctime()}: Processed batch of products.")

                if not data['data']['products']['pageInfo']['hasNextPage']:
                    print(f"{time.ctime()}: No more products to process. Exiting...")
                    break

            else:
                print(f"{time.ctime()}: 'data' key not in response. Exiting...")
                break
        else:
            print(f"{time.ctime()}: Received a non-200 status code. Exiting...")
            break

print(f"{time.ctime()}: Data extracted to products_inventory.csv")
