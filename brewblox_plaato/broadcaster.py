"""
Intermittently broadcasts plaato state to the eventbus
"""


import asyncio
from concurrent.futures import CancelledError
from os import getenv

from aiohttp import web
from brewblox_service import (brewblox_logger, events, features, http_client,
                              scheduler, strex)

AUTH_ENV_KEY = 'PLAATO_AUTH'
PINS = [
    ('bpm', 'v102'),
    ('temperature', 'v103'),
    ('volume', 'v104'),
    ('original_gravity', 'v105'),
    ('specific_gravity', 'v106'),
    ('abv', 'v107'),
    ('temperature_unit', 'v108'),
    ('volume_unit', 'v109'),
    ('bubbles', 'v110'),
    ('co2', 'v119'),
]


LOGGER = brewblox_logger(__name__)


def get_broadcaster(app: web.Application):
    return features.get(app, Broadcaster)


def setup(app: web.Application):
    features.add(app, Broadcaster(app))


async def _fetch(session, url):
    resp = await session.get(url)
    return await resp.json()


def _unpack(val):
    raw = val if not isinstance(val, list) else val[0]
    try:
        return float(raw)
    except ValueError:
        return raw


class Broadcaster(features.ServiceFeature):

    def __init__(self, app: web.Application):
        super().__init__(app)
        self._task: asyncio.Task = None

    def __str__(self):
        return f'{type(self).__name__}'

    @property
    def active(self):
        return bool(self._task and not self._task.done())

    async def startup(self, app: web.Application):
        await self.shutdown(app)
        self._task = await scheduler.create_task(app, self._broadcast())

    async def shutdown(self, _):
        await scheduler.cancel_task(self.app, self._task)
        self._task = None

    async def _fetch(self, url):
        resp = await self._session.get(url)
        return await resp.json()

    async def _broadcast(self):
        try:
            name = self.app['config']['name']
            interval = self.app['config']['broadcast_interval']
            exchange = self.app['config']['broadcast_exchange']

            if interval <= 0 or self.app['config']['volatile']:
                LOGGER.info(f'{self} disabled by user')
                return

            LOGGER.info(f'Starting {self}')

            session = http_client.get_client(self.app).session
            publisher = events.get_publisher(self.app)
            token = getenv(AUTH_ENV_KEY)
            base_url = f'http://plaato.blynk.cc/{token}/get'
            urls = [f'{base_url}/{pin[1]}' for pin in PINS]
            last_broadcast_ok = True

        except Exception as ex:
            LOGGER.error(f'{type(ex).__name__}: {str(ex)}', exc_info=True)
            raise ex

        while True:
            try:
                await asyncio.sleep(interval)

                responses = await asyncio.gather(*[_fetch(session, url) for url in urls])

                raw_data = {key: _unpack(resp) for resp, (key, pin) in zip(responses, PINS)}

                data = {
                    f'temperature[{raw_data["temperature_unit"]}]': raw_data['temperature'],
                    f'volume[{raw_data["volume_unit"]}]': raw_data['volume'],
                    f'co2[{raw_data["volume_unit"]}]': raw_data['co2'],
                    'original_gravity[g/cm3]': raw_data['original_gravity'],
                    'specific_gravity[g/cm3]': raw_data['specific_gravity'],
                    'abv': raw_data['abv'],
                    'bpm': raw_data['bpm'],
                    'bubbles': raw_data['bubbles'],
                }

                await publisher.publish(
                    exchange=exchange,
                    routing=name,
                    message=data
                )

                if not last_broadcast_ok:
                    LOGGER.info(f'{self} resumed Ok')
                    last_broadcast_ok = True

            except CancelledError:
                break

            except Exception as ex:
                if last_broadcast_ok:
                    LOGGER.error(f'{self} encountered an error: {strex(ex)}')
                    last_broadcast_ok = False
