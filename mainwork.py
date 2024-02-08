import requests
import os
import logging
import zope.interface
import interface
import datetime
from datetime import datetime
import time
from pprint import pprint
import json

log = logging.getLogger('infoblox_driver')

@zope.interface.implementer(interface.IScheduler)
class MyScheduler:
    def __init__(self):
        pass
    def schedule(self, context):
        # Log the current timestamp
        log.info("Current timestamp: {}".format(datetime.now()))

        # Fetch required environment variables
        key_name = os.getenv('key_name')
        key_token = os.getenv('key_token')
        csp_key = os.getenv('csp_key')
        ip_space = os.getenv('ip_space_name')

        # Log fetched environment variables
        log.info("Key Name: %s", key_name)
        log.info("Key Token: %s", key_token)
        log.info("CSP Key: %s", csp_key)
        log.info("IP Space: %s", ip_space)

        # Fetch address space data
        self.address_space()

        # Call the env_value method with the user input and address_space_data
        #self.post_assets()

        # Call the authenticate_and_fetch_assets method
        self.authenticate_and_fetch_assets()
        
  
    def authenticate_and_fetch_assets(self):
        key_name = os.getenv('key_name')
        key_token = os.getenv('key_token')
        sign_in_url = "https://nozomi-sales-engineering-tpnovovq.customers.us1.vantage.nozominetworks.io/api/v1/keys/sign_in"

        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json'
        }

        data = {
            'key_name': key_name,
            'key_token': key_token
        }

        response = requests.post(sign_in_url, json=data, headers=headers)
        #print("Authentication Response:", response.text)  # Print authentication response

        if response.status_code == 200:
            auth_header = response.headers.get('Authorization')
            bearer_token = auth_header.split('Bearer ')[1] if auth_header and auth_header.startswith('Bearer') else None
            #print("Bearer Token:", bearer_token)  # Print bearer token

            if bearer_token:
                base_url = "https://nozomi-sales-engineering-tpnovovq.customers.us1.vantage.nozominetworks.io/api/v1/assets"
                headers = {'Authorization': f'Bearer {bearer_token}', 'accept': '*/*'}
                all_assets = []

                page_number = 1
                while True:
                    response = requests.get(base_url, params={"sort[last_activity_time]": "desc", "page": page_number, "size": 25, "skip_total_count": "true", "include": "network_domain,site"}, headers=headers)
                    #print("Assets Response:", response.text)  # Print assets response
                    if response.status_code == 200:
                        content = response.json()
                        assets = content.get('data', [])
                        all_assets.extend(assets)

                        if len(assets) < 25:
                            break
                        page_number += 1
                    else:
                        log.error("Error: %s", response.status_code)
                        break

                log.info("Total assets retrieved: %d", len(all_assets))
                self.post_assets(all_assets)
            else:
                log.error("Bearer token not found in the response")
        else:
            log.error("Request failed with status code %s", response.status_code)

    def post_assets(self, assets):
        address_space_data = self.address_space()
        ip_space = os.getenv('ip_space_name')
        print(address_space_data[ip_space])

        for asset in assets:
            attributes = asset.get('attributes', {})
            id_value = asset.get('id', [])
            device = attributes.get('name', '')
            ip = attributes.get('ip', '')
            # Convert arrays to strings
            ip = ip[0] if isinstance(ip, list) and len(ip) > 0 else ip
            mac_address = attributes.get('mac_address', '')
            # Convert arrays to strings
            mac_address = mac_address[0] if isinstance(mac_address, list) and len(mac_address) > 0 else mac_address
            vendor = attributes.get('vendor', '')
            serial = attributes.get('serial_number', '')

            data_post = {
                "address": ip,
                "comment": "Assets from Nozomi",
                "space": f"ipam/ip_space/{address_space_data[ip_space]}",
                "tags": {
                    "Device_name": device,
                    "Mac": mac_address,
                    "id": id_value,
                    "Serial_num": serial,
                    "Vendor": vendor,
                }
            }

            result_post = self.csp("https://csp.infoblox.com/api/ddi/v1/ipam/address", method='POST', data=data_post)
            '''if result_post is None:
                print("Error: No response received")
            else:
                error_message = result_post.get('error', [{}])[0].get('message', '')
                if "cannot unmarshal array into Go value of type string" in error_message:
                    print("Data to be posted:", data_post)  # Print data_post when encountering the specific error
                print("Post Assets Result:", result_post)'''






    def csp(self, url, method='GET', data=None):
        csp_key = os.getenv('csp_key')

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'TOKEN ' + csp_key
        }

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            return response.json()
        else:
            log.error("Error: %s, %s", response.status_code, response.text)
            return None

    def address_space(self):
        data = self.fetch_ip_spaces()
        results = data.get('results', [])
        if not results:
            log.error("No IP spaces found")
            return {}
        
        address_spaces = {}
        for space in results:
            id_value = space.get('id')
            if id_value and "ip_space/" in id_value:
                space_name = space.get('name')
                space_id = id_value.split("ip_space/")[1]
                address_spaces[space_name] = space_id
            else:
                log.error("Invalid 'id' format for IP space: %s", space)
        
        return address_spaces
    


    def fetch_ip_spaces(self):
        url = "https://csp.infoblox.com/api/ddi/v1/ipam/ip_space"
        return self.csp(url)
        
                
        
         




