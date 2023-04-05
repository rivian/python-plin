#!/usr/bin/env python3
import sys

from plin.enums import (PLINFrameChecksumType, PLINFrameDirection,
                        PLINFrameFlag, PLINMode)
from plin.plin import PLIN, PLINMessage


def main():
    slave = PLIN(sys.argv[1])
    slave.start(PLINMode.SLAVE)
    slave.set_id_filter(bytearray([0xff] * 8))

    slave.set_frame_entry(id=0x1, direction=PLINFrameDirection.SUBSCRIBER_AUTO_LEN,
                          checksum_type=PLINFrameChecksumType.ENHANCED)

    slave.add_unconditional_schedule_slot(schedule=0, delay_ms=100, id=0x1)

    slave.set_frame_entry(id=0x22, direction=PLINFrameDirection.PUBLISHER,
                          checksum_type=PLINFrameChecksumType.ENHANCED, data=bytearray([0xff] * 3))

    slave.add_unconditional_schedule_slot(schedule=0, delay_ms=100, id=0x2)

    slave.start_schedule(0)

    slave.set_response_remap({0x21: 0x22})
    result = slave.get_response_remap(visual_output=True)
    print(result)

    while True:
        result = slave.read()
        print(result)


if __name__ == "__main__":
    main()