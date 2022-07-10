# /usr/bin/env python3

from pprint import pp
import sys
import os
import time
import signal
import sqlite3

import httpx
from dotenv import load_dotenv

load_dotenv()
CLOUDFLARE_API_URL = os.getenv('CLOUDFLARE_API_URL', '')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN', '')
CLOUDFLARE_EMAIL = os.getenv('CLOUDFLARE_EMAIL', '')
CLOUDFLARE_ZONE = os.getenv('CLOUDFLARE_ZONE', '')
SANDBOX_MODE = os.getenv('SANDBOX_MODE', True)


def sig_handler(signum, frame):
    res = input("Ctrl+C was pressed. Do you really want to exit(y/n)?")
    if res == 'y':
        sys.exit(1)


def check_python3() -> bool:
    if sys.version_info[0] == 3:
        return True
    return False


def delete_zone_names(zone_id: str, zone_names: dict, sandbox: bool = True):
    for key, value in zone_names.items():
        deletion_status = 'PASS'
        if sandbox != True:
            r = httpx.delete(CLOUDFLARE_API_URL + '/' + zone_id + '/dns_records/' + key,
                             headers={
                                 'Content-Type': 'application/json',
                                 'X-Auth-Email': CLOUDFLARE_EMAIL,
                                 'Authorization': 'Bearer ' + CLOUDFLARE_API_TOKEN,
                             })
            deletion_status = r.status_code
            time.sleep(1)
        print(f"[INF] Deleting name: {value['name']}, Type: {value['type']} ... {deletion_status}")


def get_zone_names(zone_id: str) -> dict:
    if zone_id == '':
        print("[ERR] Empty Zone ID. Couldn't retrive names list! Exiting...")
        sys.exit(1)

    names_dict = {}
    current_page = 1
    print("[INF] Gathering names for zone ->", CLOUDFLARE_ZONE)
    while True:
        r = httpx.get(CLOUDFLARE_API_URL + '/' + zone_id + '/dns_records', params={'page': current_page},
                      headers={
                          'Content-Type': 'application/json',
                          'X-Auth-Email': CLOUDFLARE_EMAIL,
                          'Authorization': 'Bearer ' + CLOUDFLARE_API_TOKEN,
        })
        if r.json()['result_info']['total_count'] == 0:
            print(f"[INF] You don't have any name in {CLOUDFLARE_ZONE} zone!")
            sys.exit(0)
        for i in range(len(r.json()['result'])):
            names_dict[r.json()['result'][i]['id']] = {
                'name': r.json()['result'][i]['name'],
                'type': r.json()['result'][i]['type'],
            }
        print(
            f"[INF] Current page {current_page} from {r.json()['result_info']['total_pages']}. Count -> {r.json()['result_info']['count']}")
        if current_page == r.json()['result_info']['total_pages']:
            break
        current_page += 1
    return names_dict


def main():
    if check_python3() != True:
        print("[ERR] Please use only Python 3 version. We are not support Python 2!")
        sys.exit(1)
    try:
        signal.signal(signal.SIGINT, sig_handler)
        r = httpx.get(CLOUDFLARE_API_URL, params={'name': CLOUDFLARE_ZONE}, headers={
            'Content-Type': 'application/json',
            'X-Auth-Email': CLOUDFLARE_EMAIL,
            'Authorization': 'Bearer ' + CLOUDFLARE_API_TOKEN,
        })
        if r.status_code != 200 and r.json()['success'] == False:
            print("[ERR] Something goes wrong ->",
                  r.json()['errors'][0]['message'])
        zone_names = get_zone_names(r.json()['result'][0]['id'])
        delete_zone_names(r.json()['result'][0]['id'],
                          zone_names, SANDBOX_MODE)

    except Exception as ex:
        print("[EXC] Exception happened ->", ex)


if __name__ == '__main__':
    main()
