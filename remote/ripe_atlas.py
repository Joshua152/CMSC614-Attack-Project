'''
Get the ground truth location of probes and their corresponding IP addresses
'''

import os

import country_converter as coco
from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Tuple
from dotenv import load_dotenv
import requests


load_dotenv()
api_token = os.getenv('DB_IP_TOKEN')

atlas_base_url = 'https://atlas.ripe.net/api/v2'
db_ip_base_url = f'http://api.db-ip.com/v2/{api_token}'
probe_pickle_path = 'remote/cache/probes.pkl'


@dataclass
class Probe:
    ipv4: str
    coordinates: Tuple[float, float]
    continent: str
    connection_type: str # Fixed vs Mobile
    isp: str # Keep the ISP in case we want to look at more mobile ISPs


'''
Get the probes fro the RIPE Atlas API
Saves the results to a pickle file so we don't keep hitting the API
'''
def get_probes(
    max_probes: int = 20000, 
    save_pickle: bool = True, 
    use_pickle_if_available: bool = True
) -> list[Probe]:
    if use_pickle_if_available and Path(probe_pickle_path).is_file():
        with open(probe_pickle_path, 'rb') as file:
            print("Open probes from pickle")
            probes = pickle.load(file)
            return probes

    probes = []

    url = f'{atlas_base_url}/probes/?page_size=500&sort=id'

    cnt = 0
    while cnt < max_probes:
        print(f'{cnt}/{max_probes}')
        response = requests.get(url)
        if response.status_code != 200:
            print(f'Error hitting RIPE Atlas probes endpoint: {response.status_code}')
            return []

        data = response.json()
        results = data['results']

        n_process = min(len(results), max_probes - cnt)
        n_invalid = 0
        for i in range(n_process):
            result = results[i]
            ipv4 = result['address_v4']
            geometry = result['geometry']
            if ipv4 and geometry:
                coordinates = geometry['coordinates']
                probes.append(Probe(
                    ipv4=ipv4,
                    coordinates=(coordinates[1], coordinates[0]),
                    continent=coco.convert(names=result['country_code'], to='Continent'),
                    connection_type='Unknown',
                    isp=None
                ))
            else:
                n_invalid += 1

        cnt += n_process - n_invalid
        url = data['next']
        if not url:
            break

    _augment_fixed_mobile_ip(probes)

    if save_pickle:
        with open(probe_pickle_path, 'wb') as file:
            pickle.dump(probes, file)

    return probes


def _augment_fixed_mobile_ip(probes: list[Probe]):
    print('Augmenting with fixed vs mobile IPs...')

    ips = list(set([p.ipv4 for p in probes]))
    connection_map = {ip: 'Unknown' for ip in ips}
    isp_map = {ip: None for ip in ips}

    # Can batch up to 256 together
    for i in range(len(ips) // 256):
        sample_ips = ips[i * 256:(i + 1) * 256]
        url = f'{db_ip_base_url}/{','.join(sample_ips)}'

        response = requests.get(url)
        if response.status_code != 200:
            print(f'Error hitting DB-IP endpoint: {response.status_code}')
            return {}

        data = response.json()
        for ip in data.keys():
            ip_data = data[ip]
            if 'linkType' not in ip_data or 'isp' not in ip_data:
                continue

            link_type = ip_data['linkType'] # dialup, isdn, cable, dsl, fttx, wireless
            isp = ip_data['isp']

            isp_map[ip] = isp

            if link_type in ['dialup', 'isdn', 'cable', 'dsl', 'fttx']:
                connection_map[ip] = 'Fixed'
            elif link_type in ['wireless'] and _is_mobile_isp(isp):
                connection_map[ip] = 'Mobile'
            else:
                connection_map[ip] = 'Unknown'

    for probe in probes:
        probe.isp = isp_map[probe.ipv4]
        probe.connection_type = connection_map[probe.ipv4]


def _is_mobile_isp(isp: str) -> bool:
    # not classifying all isp, just the obvious ones
    if 't-mobile' in isp.lower() or 'china mobile' in isp.lower():
        return True

    return False
