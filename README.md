# Python PLIN library
This library provides a Python interface for interacting with PEAK devices such as the PCAN-USB Pro and PLIN-USB on Linux. It is based on the chardev API provided by the PEAK LIN Linux Beta. The PEAK Linux beta driver is required to use this library and is available [here](https://forum.peak-system.com/viewtopic.php?t=5875).

## Examples
Runnable examples are located in the `examples/` directory.

### Master Example
```python
from plin.plin import PLIN
from plin.enums import (PLINFrameChecksumType, PLINFrameDirection,
                        PLINFrameFlag, PLINMode)

# Initializes /dev/plin0 as a LIN master
master = PLIN(interface="/dev/plin0")

master.start(mode=PLINMode.MASTER, baudrate=19200)

# Get firmware version of the PEAK device
print(master.get_firmware_version())

# Get current status of the PEAK device
print(master.get_status())

# Add a publisher frame entry
master.set_frame_entry(id=0x01,
                       direction=PLINFrameDirection.PUBLISHER,
                       checksum_type=PLINFrameChecksumType.CLASSIC,
                       flags=PLINFrameFlag.RSP_ENABLE,
                       data=bytearray([0x01, 0x02, 0x03]))

# Add a subscriber frame entry
master.set_frame_entry(id=0x02,
                       direction=PLINFrameDirection.SUBSCRIBER_AUTO_LEN,
                       checksum_type=PLINFrameChecksumType.CLASSIC)

# Get frame entry
print(master.get_frame_entry(id=0x01))

# Add unconditional slot to schedule 0
master.add_unconditional_schedule_slot(schedule=0, delay_ms=10, id=0x01)
master.add_unconditional_schedule_slot(schedule=0, delay_ms=10, id=0x02)

# Get schedule 0 slots
print(master.get_schedule_slots(0))

# Start schedule 0
master.start_schedule(0)

# Set ID filter
master.set_id_filter(bytearray([0xff] * 8))

# Read frames
while True:
    result = master.read()
    print(result)

```

## Documentation
Additional documentation is located under the `docs/` directory.


## Unit Tests
Unit tests are located in the `unit_tests/` directory and require a PEAK LIN device connected to run.

## License

    Copyright 2023 Rivian Automotive, Inc.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.