import requests
import json
import csv

# Replace with your actual Admin API access token
ACCESS_TOKEN = 'ACCESS_TOKEN'

# Your Shopify store's GraphQL endpoint
GRAPHQL_URL = 'GRAPHQL_URL'

# GraphQL query string
query = '''
{
  products(first: 250) {
    edges {
      node {
        id
        title
      }
    }
  }
}
'''

# HTTP headers
headers = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': ACCESS_TOKEN
}

# Execute the query
response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)
if response.status_code == 200:
    result_data = response.json()
    products = result_data['data']['products']['edges']

    # Initialize CSV file
    with open('shopify_products_graphql.csv', 'w', newline='') as csvfile:
        fieldnames = ['Product ID', 'Product Title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write header

        for edge in products:
            product_node = edge['node']
            writer.writerow({'Product ID': product_node['id'], 'Product Title': product_node['title']})

else:
    print("Failed to fetch data:", response.content)
