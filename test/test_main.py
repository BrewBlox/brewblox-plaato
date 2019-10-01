from brewblox_plaato import __main__ as main
from brewblox_plaato import broadcaster

TESTED = main.__name__


def test_main(mocker, app):
    mocker.patch(TESTED + '.service.run')
    mocker.patch(TESTED + '.service.create_app').return_value = app

    main.main()

    assert None not in [
        broadcaster.get_broadcaster(app)
    ]
