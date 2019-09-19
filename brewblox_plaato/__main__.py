"""
Example of how to import and use the brewblox service
"""

from brewblox_service import (brewblox_logger, events, http_client, scheduler,
                              service)

from brewblox_plaato import broadcaster

LOGGER = brewblox_logger(__name__)


def create_parser(default_name='plaato'):
    parser = service.create_parser(default_name=default_name)

    # Service network options
    group = parser.add_argument_group('Service communication')
    group.add_argument('--broadcast-interval',
                       help='Interval (in seconds) between plaato queries [%(default)s]',
                       type=float,
                       default=30)
    group.add_argument('--broadcast-exchange',
                       help='Eventbus exchange to which service state is broadcast. [%(default)s]',
                       default='brewcast')

    return parser


def main():
    app = service.create_app(parser=create_parser())

    scheduler.setup(app)
    events.setup(app)
    http_client.setup(app)
    broadcaster.setup(app)

    service.furnish(app)
    service.run(app)


if __name__ == '__main__':
    main()
