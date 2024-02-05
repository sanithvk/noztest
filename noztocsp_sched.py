import requests
import os
import logging
import zope.interface
import interface
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
        address_space_data = self.address_space()

        # Call the env_value method with the user input and address_space_data
        self.env_value(ip_space, address_space_data)

        # Call the authenticate_and_fetch_assets method
        self.authenticate_and_fetch_assets()
        
  
    def csp(self,url, method='GET', data=None):
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
            content = [json.loads(dat) for dat in response.text.split('\n') if dat.strip()]
            return content
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

  
    def fetch_ip_spaces(self):
        url = "https://csp.infoblox.com/api/ddi/v1/ipam/ip_space"
        return self.csp(url)

   
    def address_space(self):
        data = self.fetch_ip_spaces()
        return {spaces.get('name'): spaces.get('id').split("ip_space/")[1] for spaces in data[0].get('results', [])}

    
    def env_value(self,name, address_space_data):
        if name in address_space_data:
            print(address_space_data[name])
        else:
            print(f"No matching 'id' found for the given name: {name}")

    
    def authenticate_and_fetch_assets(self):
        key_name = os.getenv('key_name')
        key_token = os.getenv('key_token')
        ip_space = os.getenv('ip_space_name')
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

        if response.status_code == 200:
            auth_header = response.headers.get('Authorization')
            bearer_token = auth_header.split('Bearer ')[1] if auth_header and auth_header.startswith('Bearer') else None

            if bearer_token:
                alerts_url = "https://nozomi-sales-engineering-tpnovovq.customers.us1.vantage.nozominetworks.io/api/v1/assets"
                headers = {'Authorization': f'Bearer {bearer_token}', 'accept': '*/*'}

                response = requests.get(alerts_url, headers=headers)

                if response.status_code == 200:
                    content = response.json()
                    address_space_data = self.address_space()

                    for item in content.get('data', []):
                        attributes = item.get('attributes', {})
                        id_value = item.get('id', [])
                        device = attributes.get('name', '')
                        ip_list = attributes.get('ip', [])
                        mac_address_list = attributes.get('mac_address', [])
                        ip = ip_list[0] if ip_list else ''
                        mac_address = mac_address_list[0] if mac_address_list else ''
                        vendor = attributes.get('vendor', [])
                        serial = attributes.get('serial_number', [])
                        time = attributes.get('last_activity_time', [])

                        data_post = {
                            "address": ip,
                            "comment": "Assets from Nozomi",
                            "space": "ipam/ip_space/" + address_space_data[ip_space],
                            "tags": {
                                "Device_name": device,
                                "Mac": mac_address,
                                "id": id_value,
                                "Serial_num": serial,
                                "Vendor": vendor
                            }
                        }
                        
                    
                    
                        result_post = self.csp("https://csp.infoblox.com/api/ddi/v1/ipam/address", method='POST', data=data_post)
            
                else:

                    print(f"Request failed with status code {response.status_code}")
            else:
                print("Bearer token not found in the response")
        else:
            print(f"Request failed with status code {response.status_code}")
    print("end of functions") 
    print("starting functions")      




