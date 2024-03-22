import sys
from unittest.mock import patch, MagicMock

import pytest

from plin.enums import (
    PLINMode,
    PLINFrameDirection,
    PLINFrameChecksumType,
    PLINFrameFlag,
)

FCNTL_MOD_NAME = "fcntl"


class TestUnitPLIN:
    @pytest.fixture(scope="class")
    def mock_fcntl_mod(self):
        """Mock the fcntl module

        The module does not exist on Windows, but the unit test should be runnable
        on any system.
        """
        has_module = FCNTL_MOD_NAME in sys.modules
        orig = sys.modules.get(FCNTL_MOD_NAME)

        fcntl_mock = sys.modules[FCNTL_MOD_NAME] = MagicMock()
        yield fcntl_mock

        if has_module:
            sys.modules[FCNTL_MOD_NAME] = orig
        else:
            del sys.modules[FCNTL_MOD_NAME]

    @pytest.fixture
    def plin_master_unit(self, mock_fcntl_mod: MagicMock):
        """Create a PLIN master object with mocked fopen and ioctl"""

        # We must import here after fcntl has been mocked
        # because the module does not exist on Windows
        from plin.device import PLIN

        plin = PLIN("/dev/plin0")
        with patch("os.open") as mock_open:
            mock_ioctl = mock_fcntl_mod.ioctl
            plin.start(PLINMode.MASTER)

            mock_open.reset_mock()
            mock_ioctl.reset_mock()

            yield plin, mock_open, mock_ioctl

    @pytest.mark.parametrize("data", (None, bytearray(b"1234")))
    @pytest.mark.parametrize(
        "flags, direction",
        [
            (PLINFrameFlag.NONE, PLINFrameDirection.PUBLISHER),
            (PLINFrameFlag.SINGLE_SHOT, PLINFrameDirection.PUBLISHER),
            (PLINFrameFlag.NONE, PLINFrameDirection.SUBSCRIBER),
        ],
    )
    def test_set_frame_entry(
        self,
        plin_master_unit,
        data: bytearray,
        flags: PLINFrameFlag,
        direction: PLINFrameDirection,
    ):
        plin, mock_open, mock_ioctl = plin_master_unit

        plin.set_frame_entry(
            0x22,
            direction=direction,
            checksum_type=PLINFrameChecksumType.CLASSIC,
            flags=flags,
            data=data,
            len=len(data) if data else 0,
        )

        assert len(mock_ioctl.mock_calls) == 1
        fd, ioctl_num, arg = mock_ioctl.mock_calls[0].args

        assert ioctl_num == 1074820354
        assert arg.id == 0x22
        assert arg.direction == direction
        assert arg.checksum == PLINFrameChecksumType.CLASSIC
        assert arg.len == (len(data) if data else 0)

        # We just compare the first data byte
        if data is not None:
            assert arg.d[0] == data[0]
        else:
            assert arg.d[0] == 0

        if direction == PLINFrameDirection.PUBLISHER:
            assert arg.flags == PLINFrameFlag.RSP_ENABLE | flags
        else:
            assert arg.flags == flags
