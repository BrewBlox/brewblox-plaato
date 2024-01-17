"""
Example of how to import and use the brewblox service
"""

from brewblox_service import brewblox_logger, http, mqtt, scheduler, service

from brewblox_plaato import broadcaster
from brewblox_plaato.models import ServiceConfig

LOGGER = brewblox_logger(__name__)


def create_parser():
    parser = service.create_parser('plaato')

    # Service network options
    group = parser.add_argument_group('Service communication')
    group.add_argument('--broadcast-interval',
                       help='Interval (in seconds) between plaato queries [%(default)s]',
                       type=float,
                       default=30)

    return parser


def main():
    parser = create_parser()
    config = service.create_config(parser, model=ServiceConfig)
    app = service.create_app(config)

    async def setup():
        scheduler.setup(app)
        mqtt.setup(app)
        http.setup(app)
        broadcaster.setup(app)

    service.run_app(app, setup())


if __name__ == '__main__':
    main()
