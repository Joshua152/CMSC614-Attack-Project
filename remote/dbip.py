import os
from pathlib import Path
import pickle
from typing import Tuple

from dotenv import load_dotenv
import requests

from remote.ip_interface import IpLocationLookup


load_dotenv()
api_token = os.getenv('DB_IP_TOKEN')

db_ip_base_url = f'http://api.db-ip.com/v2/{api_token}'
db_ip_save_path = 'remote/cache/db_ip_info_save.pkl'


class DBIP(IpLocationLookup):
    def lookup_location(self, ips: list[str]) -> dict[str, Tuple[float, float]]:
        if Path(db_ip_save_path).is_file():
            with open(db_ip_save_path, 'rb') as file:
                print('Open DB-IP locations from pickle')
                return pickle.load(file)

        ip_locations = {}

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
                if 'latitude' in ip_data and 'longitude' in ip_data:
                    ip_locations[ip] = (ip_data['latitude'], ip_data['longitude'])
        
        with open(db_ip_save_path, 'wb') as file:
            pickle.dump(ip_locations, file)

        return ip_locations