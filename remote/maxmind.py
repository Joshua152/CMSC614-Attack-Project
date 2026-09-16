import geoip2.database
from typing import Tuple

from remote.ip_interface import IpLocationLookup


class MaxMind(IpLocationLookup):
    def lookup_location(self, ips: list[str]) -> Tuple[float, float]:
        ip_locations = {}

        with geoip2.database.Reader('data/GeoLite2-City.mmdb') as reader:
            for ip in ips:
                response = reader.city(ip)
                ip_locations[ip] = (response.location.latitude, response.location.longitude)

        return ip_locations
