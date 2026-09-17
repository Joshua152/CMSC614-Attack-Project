'''
Half the measurement papers you'll read this term geolocate an IP address and then say something about a country. RIPE Atlas probes publish operator-reported coordinates — real ground truth, free. So you can check.

Build: query MaxMind GeoLite2, IPinfo, DB-IP, and IP2Location for the IPs of RIPE Atlas probes with known locations, and plot the error distribution.

A  The pooled error CDF across all four providers — and then the split that matters: fixed vs. mobile networks, and by continent. The pooled CDF is the trap; the split is the finding.

B  Go after the mechanism: show that prefix size predicts error, and derive a rule of thumb for when a paper is entitled to make a sub-national claim.

SAFETY. Public RIPE Atlas metadata and free-tier geolocation APIs. Respect their rate limits.
'''

from typing import Mapping

from geopy.distance import geodesic
import matplotlib.pyplot as plt
import pandas as pd

from remote.ip_interface import IpLocationLookup
from remote.maxmind import MaxMind
from remote.ripe_atlas import get_probes


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
            distance_km = geodesic(providerLocs[probe.ipv4], probe.coordinates).kilometers
            errors.append(distance_km)
            continents.append(probe.continent)
            connection_type.append(probe.connection_type)

    df = pd.DataFrame({
        'error': errors,
        'continent': continents,
        'connection_type': connection_type
    })

    return df


def plot_cdf(errors: Mapping[str, list[float]]):
    fig = plt.figure()
    ax = fig.gca()

    for category in errors:
        ax.ecdf(errors[category], label=category)

    plt.xlabel('Error (km)')
    plt.ylabel('CDF')
    plt.title('Error CDF by Continent')
    plt.grid(True)
    plt.legend()
    plt.show()


if __name__ == '__main__':
    df = get_errors_df(MaxMind())
    plot_cdf({
        'All': df['error'].tolist(),
        **df.groupby('continent')['error'].apply(list).to_dict()
    })
