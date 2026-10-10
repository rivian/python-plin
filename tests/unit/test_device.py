from unittest.mock import MagicMock, patch

import pytest
from plin.enums import PLINFrameChecksumType, PLINFrameDirection, PLINFrameFlag
from plin.device import *


@pytest.fixture
def mock_ioctl():
    with patch('fcntl.ioctl', new_callable=MagicMock) as mock_ioctl:
        yield mock_ioctl


@pytest.fixture
def plin_master(mock_ioctl: MagicMock):
    plin = PLIN("/dev/plin0")
    plin.fd = MagicMock()
    mock_ioctl.reset_mock()

    yield plin, mock_ioctl


def test_reset(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.reset()
    assert len(mock_ioctl.mock_calls) == 1  # Check if ioctl was called


@pytest.mark.parametrize(
    "direction, flags, data",
    [
        (
            PLINFrameDirection.PUBLISHER,
            PLINFrameFlag.NONE,
            bytearray([0x01, 0x02, 0x03])
        ),
        (
            PLINFrameDirection.PUBLISHER,
            PLINFrameFlag.RSP_ENABLE,
            bytearray([0x01, 0x02, 0x03])
        ),
        (
            PLINFrameDirection.PUBLISHER,
            PLINFrameFlag.SINGLE_SHOT,
            bytearray([0x01, 0x02, 0x03])
        ),
        (
            PLINFrameDirection.PUBLISHER,
            PLINFrameFlag.RSP_ENABLE | PLINFrameFlag.SINGLE_SHOT,
            bytearray([0x01, 0x02, 0x03])
        ),
        (
            PLINFrameDirection.SUBSCRIBER,
            PLINFrameFlag.NONE,
            None
        ),
    ],
)
def test_set_frame_entry(
    plin_master,
    direction: PLINFrameDirection,
    flags: PLINFrameFlag,
    data: bytearray,
):
    plin, mock_ioctl = plin_master

    plin.set_frame_entry(
        0x22,
        direction=direction,
        checksum_type=PLINFrameChecksumType.CLASSIC,
        flags=flags,
        data=data,
        len=len(data) if data else 0,
    )

    mock_ioctl.assert_called_once()
    _, ioctl_num, arg = mock_ioctl.mock_calls[0].args

    assert ioctl_num == PLIOSETFRMENTRY
    assert arg.id == 0x22
    assert arg.direction == direction
    assert arg.checksum == PLINFrameChecksumType.CLASSIC
    assert arg.len == (len(data) if data else 0)

    if data:
        for i in range(len(data)):
            assert arg.d[i] == data[i]

    if direction == PLINFrameDirection.PUBLISHER:
        assert arg.flags == PLINFrameFlag.RSP_ENABLE | flags
    else:
        assert arg.flags == flags


def test_get_mode(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.get_mode()

    mock_ioctl.assert_called_once()
    _, ioctl_num, arg = mock_ioctl.mock_calls[0].args
    assert ioctl_num == PLIOGETMODE


def test_get_id_string(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.get_id_string()

    mock_ioctl.assert_called_once()
    _, ioctl_num, arg = mock_ioctl.mock_calls[0].args
    assert ioctl_num == PLIOGETIDSTR


def test_identify(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.identify()

    mock_ioctl.assert_called_once()
    _, ioctl_num = mock_ioctl.mock_calls[0].args
    assert ioctl_num == PLIOIDENTIFY


def test_get_firmware_version(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.get_firmware_version()

    mock_ioctl.assert_called_once()
    _, ioctl_num, arg = mock_ioctl.mock_calls[0].args
    assert ioctl_num == PLIOGETFWVER


def test_get_status(plin_master, mock_ioctl):
    plin, mock_ioctl = plin_master
    plin.get_status()

    mock_ioctl.assert_called_once()
    _, ioctl_num, arg = mock_ioctl.mock_calls[0].args
    assert ioctl_num == PLIOGETSTATUS


def _record(id: int, flags: int, data: bytes, msg_type: int = 0, length: int = 8) -> bytes:
    msg = PLINMessage(type=msg_type, flags=flags, id=id, len=length, dir=PLINFrameDirection.SUBSCRIBER,
                      cs_type=PLINFrameChecksumType.CLASSIC, ts_us=1234, data=bytearray(data))
    return bytes(msg)


def test_read_keeps_unanswered_header(plin_master):
    # A header no slave answers arrives with recessive 0xFF data and SLV_NOT_RSP | TIMEOUT set. It
    # used to be discarded as "invalid", which hid every empty poll from a passive logger.
    plin, _ = plin_master
    record = _record(0x3D, PLINFrameErrorFlag.SLV_NOT_RSP | PLINFrameErrorFlag.TIMEOUT, b"\xff" * 8)

    with patch("os.get_blocking", return_value=True), patch("os.set_blocking"), \
         patch("os.read", return_value=record):
        message = plin.read()

    assert message is not None
    assert message.id == 0x3D
    assert message.flags == (PLINFrameErrorFlag.SLV_NOT_RSP | PLINFrameErrorFlag.TIMEOUT)
    assert bytes(message.data) == b"\xff" * 8


def test_read_returns_non_frame_records(plin_master):
    plin, _ = plin_master
    record = _record(0x00, 0, b"\x00" * 8, msg_type=1, length=0)  # SLEEP

    with patch("os.get_blocking", return_value=True), patch("os.set_blocking"), \
         patch("os.read", return_value=record):
        message = plin.read()

    assert message is not None
    assert message.type == 1


def test_read_nonblocking_empty_returns_none(plin_master):
    plin, _ = plin_master

    with patch("os.get_blocking", return_value=True), patch("os.set_blocking") as set_blocking, \
         patch("os.read", side_effect=BlockingIOError):
        message = plin.read(block=False)

    assert message is None
    # Blocking mode is restored even when nothing was queued.
    set_blocking.assert_called_with(plin.fd, True)


def test_read_short_record_returns_none(plin_master):
    plin, _ = plin_master

    with patch("os.get_blocking", return_value=True), patch("os.set_blocking"), \
         patch("os.read", return_value=b"\x00" * 4):
        message = plin.read()

    assert message is None
