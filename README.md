# Brewblox-Plaato

BrewBlox integration for the [Plaato airlock](https://plaato.io).

The service periodically fetches the Plaato measurements, and sends it to the history service, allowing it to be used in graphs.

## Installation

For the service to access your Plaato data, you'll need an authentication token.

See https://plaato.io/apps/help-center#!hc-auth-token on how to get one.

When you have that, download and run the install file on your Pi (in your brewblox dir):

```
source .env
curl -O https://raw.githubusercontent.com/BrewBlox/brewblox-plaato/${BREWBLOX_RELEASE}/install_plaato.py
python3 install_plaato.py
```

This script will add the service, and run `brewblox-ctl up`.

After a minute, you should see the `plaato` measurement appear in the Graph widget metrics.
