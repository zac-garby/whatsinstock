import requests
from bs4 import BeautifulSoup
import json

product_id = "313610787" #Example product, 9 pack of Monster
url = 'https://www.tesco.com/groceries/en-GB/products/' + product_id

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
prod_json = soup.find('script', attrs={'type': 'application/discover+json'})

json_data = json.loads(prod_json.string)
product_data = json_data['mfe-orchestrator']['props']['apolloCache']['ProductType:'+product_id]

output_file_path = "product_infos/"+product_id+".json"

with open(output_file_path, 'w') as json_file:
    json.dump(product_data, json_file, indent=2)