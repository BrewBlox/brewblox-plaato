# Brewblox-Plaato

**IMPORTANT: Plaato has discontinued their line of homebrewing products, and the API will shut down november 2025. 
This service is archived unless **

BrewBlox integration for the [Plaato airlock](https://plaato.io).

The service periodically fetches the Plaato measurements, and sends it to the history service, allowing it to be used in graphs.

## Installation

For the service to access your Plaato data, you'll need an authentication token.

See <https://intercom.help/plaato/en/articles/5004720-auth_token> on how to get one.

When you have that, add the following service to docker-compose.yml:

```yml
  plaato:
    imdage: ghcr.io/brewblox/brewblox-plaato:${BREWBLOX_RELEASE}
    restart: unless-stopped
    environment:
      - PLAATO_AUTH={TOKEN}
```

Replace `{TOKEN}` with your auth token

Run `brewblox-ctl up`, and you should see the `plaato` measurement appear in the Graph widget metrics.
