'''
Half the measurement papers you'll read this term geolocate an IP address and then say something about a country. RIPE Atlas probes publish operator-reported coordinates — real ground truth, free. So you can check.

Build: query MaxMind GeoLite2, IPinfo, DB-IP, and IP2Location for the IPs of RIPE Atlas probes with known locations, and plot the error distribution.

A  The pooled error CDF across all four providers — and then the split that matters: fixed vs. mobile networks, and by continent. The pooled CDF is the trap; the split is the finding.

B  Go after the mechanism: show that prefix size predicts error, and derive a rule of thumb for when a paper is entitled to make a sub-national claim.

SAFETY. Public RIPE Atlas metadata and free-tier geolocation APIs. Respect their rate limits.
'''

from remote.ip_interface import IpLocationLookup
from remote.maxmind import MaxMind
from remote.ripe_atlas import get_probes

from geopy.distance import geodesic


probes = get_probes()
print(probes)

def get_errors(provider: IpLocationLookup):
    errors = []

    ips = []
    for probe in probes:
        ips.append(probe.ipv4)

    '''
    Either providerLocs or probes.coordinates is in [long, lat] instaed of [lat, long]
    '''
    providerLocs = provider.lookup_location(ips)
    for probe in probes:
        distance_km = geodesic(providerLocs[probe.ipv4], probe.coordinates).kilometers
        errors.append(distance_km)
        # print(probe.ipv4, probe.coordinates, providerLocs[probe.ipv4], distance_km)

    errors.sort()

    return errors

def plot_cdf():


    pass

errors = get_errors(MaxMind())
print(len(errors))