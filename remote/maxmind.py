import geoip2.database
from geoip2.errors import AddressNotFoundError
from typing import Tuple

from remote.ip_interface import IpLocationLookup


class MaxMind(IpLocationLookup):
    def lookup_location(self, ips: list[str]) -> Tuple[float, float]:
        ip_locations = {}

        with geoip2.database.Reader('data/GeoLite2-City.mmdb') as reader:
            for ip in ips:
                try:
                    response = reader.city(ip)
                    ip_locations[ip] = (response.location.latitude, response.location.longitude)
                except AddressNotFoundError:
                    print(f'Could not find {ip} in the MaxMind database.')

        return ip_locations
