import requests
import json
import csv
import time

# Your Shopify Admin API access token
ACCESS_TOKEN = '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'

# Your Shopify store's GraphQL endpoint
GRAPHQL_URL = 'https://gorillawearfi.myshopify.com/admin/api/2022-07/graphql.json'

# Initialize CSV file
with open('active_shopify_products_graphql.csv', 'w', newline='') as csvfile:
    fieldnames = ['Product ID', 'Product Title', 'Product Type', 'Total Inventory']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    product_cursor = None

    while True:
        print("Sending request to Shopify API...")

        # GraphQL query for products
        product_query = '''
        {{
          products(first: 10, after: {product_cursor}, query:"published_status:published") {{
            pageInfo {{
              hasNextPage
            }}
            edges {{
              cursor
              node {{
                id
                title
                productType
                variants(first: 10) {{
                  pageInfo {{
                    hasNextPage
                  }}
                  edges {{
                    cursor
                    node {{
                      id
                      title
                      inventoryQuantity
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        '''.format(product_cursor=json.dumps(product_cursor) if product_cursor else "null")

        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': ACCESS_TOKEN
        }

        product_response = requests.post(GRAPHQL_URL, json={'query': product_query}, headers=headers)

        if product_response.status_code == 200:
            print("Received 200 OK from Shopify API.")
            product_data = product_response.json()

            if 'errors' in product_data:
                print("Received errors in response.")
                error_code = product_data.get('extensions', {}).get('code', 'UNKNOWN')
                print(f"Received unexpected error code: {error_code}.")
                break

            if 'data' in product_data and 'products' in product_data['data']:
                products = product_data['data']['products']['edges']
                has_next_page = product_data['data']['products']['pageInfo']['hasNextPage']

                for product_edge in products:
                    product_node = product_edge['node']
                    product_id = product_node['id'].split('/')[-1]
                    product_type = product_node['productType']
                    total_inventory = 0

                    # Sum up inventory for all variants
                    variants = product_node['variants']['edges']
                    for variant_edge in variants:
                        total_inventory += variant_edge['node']['inventoryQuantity']

                    if total_inventory > 0:
                        writer.writerow({'Product ID': product_id, 'Product Title': product_node['title'],
                                         'Product Type': product_type, 'Total Inventory': total_inventory})
                        print(f"Processed Product ID {product_id} with Total Inventory {total_inventory}")

                if has_next_page:
                    product_cursor = products[-1]['cursor']
                else:
                    break
            else:
                print("Unexpected response format:", product_data)
                break
        else:
            print(f"Failed to fetch data, status code: {product_response.status_code}")
            break

        time.sleep(2)  # Sleep for 2 seconds to reduce the chance of rate limiting
