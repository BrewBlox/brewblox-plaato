"""
Tests brewblox_plaato.broadcaster
"""

import asyncio
import json
from unittest.mock import Mock

import pytest
from aiohttp import web
from aresponses import ResponsesMockServer
from brewblox_service import http, mqtt, repeater, scheduler

from brewblox_plaato import broadcaster
from brewblox_plaato.models import ServiceConfig

TESTED = broadcaster.__name__


@pytest.fixture
def m_publish(mocker):
    m = mocker.spy(mqtt, 'publish')
    return m


@pytest.fixture
def m_token(mocker):
    mocker.patch(TESTED + '.getenv', Mock(return_value='xyz'))


def plaato_resp(aresp: ResponsesMockServer):
    def add(pin, val, json=True):
        aresp.add(
            'plaato.blynk.cc', f'/xyz/get/{pin}', 'GET',
            web.json_response(val) if json else web.Response(body=val, content_type='application/json')
        )

    add('v102', 10)
    add('v103', ['17.5'])
    add('v104', '--', False)
    add('v105', ['1.055'])
    add('v106', ['1.04'])
    add('v107', ['37.5'])
    add('v108', ['°C'])
    add('v109', ['L'])
    add('v110', ['42'])
    add('v119', ['0.2'])


@pytest.fixture
async def setup(app, broker):
    config: ServiceConfig = app['config']
    config.broadcast_interval = 0.001
    config.mqtt_host = 'localhost'
    config.mqtt_port = broker['mqtt']

    scheduler.setup(app)
    mqtt.setup(app)
    http.setup(app)
    broadcaster.setup(app, autostart=False)


@pytest.fixture(autouse=True)
async def synchronized(app, client):
    await asyncio.wait_for(mqtt.fget(app).ready.wait(), timeout=5)


async def test_run(app, client, m_publish, m_token, aresponses):
    c = broadcaster.fget(app)
    plaato_resp(aresponses)
    await c.prepare()
    await c.run()

    m_publish.assert_awaited_with(
        app,
        topic='brewcast/history/plaato',
        payload=json.dumps({
            'key': 'test_app',
            'data': {
                'temperature[°C]': 17.5,
                'volume[L]': None,
                'co2[L]': 0.2,
                'original_gravity[g/cm3]': 1.055,
                'specific_gravity[g/cm3]': 1.04,
                'abv': 37.5,
                'bpm': 10.0,
                'bubbles': 42.0,
            },
        }))


async def test_token_error(app, client):
    c = broadcaster.fget(app)
    with pytest.raises(KeyError, match=r'Plaato auth token'):
        await c.prepare()


async def test_cancel(app, client):
    app['config'].broadcast_interval = 0
    c = broadcaster.fget(app)
    with pytest.raises(repeater.RepeaterCancelled):
        await c.prepare()
