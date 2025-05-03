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


def read_device_types_from_netbox():
    url = "http://198.1.10.19:8000/api/dcim/device-types/?manufacturer=cisco&limit=0"

    headers = {
    "Authorization": "Token 9fe22e04104757bbe78fc2fe617f09438bad1509",
    "Content-type": "application/json",
    "Accept": "application/json",
    }
    
    nb_map = list()
    r = requests.get(url, headers=headers, verify=False)
    json_data = json.loads(r.text)['results']
    for model in json_data:
        nb_map.append(model['model'])
    return nb_map


def cf_device_type():
    token = get_token()
    product_id_list = read_device_types_from_netbox()
    parsed_list = list()
    for product_id in product_id_list:
        product_url = "https://api.cisco.com/product/v1/information/product_ids/" + product_id
        eox_url = "https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/" + product_id
        image_url = "https://api.cisco.com/software/suggestion/v2/suggestions/software/productIds/" + product_id

        headers = {
        'Content-Type': 'application/json-rpc',
        'Authorization': 'Bearer ' + token 
        }

        product_resp = requests.request("GET", product_url, headers=headers)
        product_resp = json.loads(product_resp.text)
        product_resp = product_resp['product_list'][0]
        # pprint(product_resp)

        eox_resp = requests.request("GET", eox_url, headers=headers)
        eox_resp = json.loads(eox_resp.text)
        eox_resp = eox_resp['EOXRecord'][0]
        # pprint(eox_resp)

        image_resp = requests.request("GET", image_url, headers=headers)
        image_resp = json.loads(image_resp.text)
        image_resp = image_resp['productList'][0]
        # pprint(image_resp)
        
        if eox_resp['LinkToProductBulletinURL'] == '' and image_resp['suggestions'][0]['isSuggested'] == "Y":
            parsed_list.append({
                "model": product_id, 
                "product_support_page": product_resp['product_support_page'], 
                "product_release_date": product_resp['release_date'],
                "product_image_suggestion": image_resp['suggestions'][0]['images'][-1]['imageName']
            })
        elif eox_resp['LinkToProductBulletinURL'] == '' and image_resp['suggestions'][0]['isSuggested'] == '':
            parsed_list.append({
                "model": product_id, 
                "product_support_page": product_resp['product_support_page'], 
                "product_release_date": product_resp['release_date']
            })
        elif eox_resp['LinkToProductBulletinURL'] != '' and image_resp['suggestions'][0]['isSuggested'] == "Y":
            parsed_list.append({
                "model": product_id, 
                "product_support_page": product_resp['product_support_page'], 
                "product_release_date": product_resp['release_date'],
                "product_eol_page": eox_resp['LinkToProductBulletinURL'],
                "end_of_life_announcement_date": eox_resp['EOXExternalAnnouncementDate']['value'],
                "end_of_sale_date": eox_resp['EndOfSaleDate']['value'],
                "end_of_service_contract_renewal_date": eox_resp['EndOfServiceContractRenewal']['value'],
             	"end_of_security_vul_support_date": eox_resp['EndOfSecurityVulSupportDate']['value'],
                "end_of_sw_maintenance_releases_date": eox_resp['EndOfSWMaintenanceReleases']['value'],
                "last_date_of_support": eox_resp['LastDateOfSupport']['value'],
                "migration_product": eox_resp['EOXMigrationDetails']['MigrationProductId'],
                "product_image_suggestion": image_resp['suggestions'][0]['images'][-1]['imageName']
            })
        elif eox_resp['LinkToProductBulletinURL'] != '' and image_resp['suggestions'][0]['isSuggested'] == '':
            parsed_list.append({
                "model": product_id, 
                "product_support_page": product_resp['product_support_page'], 
                "product_release_date": product_resp['release_date'],
                "product_eol_page": eox_resp['LinkToProductBulletinURL'],
                "end_of_life_announcement_date": eox_resp['EOXExternalAnnouncementDate']['value'],
                "end_of_sale_date": eox_resp['EndOfSaleDate']['value'],
                "end_of_service_contract_renewal_date": eox_resp['EndOfServiceContractRenewal']['value'],
             	"end_of_security_vul_support_date": eox_resp['EndOfSecurityVulSupportDate']['value'],
                "end_of_sw_maintenance_releases_date": eox_resp['EndOfSWMaintenanceReleases']['value'],
                "last_date_of_support": eox_resp['LastDateOfSupport']['value'],
                "migration_product": eox_resp['EOXMigrationDetails']['MigrationProductId']
            })

    return parsed_list


def main():
    result = cf_device_type()
    pprint(result)

if __name__ == '__main__':
    main()
