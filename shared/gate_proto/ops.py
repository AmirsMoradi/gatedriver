from __future__ import annotations

from enum import IntEnum


class Op(IntEnum):
    UNAUTHORIZED = 0x00

    OP_DOOR_SET = 0x01
    OP_DOOR_MAX_SPEED_SET = 0x02
    OP_DOOR_LOW_SPEED_SET = 0x03
    OP_DOOR_ACCEL_MS_SET = 0x04
    OP_DOOR_DECEL_MS_SET = 0x05
    OP_DOOR_HOLD_MS_SET = 0x06
    OP_DOOR_POSITION_GET = 0x07
    OP_DOOR_STATUS_GET = 0x08

    OP_V_BUS_GET = 0x21
    OP_TEMP_GET = 0x22
    OP_FAN_EN = 0x23
    OP_BUZZ_EN = 0x24
    OP_BUZZ_MS_SET = 0x25

    OP_IP_GET = 0x31
    OP_MAC_GET = 0x32
    OP_LOCAL_PORT_GET = 0x33

    OP_MAX = 0xFF
