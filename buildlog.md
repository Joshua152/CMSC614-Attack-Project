### Sep 19, 2026
Wrote a function to get the probes from the RIPE Atlas REST API

Implement an overarching ip lookup interface to create adapters for MaxMind, ...

Implemented IP lookup for MaxMind

Implemented error and CDF (interesting to note that the MaxMind ip seems to have a default if it can't locate the address: (37.751, -97.822))

Put the results in a Pandas dataframe so it would be easy to plot based on continent, fixed vs mobile