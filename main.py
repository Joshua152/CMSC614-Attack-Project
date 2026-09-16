'''
Half the measurement papers you'll read this term geolocate an IP address and then say something about a country. RIPE Atlas probes publish operator-reported coordinates — real ground truth, free. So you can check.

Build: query MaxMind GeoLite2, IPinfo, DB-IP, and IP2Location for the IPs of RIPE Atlas probes with known locations, and plot the error distribution.

A  The pooled error CDF across all four providers — and then the split that matters: fixed vs. mobile networks, and by continent. The pooled CDF is the trap; the split is the finding.

B  Go after the mechanism: show that prefix size predicts error, and derive a rule of thumb for when a paper is entitled to make a sub-national claim.

SAFETY. Public RIPE Atlas metadata and free-tier geolocation APIs. Respect their rate limits.
'''

