from __future__ import annotations

import binascii


def crc32_u32(data: bytes) -> int:
    # CRC32 IEEE (zlib/binascii)
    return binascii.crc32(data) & 0xFFFFFFFF


def u16_to_be(x: int) -> bytes:
    return int(x & 0xFFFF).to_bytes(2, byteorder="big", signed=False)


def u32_to_be(x: int) -> bytes:
    return int(x & 0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
