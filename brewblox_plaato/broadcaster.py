"""
Intermittently broadcasts plaato state to the eventbus
"""


import asyncio
from dataclasses import dataclass
from json import JSONDecodeError
from os import getenv

from aiohttp import web
from brewblox_service import (brewblox_logger, events, features, http_client,
                              repeater, strex)

LOGGER = brewblox_logger(__name__)
AUTH_ENV_KEY = 'PLAATO_AUTH'
PINS = [
    'v102',  # bpm
    'v103',  # temperature
    'v104',  # volume
    'v105',  # original_gravity
    'v106',  # specific_gravity
    'v107',  # abv
    'v108',  # temperature_unit
    'v109',  # volume_unit
    'v110',  # bubbles
    'v119',  # co2
]


def get_broadcaster(app: web.Application):
    return features.get(app, Broadcaster)


def setup(app: web.Application):
    features.add(app, Broadcaster(app))


@dataclass
class PlaatoData:
    bpm: int
    temperature: float
    volume: float
    original_gravity: float
    specific_gravity: float
    abv: float
    temperature_unit: str
    volume_unit: str
    bubbles: int
    co2: float

    def serialize(self):
        values = {
            f'temperature[{self.temperature_unit}]': self.temperature,
            f'volume[{self.volume_unit}]': self.volume,
            f'co2[{self.volume_unit}]': self.co2,
            'original_gravity[g/cm3]': self.original_gravity,
            'specific_gravity[g/cm3]': self.specific_gravity,
            'abv': self.abv,
            'bpm': self.bpm,
            'bubbles': self.bubbles,
        }
        return {k: (v if not isinstance(v, str) else None) for k, v in values.items()}


class Broadcaster(repeater.RepeaterFeature):

    async def _fetch(self, url):
        resp = await self.session.get(url)
        try:
            val = await resp.json()
        except JSONDecodeError as ex:
            val = await resp.text()
            LOGGER.debug(f'Failed to decode response "{val}" from {url}: {strex(ex)}')

        # We're dealing with the following types:
        # - int -> int
        # - float as string in list -> int
        # - str in list -> str
        val = val[0] if isinstance(val, list) else val
        try:
            return float(val)
        except ValueError:
            return val

    async def prepare(self):
        self.name = self.app['config']['name']
        self.interval = self.app['config']['broadcast_interval']
        self.exchange = self.app['config']['broadcast_exchange']

        if self.interval <= 0:
            raise repeater.RepeaterCancelled()

        self.session = http_client.get_client(self.app).session
        self.publisher = events.get_publisher(self.app)

        token = getenv(AUTH_ENV_KEY)
        if token is None:
            raise KeyError(f'Plaato auth token not added as env variable (key={AUTH_ENV_KEY})')

        self.urls = [f'http://plaato.blynk.cc/{token}/get/{pin}' for pin in PINS]

    async def run(self):
        await asyncio.sleep(self.interval)

        responses = await asyncio.gather(*(self._fetch(url) for url in self.urls))
        data = PlaatoData(*responses)
        LOGGER.debug(data)

        await self.publisher.publish(
            exchange=self.exchange,
            routing=self.name,
            message=data.serialize()
        )
