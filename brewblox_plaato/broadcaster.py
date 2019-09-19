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


LOGGER = brewblox_logger(__name__)


def get_broadcaster(app: web.Application):
    return features.get(app, Broadcaster)


def setup(app: web.Application):
    features.add(app, Broadcaster(app))


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
            last_broadcast_ok = True

        except Exception as ex:
            LOGGER.error(f'{type(ex).__name__}: {str(ex)}', exc_info=True)
            raise ex

        while True:
            try:
                await asyncio.sleep(interval)

                url = f'http://plaato.blynk.cc/{token}/get/v102'
                resp = await session.get(url)
                data = await resp.json()

                await publisher.publish(
                    exchange=exchange,
                    routing=name,
                    message={'bpm': data}
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
