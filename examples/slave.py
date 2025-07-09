#!/usr/bin/env python3
import sys

from plin.device import PLIN
from plin.enums import PLINFrameChecksumType, PLINFrameDirection, PLINMode


def main():
    slave = PLIN(sys.argv[1])
    slave.start(PLINMode.SLAVE)
    slave.set_id_filter(bytearray([0xff] * 8))

    slave.set_frame_entry(id=0x02, direction=PLINFrameDirection.PUBLISHER,
                          checksum_type=PLINFrameChecksumType.ENHANCED, data=bytearray([0xff] * 3))

    slave.set_response_remap({0x01: 0x02})
    result = slave.get_response_remap(visual_output=True)
    print(result)

    while True:
        result = slave.read()
        print(result)


if __name__ == "__main__":
    main()
