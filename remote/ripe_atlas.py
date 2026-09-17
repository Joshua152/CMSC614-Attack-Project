'''
Get the ground truth location of probes and their corresponding IP addresses
'''

from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Tuple
import requests


atlas_base_url = 'https://atlas.ripe.net/api/v2'
probe_pickle_path = 'remote/probes.pkl'


@dataclass
class Probe:
    ipv4: str
    coordinates: Tuple[float, float]


'''
Get the probes fro the RIPE Atlas API
Saves the results to a pickle file so we don't keep hitting the API
'''
def get_probes(
    max_probes: int = 10, 
    save_pickle: bool = True, 
    use_pickle_if_available: bool = True
) -> list[Probe]:
    if use_pickle_if_available and Path(probe_pickle_path).is_file():
        with open(probe_pickle_path, 'rb') as file:
            print("Open probes from pickle")
            return pickle.load(file)

    probes = []

    url = f'{atlas_base_url}/probes/?page_size=10&sort=id'

    cnt = 0
    while cnt < max_probes:
        response = requests.get(url)
        if response.status_code != 200:
            print(f'Error hitting RIPE Atlas probes URL: {response.status_code}')
            return []

        data = response.json()
        results = data['results']

        n_process = min(len(results), max_probes - cnt)
        n_invalid = 0
        for i in range(n_process):
            ipv4 = results[i]['address_v4']
            coordinates = results[i]['geometry']['coordinates']
            if ipv4:
                probes.append(Probe(
                    ipv4 = ipv4,
                    coordinates = (coordinates[1], coordinates[0])
                ))
            else:
                n_invalid += 1

        cnt += n_process - n_invalid
        url = data['next']
        if not url:
            break

    if save_pickle:
        with open(probe_pickle_path, 'wb') as file:
            pickle.dump(probes, file)

    return probes
