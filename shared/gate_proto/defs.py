from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Final


PROTO_SOF_0: Final[int] = 0xA5
PROTO_SOF_1: Final[int] = 0x5A
PROTO_VERSION: Final[int] = 0x01

PROTO_WIRE_HDR_LEN: Final[int] = 9  # SOF0..LEN
PROTO_CRC_LEN: Final[int] = 4

# LEN is uint8 => max 255
PROTO_MAX_PAYLOAD: Final[int] = 255


class MsgType(IntEnum):
    HELLO = 0x01
    HEARTBEAT = 0x02

    CMD = 0x10
    ACK = 0x11
    CMD_ACK = 0x12

    STATUS = 0x20
    PUSH_STATUS = 0x21
    EVENT = 0x22

    ERROR = 0x7F


class ProtoFlag(IntFlag):
    NONE = 0
    ACK_REQ = 1 << 0
    RESPONSE = 1 << 1
    ERROR = 1 << 2


@dataclass(frozen=True, slots=True)
class Frame:
    ver: int
    msg_type: MsgType
    flags: ProtoFlag
    gate_id: int
    seq: int
    payload: bytes  # JSON utf-8 bytes (not null-terminated)
    crc32: int      # uint32 received

    @property
    def payload_len(self) -> int:
        return len(self.payload)
