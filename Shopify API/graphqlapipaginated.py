import requests
import json
import csv

# Your Shopify Admin API access token
ACCESS_TOKEN = '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'

# Your Shopify store's GraphQL endpoint
GRAPHQL_URL = 'https://gorillawearfi.myshopify.com/admin/api/2022-07/graphql.json'

# Initialize CSV file
with open('shopify_products_graphql.csv', 'w', newline='') as csvfile:
    fieldnames = ['Product ID', 'Product Title']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()  # Write header

    # Initial cursor as None
    cursor = None

    while True:  # Keep looping until break
        # GraphQL query string with dynamic "after" cursor for pagination
        query = '''
        {{
          products(first: 250, after: {cursor}) {{
            pageInfo {{
              hasNextPage
            }}
            edges {{
              cursor
              node {{
                id
                title
              }}
            }}
          }}
        }}
        '''.format(cursor=json.dumps(cursor) if cursor else "null")

        # HTTP headers
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': ACCESS_TOKEN
        }

        # Execute the query
        response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)

        if response.status_code == 200:
            result_data = response.json()
            if 'data' in result_data and 'products' in result_data['data']:
                products = result_data['data']['products']['edges']
                has_next_page = result_data['data']['products']['pageInfo']['hasNextPage']

                # Write to CSV
                for edge in products:
                    product_node = edge['node']
                    product_id = product_node['id'].split('/')[-1]  # Extract numerical ID from global ID
                    writer.writerow({'Product ID': product_id, 'Product Title': product_node['title']})

                # Check for next page
                if has_next_page:
                    cursor = products[-1]['cursor']  # last cursor for next iteration
                else:
                    break  # Exit loop if no more pages

            else:
                print("Unexpected response format:", result_data)
                break

        else:
            print("Failed to fetch data, status code:", response.status_code, "Response:", response.content)
            break
