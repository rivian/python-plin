from enum import IntEnum, IntFlag


class PLINError(IntEnum):
    '''
    LIN error.
    '''
    OK = 0                              # success
    FAIL = 1                            # (PCAN-USB Pro) failure
    INITIALIZE = 2                      # hw initialized
    SCHEDULER = 3                       # scheduler bad state
    FRAME = 4                           # bad frame config
    SLOTPOOL = 5                        # slots global pool full
    ILL_SCHEDULE = 6                    # no schedule present
    ILL_MODE = 7                        # bad mode


class PLINMode(IntEnum):
    '''
    LIN mode.
    '''
    NONE = 0
    SLAVE = 1
    MASTER = 2


class PLINBusState(IntEnum):
    '''
    LIN Bus hardware state.
    '''
    UNINIT = 0
    AUTOBAUD = 1
    ACTIVE = 2
    SLEEP = 3
    GND_SHORT = 6
    VBAT_MISSING = 7


class PLINMessageType(IntEnum):
    '''
    LIN message type.
    '''
    FRAME = 0
    SLEEP = 1
    WAKEUP = 2
    AUTOBAUD_TO = 3
    AUTOBAUD_OK = 4
    OVERRUN = 5


class PLINFrameDirection(IntEnum):
    '''
    LIN frame direction.
    '''
    DISABLED = 0
    PUBLISHER = 1
    SUBSCRIBER = 2
    SUBSCRIBER_AUTO_LEN = 3


class PLINFrameChecksumType(IntEnum):
    '''
    LIN frame checksum type.
    '''
    CUSTOM = 0
    CLASSIC = 1
    ENHANCED = 2
    AUTO = 3                            # not for publisher


class PLINFrameFlag(IntFlag):
    '''
    LIN frame flags for frame table entry.
    '''
    NONE = 0x0000
    RSP_ENABLE = 0x0001                 # publisher
    SINGLE_SHOT = 0x0002                # publisher
    IGNORE_DATA = 0x0004


class PLINFrameErrorFlag(IntFlag):
    '''
    LIN frame received (error) flags.
    '''
    INC_SYNC = 0x0001
    PARITY0 = 0x0002
    PARITY1 = 0x0004
    SLV_NOT_RSP = 0x0008
    TIMEOUT = 0x0010
    BAD_CS = 0x0020
    BUS_SHORT_GND = 0x0040
    BUS_SHORT_VBAT = 0x0080
    RESERVED = 0x0100
    OTHER_RSP = 0x0200


class PLINFrameID(IntEnum):
    UNC_MIN = 0
    UNC_MAX = 59
    DIAG_MASTER_REQ = 60
    DIAG_SLAVE_RSP = 61
    USER = 62
    RESERVED = 63
    MIN = 0
    MAX = 63


class PLINUSBSlotType(IntEnum):
    UNCOND = 0                          # id0 is sent
    EVENT = 1                           # id0 is sent
    SPORADIC = 2                        # id0 highest priority
    MASTER_REQ = 3                      # 60h implicit
    SLAVE_RSP = 4                       # 61h implicit


class PLINUSBResponseRemapType(IntEnum):
    GET = 0
    SET = 1


class PLINUSBSlotNumber(IntEnum):
    '''
    Slot number range.
    '''
    MIN = 1
    MAX = 8


class PLINBaudrate(IntEnum):
    '''
    LIN baudrate range.
    '''
    MIN = 1000
    MAX = 20000


class PLINScheduleIndex(IntEnum):
    '''
    LIN schedule index range.
    '''
    MIN = 0
    MAX = 7
