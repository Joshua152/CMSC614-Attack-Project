"""Test whether announced IP prefix size predicts geolocation error."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import math
import sys
from pathlib import Path
from typing import Iterable, Iterator, TypeVar

import matplotlib.pyplot as plt
import pandas as pd
from geopy.distance import geodesic

from remote.dbip import DBIP
from remote.ip2location import Ip2Location
from remote.ip_interface import IpLocationLookup
from remote.ipinfo import IpInfo
from remote.maxmind import MaxMind
from remote.ripe_atlas import get_probes


PROVIDERS = {
    'MaxMind': MaxMind,
    'IpInfo': IpInfo,
    'Ip2Location': Ip2Location,
    'DB-IP': DBIP,
}
RESULTS_DIR = Path('results')
ProgressItem = TypeVar('ProgressItem')


def progress(items: Iterable[ProgressItem], total: int, label: str) -> Iterator[ProgressItem]:
    """Yield items while displaying progress without an extra dependency."""
    width = 30
    for completed, item in enumerate(items, start=1):
        filled = int(width * completed / total) if total else width
        bar = '#' * filled + '-' * (width - filled)
        print(f'\r{label}: [{bar}] {completed}/{total}', end='', file=sys.stderr, flush=True)
        yield item
    print(file=sys.stderr)


def prefix_length(prefix: str | None) -> int | None:
    """Parse a CIDR prefix and return its address length."""
    if not prefix:
        return None
    try:
        return ipaddress.ip_network(prefix, strict=False).prefixlen
    except ValueError:
        return None


def get_error_rows(provider: IpLocationLookup, probes) -> pd.DataFrame:
    """Calculate provider error while retaining the IP needed for the join."""
    ips = [probe.ipv4 for probe in probes]
    locations = provider.lookup_location(ips)
    rows = []
    for probe in probes:
        if probe.ipv4 not in locations:
            continue
        try:
            error_km = geodesic(locations[probe.ipv4], probe.coordinates).kilometers
        except ValueError:
            continue
        rows.append({
            'ip': probe.ipv4,
            'prefix': probe.prefix,
            'error_km': error_km,
            'continent': probe.continent,
            'connection_type': probe.connection_type,
        })
    return pd.DataFrame(rows, columns=[
        'ip', 'prefix', 'error_km', 'continent', 'connection_type'
    ])


def regression_stats(x: pd.Series, y: pd.Series) -> tuple[float, float, float]:
    """Return OLS slope, intercept, and R-squared for x predicting y."""
    x_values = x.to_numpy(dtype=float)
    y_values = y.to_numpy(dtype=float)
    centered_x = x_values - x_values.mean()
    centered_y = y_values - y_values.mean()
    denominator = (centered_x ** 2).sum()
    if denominator == 0:
        return float('nan'), float('nan'), float('nan')
    slope = float((centered_x * centered_y).sum() / denominator)
    intercept = float(y_values.mean() - slope * x_values.mean())
    predictions = intercept + slope * x_values
    residual_sum = ((y_values - predictions) ** 2).sum()
    total_sum = (centered_y ** 2).sum()
    r_squared = float(1 - residual_sum / total_sum) if total_sum else float('nan')
    return slope, intercept, r_squared


def analyse_provider(
    provider_name: str,
    probes,
) -> tuple[pd.DataFrame, float, float, float]:
    rows = get_error_rows(PROVIDERS[provider_name](), probes)
    rows['prefix_length'] = rows['prefix'].map(prefix_length)
    rows = rows.dropna(subset=['prefix_length', 'error_km']).copy()
    rows['log_error_km'] = (rows['error_km'] + 1).map(math.log)
    slope, intercept, r_squared = regression_stats(
        rows['prefix_length'], rows['log_error_km']
    )
    return rows, slope, intercept, r_squared


def plot_median_error_by_prefix_length(results: dict[str, pd.DataFrame]) -> None:
    """Plot each provider's median error for prefix lengths 8 through 24."""
    prefix_lengths = list(range(8, 25))
    figure, axis = plt.subplots(figsize=(10, 6))
    for provider_name, rows in results.items():
        median_errors = (
            rows[rows['prefix_length'].between(8, 24)]
            .groupby('prefix_length')['error_km']
            .median()
            .reindex(prefix_lengths)
        )
        axis.plot(prefix_lengths, median_errors, marker='o', linewidth=2, label=provider_name)
    axis.set_xticks(prefix_lengths)
    axis.set_xlabel('Announced prefix length (CIDR)')
    axis.set_ylabel('Median geolocation error (km)')
    axis.set_title('Median geolocation error by announced prefix length')
    axis.set_yscale('log')
    axis.grid(True, axis='y', alpha=0.25)
    axis.legend()
    figure.tight_layout()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(RESULTS_DIR / 'part_b_median_error_by_prefix_length.png', dpi=200)
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=20_000)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()

    probes = get_probes(max_probes=args.limit, use_pickle_if_available=True, save_pickle=True)
    results = {}
    summary = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(PROVIDERS))) as executor:
        futures = {
            executor.submit(
                analyse_provider,
                provider_name,
                probes,
            ): provider_name
            for provider_name in PROVIDERS
        }
        for future in progress(as_completed(futures), len(futures), 'Providers'):
            provider_name = futures[future]
            rows, slope, intercept, r_squared = future.result()
            results[provider_name] = rows
            summary.append({
                'provider': provider_name,
                'n_probes': len(rows),
                'regression_slope_log_error': slope,
                'regression_intercept_log_error': intercept,
                'r_squared': r_squared,
            })

    summary_df = pd.DataFrame(summary).sort_values('provider')
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(RESULTS_DIR / 'part_b_summary.csv', index=False)
    plot_median_error_by_prefix_length(results)

    print(summary_df.to_string(index=False))


if __name__ == '__main__':
    main()