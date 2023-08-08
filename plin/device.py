import fcntl
import math
import os
from ctypes import *
from typing import Any, Dict, List, Union

from ioctl_opt import IO, IOW, IOWR

from plin.enums import *
from plin.structs import *

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
        self.response_remap = [-1] * PLIN_USB_RSP_REMAP_ID_LEN
        self.fd = None

    def _ioctl(self, *args, **kwargs):
        '''
        Generic ioctl function to wrap open/closing the file descriptor.
        '''
        if self.fd:
            try:
                fcntl.ioctl(self.fd, *args, **kwargs)
            except:
                print("File descriptor busy!")
        else:
            raise Exception("PLIN not connected!")

    def reset(self):
        '''
        Resets the PLIN device.
        '''
        self._ioctl(PLIORSTHW)

    def start(self, mode: PLINMode, baudrate: int = 19200):
        '''
        Connects to and configures the PLIN device with the specified mode and baudrate.
        '''
        self.mode = mode
        self.baudrate = baudrate

        if not self.fd:
            self.fd = os.open(self.interface, os.O_RDWR)

        self.reset()
        buffer = PLINUSBInitHardware(self.baudrate, self.mode, 0)
        self._ioctl(PLIOHWINIT, buffer)

    def stop(self):
        '''
        Disconnects from the PLIN device by closing the file descriptor.
        '''
        if self.fd:
            os.close(self.fd)

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
        self._ioctl(PLIOSETFRMENTRY, buffer)

    def set_frame_entry_data(self, id: int, index: int, data: bytearray, len: int):
        '''
        Sets or updates the data for the frame entry corresponding to the specified ID.
        '''
        buffer = PLINUSBUpdateData(id=id, idx=index, d=data, len=len)
        self._ioctl(PLIOCHGBYTEARRAY, buffer)

    def get_frame_entry(self, id: int) -> PLINUSBFrameEntry:
        '''
        Gets the frame entry corresponding to the specified ID.
        '''
        buffer = PLINUSBFrameEntry(id=id)
        self._ioctl(PLIOGETFRMENTRY, buffer)
        return buffer

    def start_autobaud(self, timeout: int) -> int:
        '''
        Starts process to detect the baudrate of the connected LIN bus.

        IMPORTANT NOTE: The LIN hardware must not be active (i.e. start() has not been called yet).
        '''
        buffer = PLINUSBAutoBaud(timeout=timeout)
        self._ioctl(PLIOSTARTAUTOBAUD, buffer)
        return buffer.err

    def get_baudrate(self) -> int:
        '''
        Gets the baudrate.
        '''
        buffer = PLINUSBGetBaudrate()
        self._ioctl(PLIOGETBAUDRATE, buffer)
        return buffer.baudrate

    def set_id_filter(self, filter: bytearray):
        '''
        Sets the ID filter.
        '''
        buffer = PLINUSBIDFilter()
        buffer.id_mask = (c_ubyte * PLIN_USB_FILTER_LEN)(*
                                                         filter.ljust(PLIN_USB_FILTER_LEN, b'\x00'))
        self._ioctl(PLIOSETIDFILTER, buffer)

    def get_id_filter(self) -> bytearray:
        '''
        Gets the ID filter.
        '''
        buffer = PLINUSBIDFilter()
        self._ioctl(PLIOGETIDFILTER, buffer)
        return bytearray(buffer.id_mask)

    def block_id(self, id: int):
        '''
        Add ID to filter (block ID).
        '''
        if id > PLINFrameID.MAX or id < PLINFrameID.MIN:
            raise ValueError(
                f"ID {id} out of range [{PLINFrameID.MIN}..{PLINFrameID.MAX}].")
        current_filter = int.from_bytes(self.get_id_filter(), 'little')
        mask = ~(1 << id)
        current_filter &= mask
        self.set_id_filter(current_filter.to_bytes(
            PLIN_USB_FILTER_LEN, 'little'))

    def register_id(self, id: int):
        '''
        Remove ID from filter (allow ID through).
        '''
        if id > PLINFrameID.MAX or id < PLINFrameID.MIN:
            raise ValueError(
                f"ID {id} out of range [{PLINFrameID.MIN}..{PLINFrameID.MAX}].")
        current_filter = int.from_bytes(self.get_id_filter(), 'little')
        mask = (1 << id)
        current_filter |= mask
        self.set_id_filter(current_filter.to_bytes(
            PLIN_USB_FILTER_LEN, 'little'))

    def clear_id_filter(self, allow_all=True):
        '''
        Clear ID filter to either allow all IDs or disallow all IDs.
        '''
        if allow_all:
            self.set_id_filter(bytearray([0xff] * PLIN_USB_FILTER_LEN))
        else:
            self.set_id_filter(bytearray([0] * PLIN_USB_FILTER_LEN))

    def get_mode(self) -> PLINMode:
        '''
        Gets the mode.
        '''
        buffer = PLINUSBGetMode()
        self._ioctl(PLIOGETMODE, buffer)
        return PLINMode(buffer.mode)

    def set_id_string(self, id_string: str):
        '''
        Sets the ID string.
        '''
        buffer = PLINUSBIDString()
        buffer.str = id_string.encode("utf-8")
        self._ioctl(PLIOSETIDSTR, buffer)

    def get_id_string(self) -> str:
        '''
        Gets the ID string.
        '''
        buffer = PLINUSBIDString()
        self._ioctl(PLIOGETIDSTR, buffer)
        return buffer.str.decode("utf-8")

    def identify(self):
        '''
        Identifies the PLIN device by flashing the LED.
        '''
        self._ioctl(PLIOIDENTIFY)

    def get_firmware_version(self) -> str:
        '''
        Gets the firmware version.
        '''
        buffer = PLINUSBFirmwareVersion()
        self._ioctl(PLIOGETFWVER, buffer)
        return '.'.join([str(buffer.major), str(buffer.minor), str(buffer.sub)])

    def start_keep_alive(self, id: int, period_ms: int) -> int:
        '''
        Sets the specified ID as a keep-alive frame and starts sending it with the specified period.
        '''
        buffer = PLINUSBKeepAlive(id=id, period_ms=period_ms)
        self._ioctl(PLIOSTARTHB, buffer)
        return buffer.err

    def resume_keep_alive(self) -> int:
        '''
        Resumes the sending of keep-alive frames.
        '''
        buffer = PLINUSBKeepAlive()
        self._ioctl(PLIORESUMEHB, buffer)
        return buffer.err

    def suspend_keep_alive(self) -> int:
        '''
        Suspends the sending of keep-alive frames.
        '''
        buffer = PLINUSBKeepAlive()
        self._ioctl(PLIOPAUSEHB, buffer)
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
        self._ioctl(PLIOADDSCHDSLOT, buffer)
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
        self._ioctl(PLIOADDSCHDSLOT, buffer)
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
        self._ioctl(PLIOADDSCHDSLOT, buffer)
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
        self._ioctl(PLIOADDSCHDSLOT, buffer)
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
        self._ioctl(PLIODELSCHD, buffer)
        return buffer.err

    def get_slot_count(self, schedule: int) -> int:
        '''
        Gets the number of slots in the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBGetSlotCount(schedule=schedule)
        self._ioctl(PLIOGETSLOTSCNT, buffer)
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
            self._ioctl(PLIOGETSCHDSLOT, buffer)
            result.append(buffer._asdict())
        return result

    def set_schedule_breakpoint(self, handle: int, enable: bool = True):
        '''
        Enables or disables a breakpoint on a schedule slot with the given handle.
        '''
        buffer = PLINUSBSetScheduleBreakpoint(brkpt=int(enable), handle=handle)
        self._ioctl(PLIOSETSCHDBP, buffer)

    def start_schedule(self, schedule: int) -> int:
        '''
        Starts the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBStartSchedule(schedule=schedule)
        self._ioctl(PLIOSTARTSCHD, buffer)
        return buffer.err

    def resume_schedule(self) -> int:
        '''
        Resumes the specified schedule.
        '''
        buffer = PLINUSBResumeSchedule()
        self._ioctl(PLIORESUMESCHD, buffer)
        return buffer.err

    def suspend_schedule(self, schedule: int) -> int:
        '''
        Suspends the specified schedule.
        '''
        if schedule < PLINScheduleIndex.MIN or schedule > PLINScheduleIndex.MAX:
            raise ValueError(
                f"Schedule out of range [{PLINScheduleIndex.MIN}..{PLINScheduleIndex.MAX}].")
        buffer = PLINUSBSuspendSchedule(schedule=schedule)
        self._ioctl(PLIOPAUSESCHD, buffer)
        return buffer.err

    def get_status(self) -> Dict[str, int]:
        '''
        Gets the status of the PLIN device.
        '''
        buffer = PLINUSBGetStatus()
        self._ioctl(PLIOGETSTATUS, buffer)
        return buffer._asdict()

    def reset_tx_queue(self):
        '''
        Resets the outgoing queue.
        '''
        self._ioctl(PLIORSTUSBTX)

    def wakeup(self):
        '''
        Wakes up the LIN bus.
        '''
        self._ioctl(PLIOXMTWAKEUP)

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
        self._ioctl(PLIOSETGETRSPMAP, buffer)

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
        self._ioctl(PLIOSETGETRSPMAP, buffer)

        if visual_output:
            print(self.get_visual_response_remap(buffer.id))

        print(bytearray(buffer))
        remap = {i: buffer.id[i]
                 for i in range(len(buffer.id)) if buffer.id[i] != 0}
        return remap

    def set_led_state(self, enable: bool):
        '''
        Sets the state of the LED on the PLIN device.
        '''
        buffer = PLINUSBLEDState(on_off=int(enable))
        self._ioctl(PLIOSETLEDSTATE, buffer)

    def read(self, block=True) -> Union[PLINMessage, None]:
        '''
        Reads a PLINMessage from the LIN bus with an optional timeout in milliseconds.

        A timeout value of 0 blocks until data is read. If the timeout is reached before data is read, None is returned.
        '''
        if self.fd:
            blocking = os.get_blocking(self.fd)
            os.set_blocking(self.fd, block)
            try:
                result = os.read(self.fd, PLINMessage.buffer_length)
                message = PLINMessage.from_buffer_copy(result)
                # If bytes read was invalid.
                if bytes(message.data) == PLIN_EMPTY_DATA:
                    message = None
            except:
                message = None
            os.set_blocking(self.fd, blocking)
            return message
        else:
            raise Exception("PLIN not connected!")

    def write(self, message: PLINMessage):
        '''
        Writes a PLINMessage to the LIN bus.
        '''
        if self.fd:
            if message.dir == PLINFrameDirection.PUBLISHER:
                self.block_id(message.id)
            buffer = bytearray(message)
            os.write(self.fd, buffer)
        else:
            raise Exception("PLIN not connected!")
