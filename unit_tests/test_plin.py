import pytest

from plin.enums import PLINMode
from plin.plin import PLIN


@pytest.fixture
def test_interface():
    return "/dev/plin0"


@pytest.fixture
def test_plin(test_interface):
    return PLIN(test_interface)


@pytest.fixture
def test_plin_slave_1000(test_plin):
    test_plin.start(mode=PLINMode.SLAVE, baudrate=1000)
    return test_plin


def test_start(test_plin):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    test_plin.start(mode=expected_mode, baudrate=expected_baudrate)
    assert test_plin.get_baudrate() == expected_baudrate
    assert test_plin.get_mode() == expected_mode
    test_plin.stop()


def test_reset(test_plin_slave_1000):
    expected_baudrate = 0
    expected_mode = PLINMode.NONE

    test_plin_slave_1000.reset()
    assert test_plin_slave_1000.get_baudrate() == expected_baudrate
    assert test_plin_slave_1000.get_mode() == expected_mode
    test_plin_slave_1000.stop()


def test_set_id_filter(test_plin_slave_1000):
    expected_id_filter = bytearray([0xff] * 8)

    test_plin_slave_1000.set_id_filter(expected_id_filter)
    assert test_plin_slave_1000.get_id_filter() == expected_id_filter
    test_plin_slave_1000.stop()


def test_set_id_string(test_plin_slave_1000):
    expected_id_string = "test ID"

    test_plin_slave_1000.set_id_string(expected_id_string)
    assert test_plin_slave_1000.get_id_string() == expected_id_string
    test_plin_slave_1000.stop()


def test_identify(test_plin_slave_1000):
    test_plin_slave_1000.identify()
    test_plin_slave_1000.stop()


def test_get_firmware_version(test_plin_slave_1000):
    expected_num_subversions = 3

    version = test_plin_slave_1000.get_firmware_version()
    assert len(version.split('.')) == expected_num_subversions
    test_plin_slave_1000.stop()


def test_get_status(test_plin_slave_1000):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    status = test_plin_slave_1000.get_status()
    assert status["mode"] == expected_mode
    assert status["baudrate"] == expected_baudrate
    test_plin_slave_1000.stop()


def test_set_response_remap(test_plin_slave_1000):
    expected_remap = {1: 2}

    test_plin_slave_1000.set_response_remap(expected_remap)
    assert test_plin_slave_1000.response_remap[1] == 2
    assert test_plin_slave_1000.get_response_remap() == expected_remap
    test_plin_slave_1000.stop()


def test_set_led_state(test_plin_slave_1000):
    test_plin_slave_1000.set_led_state(enable=True)
    test_plin_slave_1000.stop()
