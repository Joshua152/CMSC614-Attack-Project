### Sep 16, 2026
Wrote a function to get the probes from the RIPE Atlas REST API

Implement an overarching ip lookup interface to create adapters for MaxMind, ...

Implemented IP lookup for MaxMind

Implemented error and CDF (interesting to note that the MaxMind ip seems to have a default if it can't locate the address: (37.751, -97.822))

Put the results in a Pandas dataframe so it would be easy to plot based on continent, fixed vs mobile

Graphed the CDF error plots on a single plot so it is easier to visualize against each other

### Sep 19, 2026
Implemented IpInfo
The API has a 50k per month API limit
Since we are looking at 20k probes, we are under that quota but, we need to save the values in a file so that we can cache the result
If we don't, we would run into the limit after only 2 full lookups
