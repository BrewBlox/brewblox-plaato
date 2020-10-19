"""
Tests brewblox_plaato.broadcaster
"""

import asyncio

import pytest
from aiohttp import web
from aresponses import ResponsesMockServer
from brewblox_service import http, repeater, scheduler
from mock import AsyncMock, Mock

from brewblox_plaato import broadcaster

TESTED = broadcaster.__name__


@pytest.fixture
def token_mock(mocker):
    mocker.patch(TESTED + '.getenv', Mock(return_value='xyz'))


@pytest.fixture
def m_publish(mocker):
    m = mocker.patch(TESTED + '.mqtt.publish', AsyncMock())
    return m


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
def app(app, m_publish):
    app['config']['broadcast_interval'] = 0.001
    scheduler.setup(app)
    http.setup(app)
    return app


@pytest.fixture
def setup_broadcaster(app, aresponses):
    broadcaster.setup(app)
    for i in range(100):
        plaato_resp(aresponses)


async def test_run(app, m_publish, aresponses, client, token_mock):
    plaato_resp(aresponses)
    caster = broadcaster.Broadcaster(app)
    await caster.prepare()
    await caster.run()

    m_publish.assert_awaited_with(
        app,
        'brewcast/history/plaato',
        {
            'key': 'test_app',
            'data': {
                'temperature[°C]': pytest.approx(17.5),
                'volume[L]': None,
                'co2[L]': pytest.approx(0.2),
                'original_gravity[g/cm3]': pytest.approx(1.055),
                'specific_gravity[g/cm3]': pytest.approx(1.04),
                'abv': pytest.approx(37.5),
                'bpm': 10,
                'bubbles': 42,
            },
        })


async def test_setup(app, setup_broadcaster, m_publish, token_mock, client):
    assert broadcaster.fget(app)
    await asyncio.sleep(0.1)
    assert m_publish.call_count > 1


async def test_token_error(app, client):
    caster = broadcaster.Broadcaster(app)
    with pytest.raises(KeyError, match=r'Plaato auth token'):
        await caster.prepare()


async def test_cancel(app, client, token_mock):
    app['config']['broadcast_interval'] = 0
    caster = broadcaster.Broadcaster(app)
    with pytest.raises(repeater.RepeaterCancelled):
        await caster.prepare()
