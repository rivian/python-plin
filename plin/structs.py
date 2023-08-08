
from ctypes import *
from typing import Any, Union

from plin.enums import *

PLIN_USB_FILTER_LEN = 8
PLIN_DAT_LEN = 8
PLIN_EMPTY_DATA = b'\xff' * PLIN_DAT_LEN


class PLINMessage(Structure):
    '''
    Class representing a LIN message. 
    '''
    buffer_length = 32
    _fields_ = [
        ("type", c_uint16),
        ("flags", c_uint16),
        ("id", c_uint8),
        ("len", c_uint8),
        ("dir", c_uint8),
        ("cs_type", c_uint8),
        ("ts_us", c_uint64),
        ("data", c_uint8 * PLIN_DAT_LEN),
        ("reserved", c_uint8 * 8)
    ]

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            return super().__setattr__(name, buf)
        else:
            return super().__setattr__(name, value)

    def __repr__(self) -> str:
        return str(self._asdict())

    def _asdict(self) -> dict:
        result = {field[0]: getattr(self, field[0])
                  for field in self._fields_[:-2]}
        result["type"] = PLINMessageType(self.type)
        result["dir"] = PLINFrameDirection(self.dir)
        result["flags"] = PLINFrameFlag(self.flags)
        result["cs_type"] = PLINFrameChecksumType(self.cs_type)
        result["data"] = bytearray(self.data)
        return result


class PLINUSBInitHardware(Structure):
    _fields_ = [
        ("baudrate", c_uint16),
        ("mode", c_uint8),
        ("unused", c_uint8)
    ]


class PLINUSBFrameEntry(Structure):
    _fields_ = [
        ("id", c_uint8),
        ("len", c_uint8),
        ("direction", c_uint8),
        ("checksum", c_uint8),
        ("flags", c_uint16),
        ("unused", c_uint16),
        ("d", c_uint8 * PLIN_DAT_LEN)
    ]

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "d":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            return super().__setattr__(name, buf)
        else:
            return super().__setattr__(name, value)

    def __repr__(self) -> str:
        return str(self._asdict())

    def _asdict(self) -> dict:
        result = {field: getattr(self, field)
                  for field, _ in self._fields_}
        result["direction"] = PLINFrameDirection(self.direction)
        result["checksum"] = PLINFrameChecksumType(self.checksum)
        result["flags"] = PLINFrameFlag(self.flags)
        result["d"] = bytearray(self.d)
        del result["unused"]
        return result


class PLINUSBAutoBaud(Structure):
    _fields_ = [
        ("timeout", c_uint16),
        ("err", c_uint8),
        ("unused", c_uint8)
    ]


class PLINUSBGetBaudrate(Structure):
    _fields_ = [
        ("baudrate", c_uint16),
        ("unused", c_uint16)
    ]


class PLINUSBIDFilter(Structure):
    _fields_ = [
        ("id_mask", c_uint8 * PLIN_USB_FILTER_LEN)
    ]


class PLINUSBGetMode(Structure):
    _fields_ = [
        ("mode", c_uint8),
        ("unused", c_uint8 * 3)
    ]


class PLINUSBIDString(Structure):
    _fields_ = [
        ("str", c_char * 48)
    ]


class PLINUSBFirmwareVersion(Structure):
    _fields_ = [
        ("major", c_uint8),
        ("minor", c_uint8),
        ("sub", c_uint16)
    ]


class PLINUSBKeepAlive(Structure):
    _fields_ = [
        ("err", c_uint8),
        ("id", c_uint8),
        ("period_ms", c_uint16)
    ]


class PLINUSBAddScheduleSlot(Structure):
    _fields_ = [
        ("schedule", c_uint8),
        ("err", c_uint8),
        ("unused", c_uint16),
        ("type", c_uint8),              # PLIN_USB_SLOT_xxx
        ("count_resolve", c_uint8),
        ("delay", c_uint16),
        ("id", c_uint8 * PLINUSBSlotNumber.MAX),
        ("handle", c_uint32)
    ]


class PLINUSBDeleteSchedule(Structure):
    _fields_ = [
        ("schedule", c_uint8),
        ("err", c_uint8),
        ("unused", c_uint16),
    ]


class PLINUSBGetSlotCount(Structure):
    _fields_ = [
        ("schedule", c_uint8),
        ("unused", c_uint8),
        ("count", c_uint16)
    ]


class PLINUSBGetScheduleSlot(Structure):
    _fields_ = [
        ("schedule", c_uint8),          # schedule from which the slot is returned
        ("slot_idx", c_uint8),          # slot index returned
        ("err", c_uint8),               # if 1, no schedule present
        ("unused", c_uint8),
        ("type", c_uint8),              # PLIN_USB_SLOT_xxx
        ("count_resolve", c_uint8),
        ("delay", c_uint16),
        ("id", c_uint8 * PLINUSBSlotNumber.MAX),
        ("handle", c_uint32)
    ]

    def __repr__(self) -> str:
        return str(self._asdict())

    def _asdict(self) -> dict:
        result = {field: getattr(self, field)
                  for field, _ in self._fields_}
        result["type"] = PLINUSBSlotType(self.type)
        result["id"] = list(self.id)
        del result["unused"]
        return result


class PLINUSBSetScheduleBreakpoint(Structure):
    _fields_ = [
        ("brkpt", c_uint8),             # either 0 or 1
        ("unused", c_uint8 * 3),
        ("handle", c_uint32)            # slot handle returned
    ]


class PLINUSBStartSchedule(Structure):
    _fields_ = [
        ("schedule", c_uint8),
        ("err", c_uint8),
        ("unused", c_uint16),
    ]


class PLINUSBResumeSchedule(Structure):
    _fields_ = [
        ("err", c_uint8),               # if 1, not master / no schedule started
        ("unused", c_uint8 * 3),
    ]


class PLINUSBSuspendSchedule(Structure):
    _fields_ = [
        ("err", c_uint8),
        ("schedule", c_uint8),          # suspended schedule index [0..7]
        ("unused", c_uint8 * 2),
        ("handle", c_uint32)
    ]


class PLINUSBGetStatus(Structure):
    _fields_ = [
        ("mode", c_uint8),
        ("tx_qfree", c_uint8),
        ("schd_poolfree", c_uint16),
        ("baudrate", c_uint16),
        ("usb_rx_ovr", c_uint16),       # USB data overrun counter
        ("usb_filter", c_uint64),
        ("bus_state", c_uint8),
        ("unused", c_uint8 * 3)
    ]

    def __repr__(self) -> str:
        return str(self._asdict())

    def _asdict(self) -> dict:
        result = {field: getattr(self, field)
                  for field, _ in self._fields_}
        result["mode"] = PLINMode(self.mode)
        if self.usb_filter == 0:
            result["usb_filter"] = bytearray([0] * PLIN_USB_FILTER_LEN)
        else:
            result["usb_filter"] = bytearray.fromhex(
                f"{self.usb_filter:x}").ljust(PLIN_USB_FILTER_LEN, b'\x00')
        result["bus_state"] = PLINBusState(self.bus_state)
        del result["unused"]
        return result


class PLINUSBUpdateData(Structure):
    _fields_ = [
        ("id", c_uint8),                # frame ID to update [0..63]
        ("len", c_uint8),               # count of data bytes to update [1..8]
        ("idx", c_uint8),               # data offset [0..7]
        ("unused", c_uint8),
        ("d", c_uint8 * PLIN_DAT_LEN)   # new data bytes
    ]

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "d":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            return super().__setattr__(name, buf)
        else:
            return super().__setattr__(name, value)

    def __repr__(self) -> str:
        return str(self._asdict())

    def _asdict(self) -> dict:
        result = {field: getattr(self, field)
                  for field, _ in self._fields_}
        result["d"] = bytearray(result["d"])
        del result["unused"]
        return result


PLIN_USB_RSP_REMAP_ID_LEN = (PLINFrameID.MAX - PLINFrameID.MIN + 1)


class PLINUSBResponseRemap(Structure):
    _fields_ = [
        ("set_get", c_uint8),
        ("unused", c_uint8 * 3),
        ("id", c_uint8 * PLIN_USB_RSP_REMAP_ID_LEN)
    ]


class PLINUSBLEDState(Structure):
    _fields_ = [
        ("on_off", c_uint8),            # PLIN_USB_LEDS_xxx
        ("unused", c_uint8 * 3)
    ]
