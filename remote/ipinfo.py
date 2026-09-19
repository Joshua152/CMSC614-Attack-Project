from pathlib import Path
import pickle

from dotenv import load_dotenv
import ipinfo
import os
from typing import Tuple

from remote.ip_interface import IpLocationLookup


load_dotenv()
api_token = os.getenv('IPINFO_API_TOKEN')

ip_info_save_path = 'remote/ip_info_save.pkl'

handler = ipinfo.getHandler(api_token)


class IpInfo(IpLocationLookup):
    def lookup_location(self, ips: list[str]) -> dict[str, Tuple[float, float]]:
        if Path(ip_info_save_path).is_file():
            with open(ip_info_save_path, 'rb') as file:
                print('Open IpInfo locations from pickle')
                return pickle.load(file)

        ip_locations = {}

        for i in range(len(ips) // 1000):
            sampled_ips = ips[i * 1000:(i + 1) * 1000]
            batch_details = handler.getBatchDetails(sampled_ips)

            for ip in batch_details.keys():
                if not isinstance(batch_details[ip], ipinfo.details.Details) and 'loc' in batch_details[ip]:
                    loc = batch_details[ip]['loc']
                    lat, lng = loc.split(',')
                    ip_locations[ip] = (float(lat), float(lng))

        with open(ip_info_save_path, 'wb') as file:
            pickle.dump(ip_locations, file)

        return ip_locations

