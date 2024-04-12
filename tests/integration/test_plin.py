import pytest
from plin.device import PLIN
from plin.enums import PLINMode, PLINMessageType, PLINFrameDirection, PLINFrameChecksumType
from plin.structs import *

@pytest.fixture
def plin_interface():
    return "/dev/plin0"


@pytest.fixture
def plin(plin_interface):
    return PLIN(plin_interface)


@pytest.fixture
def plin_slave_1000(plin):
    plin.start(mode=PLINMode.SLAVE, baudrate=1000)
    yield plin
    plin.stop()


@pytest.fixture
def plin_master_19200(plin):
    plin.start(mode=PLINMode.MASTER, baudrate=19200)
    yield plin
    plin.stop()


@pytest.fixture
def master_request_frame():
    return PLINMessage(type=PLINMessageType.FRAME,
                       id=0x3c,
                       len=8,
                       dir=PLINFrameDirection.PUBLISHER,
                       cs_type=PLINFrameChecksumType.CLASSIC,
                       data=bytearray([0x7f, 0x6, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]))


def test_start(plin_interface, plin):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    plin.start(mode=expected_mode, baudrate=expected_baudrate)
    assert plin.get_baudrate() == expected_baudrate
    assert plin.get_mode() == expected_mode
    plin.stop()


def test_read_nonblocking(plin_master_19200):
    assert None == plin_master_19200.read(block=False)


def test_write_master_request_frame(plin_master_19200, master_request_frame):
    plin_master_19200.write(master_request_frame)


def test_reset(plin_slave_1000):
    expected_baudrate = 0
    expected_mode = PLINMode.NONE

    plin_slave_1000.reset()
    assert plin_slave_1000.get_baudrate() == expected_baudrate
    assert plin_slave_1000.get_mode() == expected_mode


def test_set_id_filter(plin_slave_1000):
    expected_id_filter = bytearray([0xff] * 8)

    plin_slave_1000.set_id_filter(expected_id_filter)
    assert plin_slave_1000.get_id_filter() == expected_id_filter


def test_block_id(plin_slave_1000):
    expected_id_filter = bytearray([0xf0] + [0xff] * 7)

    plin_slave_1000.set_id_filter(bytearray([0xff] * 8))
    plin_slave_1000.block_id(0)
    plin_slave_1000.block_id(1)
    plin_slave_1000.block_id(2)
    plin_slave_1000.block_id(3)
    assert plin_slave_1000.get_id_filter() == expected_id_filter


def test_register_id(plin_slave_1000):
    expected_id_filter = bytearray([0x0f] + [0x0] * 7)

    plin_slave_1000.set_id_filter(bytearray([0x0] * 8))
    plin_slave_1000.register_id(0)
    plin_slave_1000.register_id(1)
    plin_slave_1000.register_id(2)
    plin_slave_1000.register_id(3)
    print(plin_slave_1000.get_id_filter())
    assert plin_slave_1000.get_id_filter() == expected_id_filter


def test_clear_id_filter_allow_all(plin_slave_1000):
    expected_id_filter = bytearray([0xff] * 8)

    plin_slave_1000.clear_id_filter(allow_all=True)
    assert plin_slave_1000.get_id_filter() == expected_id_filter


def test_clear_id_filter_block_all(plin_slave_1000):
    expected_id_filter = bytearray([0x0] * 8)

    plin_slave_1000.clear_id_filter(allow_all=False)
    assert plin_slave_1000.get_id_filter() == expected_id_filter


def test_set_id_string(plin_slave_1000):
    expected_id_string = "test ID"

    plin_slave_1000.set_id_string(expected_id_string)
    assert plin_slave_1000.get_id_string() == expected_id_string


def test_identify(plin_slave_1000):
    plin_slave_1000.identify()


def test_get_firmware_version(plin_slave_1000):
    expected_num_subversions = 3

    version = plin_slave_1000.get_firmware_version()
    assert len(version.split('.')) == expected_num_subversions


def test_get_status(plin_slave_1000):
    expected_baudrate = 1000
    expected_mode = PLINMode.SLAVE

    status = plin_slave_1000.get_status()
    assert status["mode"] == expected_mode
    assert status["baudrate"] == expected_baudrate


def test_set_response_remap(plin_slave_1000):
    expected_remap = {1: 2}
    plin_slave_1000.set_response_remap(expected_remap)
    assert plin_slave_1000.response_remap[1] == 2
    assert plin_slave_1000.get_response_remap() == expected_remap


def test_set_led_state(plin_slave_1000):
    plin_slave_1000.set_led_state(enable=True)
