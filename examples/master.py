#!/usr/bin/env python3
import pprint
import sys

from plin.device import PLIN
from plin.enums import (PLINFrameChecksumType, PLINFrameDirection,
                        PLINFrameFlag, PLINMode)

pp = pprint.PrettyPrinter(indent=4)


def main():
    master = PLIN(sys.argv[1])
    master.start(mode=PLINMode.MASTER)
    print(master.get_firmware_version())

    master.set_frame_entry(id=0x01, direction=PLINFrameDirection.PUBLISHER,
                           checksum_type=PLINFrameChecksumType.ENHANCED, flags=PLINFrameFlag.RSP_ENABLE, data=bytearray([0xff, 0xff, 0xff]))
    result = master.get_frame_entry(id=0x01)
    print("FRAME ENTRY")
    pp.pprint(result)

    master.add_unconditional_schedule_slot(schedule=0, delay_ms=10, id=0x01)

    master.set_frame_entry(id=0x02, direction=PLINFrameDirection.SUBSCRIBER_AUTO_LEN,
                           checksum_type=PLINFrameChecksumType.ENHANCED)

    master.add_unconditional_schedule_slot(schedule=0, delay_ms=10, id=0x02)

    result = master.get_schedule_slots(0)
    print("SCHEDULE")
    pp.pprint(result)
    master.start_schedule(0)

    master.set_id_filter(bytearray([0xff] * 8))

    print("STATUS")
    pp.pprint(master.get_status())

    while True:
        result = master.read()
        print(result)


if __name__ == "__main__":
    main()
