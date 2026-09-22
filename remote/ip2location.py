'''
We uses the IP2Location LITE database for <a href="https://lite.ip2location.com">IP geolocation</a>.
'''

import os
from typing import Tuple

import IP2Location

from remote.ip_interface import IpLocationLookup


database = IP2Location.IP2Location(os.path.join('data', 'ip2location-lite.bin'))


class Ip2Location(IpLocationLookup):
    def lookup_location(self, ips: list[str]) -> dict[str, Tuple[float, float]]:
        ip_locations = {}

        for ip in ips:
            lat, lng = database.get_latitude(ip), database.get_longitude(ip)
            if lat is not None and lng is not None:
                ip_locations[ip] = (lat, lng)

        return ip_locations
