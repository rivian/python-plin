import math
import os
from ctypes import *
from fcntl import ioctl
from typing import Dict, List, Union

from ioctl_opt import IO, IOW, IOWR

from plin.enums import *

PLIN_DAT_LEN = 8


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

    def __setattr__(self, name, value):
        if name == "data":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            super().__setattr__("len", len(value))
            super().__setattr__(name, buf)
        else:
            super().__setattr__(name, value)

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

    def __setattr__(self, name, value):
        if name == "d":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            super().__setattr__(name, buf)
        else:
            super().__setattr__(name, value)

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
        ("id_mask", c_uint8 * 8)
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
            result["usb_filter"] = bytearray([0] * 8)
        else:
            result["usb_filter"] = bytearray.fromhex(
                f"{self.usb_filter:x}").ljust(8, b'\x00')
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

    def __setattr__(self, name, value):
        if name == "d":
            buf = (c_uint8 * PLIN_DAT_LEN)(*value)
            super().__setattr__(name, buf)
        else:
            super().__setattr__(name, value)

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


PLIOHWINIT = IOW(ord('u'), 0, PLINUSBInitHardware)
PLIORSTHW = IO(ord('u'), 1)
PLIOSETFRMENTRY = IOW(ord('u'), 2, PLINUSBFrameEntry)
PLIOGETFRMENTRY = IOWR(ord('u'), 3, PLINUSBFrameEntry)
PLIOSTARTAUTOBAUD = IOWR(ord('u'), 4, PLINUSBAutoBaud)
PLIOGETBAUDRATE = IOWR(ord('u'), 5, PLINUSBGetBaudrate)
PLIOSETIDFILTER = IOW(ord('u'), 6, PLINUSBIDFilter)
PLIOGETIDFILTER = IOWR(ord('u'), 7, PLINUSBIDFilter)
PLIOGETMODE = IOWR(ord('u'), 8, PLINUSBGetMode)
PLIOSETIDSTR = IOW(ord('u'), 9, PLINUSBIDString)
PLIOGETIDSTR = IOWR(ord('u'), 10, PLINUSBIDString)
PLIOIDENTIFY = IO(ord('u'), 11)
PLIOGETFWVER = IOWR(ord('u'), 12, PLINUSBFirmwareVersion)
PLIOSTARTHB = IOWR(ord('u'), 13, PLINUSBKeepAlive)
PLIORESUMEHB = IOWR(ord('u'), 14, PLINUSBKeepAlive)
PLIOPAUSEHB = IOW(ord('u'), 15, PLINUSBKeepAlive)
PLIOADDSCHDSLOT = IOWR(ord('u'), 16, PLINUSBAddScheduleSlot)
PLIODELSCHD = IOWR(ord('u'), 17, PLINUSBDeleteSchedule)
PLIOGETSLOTSCNT = IOWR(ord('u'), 18, PLINUSBGetSlotCount)
PLIOGETSCHDSLOT = IOWR(ord('u'), 19, PLINUSBGetScheduleSlot)
PLIOSETSCHDBP = IOWR(ord('u'), 20, PLINUSBSetScheduleBreakpoint)
PLIOSTARTSCHD = IOWR(ord('u'), 21, PLINUSBStartSchedule)
PLIORESUMESCHD = IOWR(ord('u'), 22, PLINUSBResumeSchedule)
PLIOPAUSESCHD = IOWR(ord('u'), 23, PLINUSBSuspendSchedule)
PLIOGETSTATUS = IOWR(ord('u'), 24, PLINUSBGetStatus)
PLIORSTUSBTX = IO(ord('u'), 30)
PLIOCHGBYTEARRAY = IOW(ord('u'), 31, PLINUSBUpdateData)
PLIOXMTWAKEUP = IO(ord('u'), 33)
PLIOSETGETRSPMAP = IOWR(ord('u'), 39, PLINUSBResponseRemap)
PLIOSETLEDSTATE = IOW(ord('u'), 40, PLINUSBLEDState)


class PLIN:
    def __init__(self, interface: str):
        self.interface = interface
        self.fd = os.open(interface, os.O_RDWR)
        self.response_remap = [-1] * PLIN_USB_RSP_REMAP_ID_LEN

        self.reset()

    def start(self, mode: PLINMode, baudrate: int = 19200):
        '''
        Connects to and configures the PLIN device with the specified mode and baudrate.
        '''
        self.mode = mode
        self.baudrate = baudrate

        buffer = PLINUSBInitHardware(self.baudrate, self.mode, 0)
        ioctl(self.fd, PLIOHWINIT, buffer)

    def stop(self):
        '''
        Closes connection to the PLIN device.
        '''
        os.close(self.fd)

    def reset(self):
        '''
        Resets the PLIN device.
        '''
        ioctl(self.fd, PLIORSTHW)

    def set_frame_entry(self, 
                        id: int,
                        direction: PLINFrameDirection,
                        checksum_type: PLINFrameChecksumType,
                        flags: PLINFrameFlag = PLINFrameFlag.NONE,
                        data: bytearray = None,
                        len: int = 0):
        '''
        Adds a frame entry for the specified ID.

        IMPORTANT NOTE: For a publisher frame, the flag PLINFrameFlag.RSP_ENABLE must be set in order to allow a slave response.
        This flag is set by default if the frame direction is publisher for convenience.
        '''
        buffer = PLINUSBFrameEntry(
            id=id, direction=direction, checksum=checksum_type)
        if direction == PLINFrameDirection.PUBLISHER:
            buffer.flags = flags & PLINFrameFlag.RSP_ENABLE
        if data:
            buffer.d = data
        if len > 0:
            buffer.len = len
        ioctl(self.fd, PLIOSETFRMENTRY, buffer)

    def set_frame_entry_data(self, id: int, index: int, data: bytearray, len: int):
        '''
        Sets or updates the data for the frame entry corresponding to the specified ID.
        '''
        buffer = PLINUSBUpdateData(id=id, idx=index, d=data, len=len)
        ioctl(self.fd, PLIOCHGBYTEARRAY, buffer)

    def get_frame_entry(self, id: int) -> PLINUSBFrameEntry:
        '''
        Gets the frame entry corresponding to the specified ID.
        '''
        buffer = PLINUSBFrameEntry(id=id)
        ioctl(self.fd, PLIOGETFRMENTRY, buffer)
        return buffer

    def start_autobaud(self, timeout: int) -> int:
        '''
        Starts process to detect the baudrate of the connected LIN bus.

        IMPORTANT NOTE: The LIN hardware must not be active (i.e. start() has not been called yet).
        '''
        buffer = PLINUSBAutoBaud(timeout=timeout)
        ioctl(self.fd, PLIOSTARTAUTOBAUD, buffer)
        return buffer.err

    def get_baudrate(self) -> int:
        '''
        Gets the baudrate.
        '''
        buffer = PLINUSBGetBaudrate()
        ioctl(self.fd, PLIOGETBAUDRATE, buffer)
        return buffer.baudrate

    def set_id_filter(self, filter: bytearray):
        '''
        Sets the ID filter.
        '''
        buffer = PLINUSBIDFilter()
        buffer.id_mask = (c_ubyte * 8)(*filter.ljust(8, b'\x00'))
        ioctl(self.fd, PLIOSETIDFILTER, buffer)

    def get_id_filter(self) -> bytearray:
        '''
        Gets the ID filter.
        '''
        buffer = PLINUSBIDFilter()
        ioctl(self.fd, PLIOGETIDFILTER, buffer)
        return bytearray(buffer.id_mask)

    def get_mode(self) -> PLINMode:
        '''
        Gets the mode.
        '''
        buffer = PLINUSBGetMode()
        ioctl(self.fd, PLIOGETMODE, buffer)
        return PLINMode(buffer.mode)

    def set_id_string(self, id_string: str):
        '''
        Sets the ID string.
        '''
        buffer = PLINUSBIDString()
        buffer.str = id_string.encode("utf-8")
        ioctl(self.fd, PLIOSETIDSTR, buffer)

    def get_id_string(self) -> str:
        '''
        Gets the ID string.
        '''
        buffer = PLINUSBIDString()
        ioctl(self.fd, PLIOGETIDSTR, buffer)
        return buffer.str.decode("utf-8")

    def identify(self):
        '''
        Identifies the PLIN device by flashing the LED.
        '''
        ioctl(self.fd, PLIOIDENTIFY)

    def get_firmware_version(self) -> str:
        '''
        Gets the firmware version.
        '''
        buffer = PLINUSBFirmwareVersion()
        ioctl(self.fd, PLIOGETFWVER, buffer)
        return '.'.join([str(buffer.major), str(buffer.minor), str(buffer.sub)])

    def start_keep_alive(self, id: int, period_ms: int) -> int:
        '''
        Sets the specified ID as a keep-alive frame and starts sending it with the specified period.
        '''
        buffer = PLINUSBKeepAlive(id=id, period_ms=period_ms)
        ioctl(self.fd, PLIOSTARTHB, buffer)
        return buffer.err

    def resume_keep_alive(self) -> int:
        '''
        Resumes the sending of keep-alive frames.
        '''
        buffer = PLINUSBKeepAlive()
        ioctl(self.fd, PLIORESUMEHB, buffer)
        return buffer.err

    def suspend_keep_alive(self) -> int:
        '''
        Suspends the sending of keep-alive frames.
        '''
        buffer = PLINUSBKeepAlive()
        ioctl(self.fd, PLIOPAUSEHB, buffer)
        return buffer.err

    def add_unconditional_schedule_slot(self, schedule: int, delay_ms: int, id: int) -> int:
        '''
        Adds an unconditional schedule slot for the specified ID.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        if id > PLINFrameID.UNC_MAX:
            raise ValueError(
                f"ID {id} out of range [{PLINFrameID.UNC_MIN}..{PLINFrameID.UNC_MAX}].")
        buffer = PLINUSBAddScheduleSlot(
            schedule=schedule, delay=delay_ms, type=PLINUSBSlotType.UNCOND)
        # ID idx 1 - 7 reserved for sporadic frames only.
        buffer.id[0] = id
        ioctl(self.fd, PLIOADDSCHDSLOT, buffer)
        return buffer.err

    def add_event_triggered_schedule_slot(self, schedule: int, delay_ms: int, id: int, count_resolve: int):
        '''
        Adds an event-triggered schedule slot for the specified ID.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        if id > PLINFrameID.UNC_MAX:
            raise ValueError(
                f"ID {id} out of range [{PLINFrameID.UNC_MIN}..{PLINFrameID.UNC_MAX}].")
        if count_resolve > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Resolve schedule {count_resolve} out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")

        buffer = PLINUSBAddScheduleSlot(
            schedule=schedule, delay=delay_ms, type=PLINUSBSlotType.EVENT, count_resolve=count_resolve)
        # ID idx 1 - 7 reserved for sporadic frames only.
        buffer.id[0] = id
        ioctl(self.fd, PLIOADDSCHDSLOT, buffer)
        return buffer.err

    def add_sporadic_schedule_slot(self, schedule: int, delay_ms: int, ids: List[int], count_resolve: int):
        '''
        Adds a sporadic schedule slot for the specified ID.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        if len(ids) < PLINUSBSlotNumber.MIN or len(ids) > PLINUSBSlotNumber.MAX:
            raise ValueError(
                f"Invalid number of IDs [{PLINUSBSlotNumber.MIN}..{PLINUSBSlotNumber.MAX}].")
        for id in ids:
            if id > PLINFrameID.UNC_MAX:
                raise ValueError(
                    f"ID {id} out of range [{PLINFrameID.UNC_MIN}..{PLINFrameID.UNC_MAX}].")

        buffer = PLINUSBAddScheduleSlot(
            schedule=schedule, delay=delay_ms, type=PLINUSBSlotType.SPORADIC, count_resolve=count_resolve)
        buffer.id = (c_uint8 * PLINUSBSlotNumber.MAX)(*ids)
        ioctl(self.fd, PLIOADDSCHDSLOT, buffer)
        return buffer.err

    def add_diagnostic_schedule_slot(self, schedule: int, delay_ms: int, type: PLINUSBSlotType):
        '''
        Generic function for adding a diagnostic schedule slot (either master request or slave response).
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBAddScheduleSlot(
            schedule=schedule, delay=delay_ms, type=type)
        # ID idx 1 - 7 reserved for sporadic frames only.
        buffer.id[0] = PLINFrameID.DIAG_MASTER_REQ if type == PLINUSBSlotType.MASTER_REQ else PLINFrameID.DIAG_SLAVE_RSP
        ioctl(self.fd, PLIOADDSCHDSLOT, buffer)
        return buffer.err

    def add_master_request_schedule_slot(self, schedule: int, delay_ms: int):
        '''
        Adds a master request schedule slot.
        '''
        return self.add_diagnostic_schedule_slot(schedule=schedule, delay_ms=delay_ms, type=PLINUSBSlotType.MASTER_REQ)

    def add_slave_response_schedule_slot(self, schedule: int, delay_ms: int):
        '''
        Adds a slave response schedule slot.
        '''
        return self.add_diagnostic_schedule_slot(schedule=schedule, delay_ms=delay_ms, type=PLINUSBSlotType.SLAVE_RSP)

    def delete_schedule(self, schedule: int) -> int:
        '''
        Removes all slots in the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBDeleteSchedule(schedule=schedule)
        ioctl(self.fd, PLIODELSCHD, buffer)
        return buffer.err

    def get_slot_count(self, schedule: int) -> int:
        '''
        Gets the number of slots in the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBGetSlotCount(schedule=schedule)
        ioctl(self.fd, PLIOGETSLOTSCNT, buffer)
        return buffer.count

    def get_schedule_slots(self, schedule: int) -> List[Dict[str, Union[int, bytearray]]]:
        '''
        Gets the slots in a specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")

        count = self.get_slot_count(schedule)
        result = []
        for i in range(count):
            buffer = PLINUSBGetScheduleSlot(schedule=schedule, slot_idx=i)
            ioctl(self.fd, PLIOGETSCHDSLOT, buffer)
            result.append(buffer._asdict())
        return result

    def set_schedule_breakpoint(self, handle: int, enable: bool = True):
        '''
        Enables or disables a breakpoint on a schedule slot with the given handle.
        '''
        buffer = PLINUSBSetScheduleBreakpoint(brkpt=int(enable), handle=handle)
        ioctl(self.fd, PLIOSETSCHDBP, buffer)

    def start_schedule(self, schedule: int) -> int:
        '''
        Starts the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBStartSchedule(schedule=schedule)
        ioctl(self.fd, PLIOSTARTSCHD, buffer)
        return buffer.err

    def resume_schedule(self) -> int:
        '''
        Resumes the specified schedule.
        '''
        buffer = PLINUSBResumeSchedule()
        ioctl(self.fd, PLIORESUMESCHD, buffer)
        return buffer.err

    def suspend_schedule(self, schedule: int) -> int:
        '''
        Suspends the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBSuspendSchedule(schedule=schedule)
        ioctl(self.fd, PLIOPAUSESCHD, buffer)
        return buffer.err

    def get_status(self) -> Dict[str, int]:
        '''
        Gets the status of the PLIN device.
        '''
        buffer = PLINUSBGetStatus()
        ioctl(self.fd, PLIOGETSTATUS, buffer)
        return buffer._asdict()

    def reset_tx_queue(self):
        '''
        Resets the outgoing queue.
        '''
        ioctl(self.fd, PLIORSTUSBTX)

    def wakeup(self):
        '''
        Wakes up the LIN bus.
        '''
        ioctl(self.fd, PLIOXMTWAKEUP)

    def set_response_remap(self, id_map: Dict[int, int]):
        '''
        Sets the publisher response remap. Only valid in slave mode. Setting the remap will override the old mapping. 
        All pending responses for single shot frames will be killed and therefore be lost.

        An example remapping of ID x to ID y: when ID x is received, the frame settings are taken from ID x, but the data itself is taken from ID y.
        '''
        if self.mode != PLINMode.SLAVE:
            raise Exception("Response remap only valid in slave mode.")
        buffer = PLINUSBResponseRemap()
        buffer.set_get = PLINUSBResponseRemapType.SET

        for id, v in id_map.items():
            if id < PLINFrameID.MIN or id > PLINFrameID.MAX:
                raise ValueError(
                    f"ID key {id} out of range [{PLINFrameID.MIN}..{PLINFrameID.MAX}].")
            if v < PLINFrameID.MIN or v > PLINFrameID.MAX:
                raise ValueError(
                    f"ID value {v} out of range [{PLINFrameID.MIN}..{PLINFrameID.MAX}].")
            self.response_remap[id] = v

        for i in range(PLIN_USB_RSP_REMAP_ID_LEN):
            if self.response_remap[i] >= 0:
                buffer.id[i] = self.response_remap[i]
        ioctl(self.fd, PLIOSETGETRSPMAP, buffer)

    def get_visual_response_remap(self, buffer_id_map: List[int]) -> str:
        '''
        Builds a visual representation of remapped IDs.
        '''
        output = "\nID  "
        side = int(math.sqrt(PLIN_USB_RSP_REMAP_ID_LEN))
        for i in range(side):
            output += f"{i:2d} "
        output += "\n---+--+--+--+--+--+--+--+--\n"
        for i in range(side):
            output += f"{i*8:2d}  "
            for j in range(side):
                output += f"{buffer_id_map[i*8 + j]:02x} "
            output += "\n"
        return output

    def get_response_remap(self, visual_output: bool = False) -> Dict[int, int]:
        '''
        Gets the publisher response remap.
        '''
        if self.mode != PLINMode.SLAVE:
            raise Exception("Response remap only valid in slave mode.")
        buffer = PLINUSBResponseRemap()
        buffer.set_get = PLINUSBResponseRemapType.GET
        ioctl(self.fd, PLIOSETGETRSPMAP, buffer)

        if visual_output:
            print(self.get_visual_response_remap(buffer.id))

        remap = {i: buffer.id[i]
                 for i in range(len(buffer.id)) if buffer.id[i] != 0}
        return remap

    def set_led_state(self, enable: bool):
        '''
        Sets the state of the LED on the PLIN device.
        '''
        buffer = PLINUSBLEDState(on_off=int(enable))
        ioctl(self.fd, PLIOSETLEDSTATE, buffer)

    def read(self) -> PLINMessage:
        '''
        Reads a PLINMessage from the LIN bus.
        '''
        result = os.read(self.fd, PLINMessage.buffer_length)
        return PLINMessage.from_buffer_copy(result)

    def write(self, message: PLINMessage):
        '''
        Writes a PLINMessage to the LIN bus.
        '''
        buffer = bytearray(message)
        os.write(self.fd, buffer)
