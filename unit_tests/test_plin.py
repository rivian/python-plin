import pytest
import time
from plin.enums import PLINMode, PLINMessageType, PLINFrameDirection, PLINFrameChecksumType
from plin.plin import PLIN, PLINMessage


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


@pytest.fixture
def test_plin_master_19200(test_plin):
    test_plin.start(mode=PLINMode.MASTER, baudrate=19200)
    return test_plin


@pytest.fixture
def test_master_request_frame():
    return PLINMessage(type=PLINMessageType.FRAME,
                       id=0x3c,
                       len=8,
                       dir=PLINFrameDirection.PUBLISHER,
                       cs_type=PLINFrameChecksumType.CLASSIC,
                       data=bytearray([0x7f, 0x6, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]))


def test_read_timeout(test_plin_master_19200):
    # test 1 second timeout
    expected_timeout = 1
    start = time.time()
    test_plin_master_19200.read(timeout=expected_timeout)
    diff = time.time() - start
    assert diff >= expected_timeout
    assert diff < expected_timeout + 1


def test_write_master_request_frame(test_plin_master_19200, test_master_request_frame):
    test_plin_master_19200.write(test_master_request_frame)


def test_start(test_plin):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    test_plin.start(mode=expected_mode, baudrate=expected_baudrate)
    assert test_plin.get_baudrate() == expected_baudrate
    assert test_plin.get_mode() == expected_mode


def test_reset(test_plin_slave_1000):
    expected_baudrate = 0
    expected_mode = PLINMode.NONE

    test_plin_slave_1000.reset()
    assert test_plin_slave_1000.get_baudrate() == expected_baudrate
    assert test_plin_slave_1000.get_mode() == expected_mode


def test_set_id_filter(test_plin_slave_1000):
    expected_id_filter = bytearray([0xff] * 8)

    test_plin_slave_1000.set_id_filter(expected_id_filter)
    assert test_plin_slave_1000.get_id_filter() == expected_id_filter


def test_set_id_string(test_plin_slave_1000):
    expected_id_string = "test ID"

    test_plin_slave_1000.set_id_string(expected_id_string)
    assert test_plin_slave_1000.get_id_string() == expected_id_string


def test_identify(test_plin_slave_1000):
    test_plin_slave_1000.identify()


def test_get_firmware_version(test_plin_slave_1000):
    expected_num_subversions = 3

    version = test_plin_slave_1000.get_firmware_version()
    assert len(version.split('.')) == expected_num_subversions


def test_get_status(test_plin_slave_1000):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    status = test_plin_slave_1000.get_status()
    assert status["mode"] == expected_mode
    assert status["baudrate"] == expected_baudrate


def test_set_response_remap(test_plin_slave_1000):
    expected_remap = {1: 2}
    test_plin_slave_1000.set_response_remap(expected_remap)
    assert test_plin_slave_1000.response_remap[1] == 2
    assert test_plin_slave_1000.get_response_remap() == expected_remap


def test_set_led_state(test_plin_slave_1000):
    test_plin_slave_1000.set_led_state(enable=True)
