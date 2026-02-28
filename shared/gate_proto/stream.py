from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .codec import CrcMismatchError, FramingError, decode_frame
from .defs import PROTO_CRC_LEN, PROTO_SOF_0, PROTO_SOF_1, PROTO_WIRE_HDR_LEN


class ReadWrite(Protocol):
    def read(self, n: int) -> bytes: ...
    def write(self, b: bytes) -> int: ...


class StreamClosedError(Exception):
    pass


@dataclass(slots=True)
class FrameReader:
    io: ReadWrite

    def _read_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.io.read(n - len(buf))
            if not chunk:
                raise StreamClosedError("stream closed")
            buf.extend(chunk)
        return bytes(buf)

    def read_frame(self):
        while True:
            b0 = self._read_exact(1)[0]
            if b0 != PROTO_SOF_0:
                continue

            b1 = self._read_exact(1)[0]
            if b1 != PROTO_SOF_1:
                continue

            hdr_rest = self._read_exact(PROTO_WIRE_HDR_LEN - 2)
            hdr = bytes([PROTO_SOF_0, PROTO_SOF_1]) + hdr_rest
            length = int(hdr[-1])

            tail = self._read_exact(length + PROTO_CRC_LEN)
            raw = hdr + tail

            try:
                return decode_frame(raw)
            except (FramingError, CrcMismatchError):
                continue
