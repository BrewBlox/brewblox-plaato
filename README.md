# Brewblox-Plaato

BrewBlox integration for the [Plaato airlock](https://plaato.io).

The service periodically fetches the Plaato measurements, and sends it to the history service, allowing it to be used in graphs.

## Installation

For the service to access your Plaato data, you'll need an authentication token.

See https://plaato.io/apps/help-center#!hc-auth-token on how to get one.

When you have that, edit your services by running `brewblox-ctl editor`.

Add the new service:

```yml
  plaato:
    # remove 'rpi-' if you're running on desktop
    image: brewblox/brewblox-plaato:rpi-${BREWBLOX_RELEASE:-stable}
    restart: unless-stopped
    depends_on:
      - eventbus
    labels:
      - "traefik.port=5000"
      - "traefik.frontend.rule=PathPrefix: /plaato"
    environment:
      PLAATO_AUTH: "xyzabc1234" # Put your auth token here
    command: >
      --name=plaato
```

Start your services with `brewblox-ctl up`.

After a few seconds, you should see the `plaato` measurement appear in the Graph widget metrics.
