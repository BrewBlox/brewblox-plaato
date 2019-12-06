#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience installation script for adding a Plaato service to a BrewBlox installation.

It must be run in the BrewBlox install directory.

To run:

    python3 install.py

Notes:

- Python >= 3.5 is required to run.
- Package dependencies (shared with brewblox_ctl)
    - pyyaml
    - click
"""


import re
from os import path
from platform import machine
from subprocess import check_call

import click
import yaml


def _validate_name(ctx, param, value):
    if not re.match(r'^[a-z0-9-_]+$', value):
        raise click.BadParameter('Names can only contain letters, numbers, - or _')
    return value


@click.command()
@click.option('-n', '--name',
              prompt='How do you want to call this service? The name must be unique',
              callback=_validate_name,
              help='Service name')
@click.option('--token',
              prompt=True,
              help='Plaato authentication token')
@click.option('-f', '--force',
              is_flag=True,
              help='Allow overwriting an existing service')
def install(name, token, force):
    """
    Install Plaato service for BrewBlox

    The Plaato service needs an authentication token to access your device.
    See https://plaato.io/apps/help-center#!hc-auth-token on how to get one.
    """
    compose_file = path.abspath('./docker-compose.yml')

    if not path.exists(compose_file):
        raise SystemExit('ERROR: Compose file not found in current directory. '
                         'Please navigate to your brewblox directory first.')

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    if name in config['services'] and not force:
        print('Service "{}" already exists. Use the --force flag if you want to overwrite it'.format(name))
        return

    prefix = 'rpi-' if machine().startswith('arm') else ''
    config['services'][name] = {
        'image': 'brewblox/brewblox-plaato:{}{}'.format(prefix, '${BREWBLOX_RELEASE}'),
        'restart': 'unless-stopped',
        'labels': [
            'traefik.port=5000',
            'traefik.frontend.rule=PathPrefix: /' + name
        ],
        'environment': {
            'PLAATO_AUTH': token
        },
        'command': '--name=' + name
    }

    with open(compose_file, 'w') as f:
        yaml.safe_dump(config, f)

    print('Starting services...')
    check_call('brewblox-ctl up', shell=True)


if __name__ == '__main__':
    install()
