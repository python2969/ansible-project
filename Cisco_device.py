#!/usr/bin/env python3
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pprint import pprint

def get_token():
    token_url='https://cloudsso.cisco.com/as/token.oauth2'
    client_id = 'v8p2k4puw96qhhpktxkfhjzd'
    client_secret = 'YSUsdHAGUC8Mkpd9DSrZE96y'
    data = {'grant_type': 'client_credentials'}

    access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(client_id, client_secret))
    access_token = json.loads(access_token_response.text)
    token = access_token['access_token']
    return token


def read_devices_from_netbox():
    url = "http://198.1.10.19:8000/api/dcim/devices/?limit=0&manufacturer=cisco&tag=managed"
    headers = {
    "Authorization": "Token 9fe22e04104757bbe78fc2fe617f09438bad1509",
    "Content-type": "application/json",
    "Accept": "application/json",
    }

    nb_map = list()
    r = requests.get(url, headers=headers, verify=False)
    json_data = json.loads(r.text)['results']
    for host in json_data:
        nb_map_key = {host['name']: host['asset_tag'] for host in json_data}
        nb_map.append(nb_map_key)
    nb_map = nb_map[0]
    return nb_map

def cf_devices():
    token = get_token()
    asset_tag_list = read_devices_from_netbox()
    parsed_list = list()
    for hostname, asset_tag in asset_tag_list.items():
        coverage_url = "https://api.cisco.com/sn2info/v2/coverage/summary/serial_numbers/" + asset_tag

        headers = {
        'Content-Type': 'application/json-rpc',
        'Authorization': 'Bearer ' + token 
        }

        coverage_resp = requests.request("GET", coverage_url, headers=headers)
        coverage_resp = json.loads(coverage_resp.text)
        coverage_resp = coverage_resp['serial_numbers'][0]
        
        parsed_list.append({
            "hostname": hostname,
            "coverage_end_date": coverage_resp['covered_product_line_end_date'], 
            "covered": coverage_resp['is_covered'],
            "service_contract_number": coverage_resp['service_contract_number'],
            "service_contract_level": coverage_resp['service_line_descr'],
            "warranty_end_date": coverage_resp['warranty_end_date']
        })
    return parsed_list

def main():
    result = cf_devices()
    pprint(result)

if __name__ == '__main__':
    main()
