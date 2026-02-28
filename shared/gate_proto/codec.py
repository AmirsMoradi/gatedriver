from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .crc import crc32_u32, u16_to_be, u32_to_be
from .defs import (
    PROTO_CRC_LEN,
    PROTO_MAX_PAYLOAD,
    PROTO_SOF_0,
    PROTO_SOF_1,
    PROTO_VERSION,
    PROTO_WIRE_HDR_LEN,
    Frame,
    MsgType,
    ProtoFlag,
)


class ProtoError(Exception):
    pass


class FramingError(ProtoError):
    pass


class CrcMismatchError(ProtoError):
    pass


@dataclass(frozen=True, slots=True)
class WireHeader:
    ver: int
    msg_type: MsgType
    flags: ProtoFlag
    gate_id: int
    seq: int
    length: int


def encode_frame(
    *,
    msg_type: MsgType,
    flags: ProtoFlag,
    gate_id: int,
    seq: int,
    payload: bytes,
    ver: int = PROTO_VERSION,
) -> bytes:
    if not (0 <= gate_id <= 0xFF):
        raise ValueError("gate_id must be uint8 (0..255)")
    if not (0 <= seq <= 0xFFFF):
        raise ValueError("seq must be uint16 (0..65535)")
    if len(payload) > PROTO_MAX_PAYLOAD:
        raise ValueError(f"payload too large: {len(payload)} > {PROTO_MAX_PAYLOAD}")

    sof = bytes([PROTO_SOF_0, PROTO_SOF_1])

    hdr_wo_sof = (
        bytes(
            [
                ver & 0xFF,
                int(msg_type) & 0xFF,
                int(flags) & 0xFF,
                gate_id & 0xFF,
            ]
        )
        + u16_to_be(seq)
        + bytes([len(payload) & 0xFF])
    )

    # CRC over VER..PAYLOAD (SOF excluded)
    crc_input = hdr_wo_sof + payload
    crc = crc32_u32(crc_input)

    return sof + hdr_wo_sof + payload + u32_to_be(crc)


def encode_json_frame(
    *,
    msg_type: MsgType,
    flags: ProtoFlag,
    gate_id: int,
    seq: int,
    payload_obj: Any,
    ver: int = PROTO_VERSION,
) -> bytes:
    payload = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return encode_frame(
        msg_type=msg_type,
        flags=flags,
        gate_id=gate_id,
        seq=seq,
        payload=payload,
        ver=ver,
    )


def _parse_wire_header(hdr: bytes) -> WireHeader:
    if len(hdr) != PROTO_WIRE_HDR_LEN:
        raise FramingError("invalid header length")
    if hdr[0] != PROTO_SOF_0 or hdr[1] != PROTO_SOF_1:
        raise FramingError("bad SOF")

    ver = int(hdr[2])
    msg_type = MsgType(int(hdr[3]))
    flags = ProtoFlag(int(hdr[4]))
    gate_id = int(hdr[5])
    seq = int.from_bytes(hdr[6:8], "big", signed=False)
    length = int(hdr[8])

    if not (0 <= length <= PROTO_MAX_PAYLOAD):
        raise FramingError("LEN out of range")

    return WireHeader(ver=ver, msg_type=msg_type, flags=flags, gate_id=gate_id, seq=seq, length=length)


def decode_frame(raw: bytes) -> Frame:
    if len(raw) < PROTO_WIRE_HDR_LEN + PROTO_CRC_LEN:
        raise FramingError("frame too short")

    hdr = _parse_wire_header(raw[:PROTO_WIRE_HDR_LEN])
    expected = PROTO_WIRE_HDR_LEN + hdr.length + PROTO_CRC_LEN
    if len(raw) != expected:
        raise FramingError(f"frame length mismatch: got={len(raw)} expected={expected}")

    payload = raw[PROTO_WIRE_HDR_LEN : PROTO_WIRE_HDR_LEN + hdr.length]
    crc_recv = int.from_bytes(raw[-4:], "big", signed=False)

    crc_input = raw[2:PROTO_WIRE_HDR_LEN] + payload  # VER..LEN + PAYLOAD
    crc_calc = crc32_u32(crc_input)
    if crc_calc != crc_recv:
        raise CrcMismatchError(f"CRC mismatch calc={crc_calc:08X} recv={crc_recv:08X}")

    return Frame(
        ver=hdr.ver,
        msg_type=hdr.msg_type,
        flags=hdr.flags,
        gate_id=hdr.gate_id,
        seq=hdr.seq,
        payload=payload,
        crc32=crc_recv,
    )
