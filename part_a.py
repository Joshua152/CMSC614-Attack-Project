'''
Half the measurement papers you'll read this term geolocate an IP address and then say something about a country. RIPE Atlas probes publish operator-reported coordinates — real ground truth, free. So you can check.

Build: query MaxMind GeoLite2, IPinfo, DB-IP, and IP2Location for the IPs of RIPE Atlas probes with known locations, and plot the error distribution.

A  The pooled error CDF across all four providers — and then the split that matters: fixed vs. mobile networks, and by continent. The pooled CDF is the trap; the split is the finding.

B  Go after the mechanism: show that prefix size predicts error, and derive a rule of thumb for when a paper is entitled to make a sub-national claim.

SAFETY. Public RIPE Atlas metadata and free-tier geolocation APIs. Respect their rate limits.
'''

from typing import Mapping

import IP2Location
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import pandas as pd

from remote.ip2location import Ip2Location
from remote.ip_interface import IpLocationLookup
from remote.ipinfo import IpInfo
from remote.maxmind import MaxMind
from remote.ripe_atlas import get_probes


MAX_MIND = 'MaxMind'
IPINFO = 'IpInfo'
IP2LOCATION = 'Ip2Location'

probes = get_probes()


def get_errors_df(provider: IpLocationLookup):
    errors = []
    continents = []
    connection_type = []

    ips = []
    for probe in probes:
        ips.append(probe.ipv4)

    providerLocs = provider.lookup_location(ips)
    for probe in probes:
        if probe.ipv4 in providerLocs:
            try:
                distance_km = geodesic(providerLocs[probe.ipv4], probe.coordinates).kilometers
                errors.append(distance_km)
                continents.append(probe.continent)
                connection_type.append(probe.connection_type)
            except ValueError:
                print(f'Value error with provider locs: {providerLocs[probe.ipv4]} and probe locs: {probe.coordinates}')

    df = pd.DataFrame({
        'error': errors,
        'continent': continents,
        'connection_type': connection_type
    })

    return df


def plot_cdf(errors: Mapping[str, list[float]], title: str):
    fig = plt.figure()
    ax = fig.gca()

    for category in errors:
        ax.ecdf(errors[category], label=category)

    plt.xlabel('Error (km)')
    plt.ylabel('CDF')
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_errors_for_provider(providerStr: str):
    provider = None
    if providerStr == MAX_MIND:
        provider = MaxMind()
    elif providerStr == IPINFO:
        provider = IpInfo()
    elif providerStr == IP2LOCATION:
        provider = Ip2Location()
    else:
        print(f'Invalid provider')
        return

    df = get_errors_df(provider)
    plot_cdf({
        'All': df['error'].tolist(),
        **df.groupby('continent')['error'].apply(list).to_dict()
    }, f'Error CDF by Continent via {providerStr}')
    

if __name__ == '__main__':
    providers = [MAX_MIND, IPINFO, IP2LOCATION]
    for provider in providers:
        plot_errors_for_provider(provider)
