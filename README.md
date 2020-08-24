# Brewblox-Plaato

BrewBlox integration for the [Plaato airlock](https://plaato.io).

The service periodically fetches the Plaato measurements, and sends it to the history service, allowing it to be used in graphs.

## Installation

For the service to access your Plaato data, you'll need an authentication token.

See https://plaato.io/apps/help-center#!hc-auth-token on how to get one.

When you have that, run:

```
brewblox-ctl add-plaato --name plaato --token TOKEN
```

After a minute, you should see the `plaato` measurement appear in the Graph widget metrics.
