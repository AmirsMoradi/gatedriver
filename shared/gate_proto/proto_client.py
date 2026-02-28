from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Optional

from shared.gate_proto.codec import encode_json_frame
from shared.gate_proto.defs import Frame, MsgType, ProtoFlag
from shared.gate_proto.payloads import Cmd
from shared.gate_proto.stream import FrameReader, StreamClosedError


@dataclass(slots=True)
class GateProtoConfig:
    host: str
    port: int
    gate_id: int
    timeout_s: float = 2.0


class GateProtoClient:
    def __init__(self, cfg: GateProtoConfig) -> None:
        self._cfg = cfg
        self._seq: int = 0
        self._sock: Optional[socket.socket] = None
        self._io = None
        self._reader: Optional[FrameReader] = None

    def connect(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self._cfg.timeout_s)
        s.connect((self._cfg.host, self._cfg.port))
        self._sock = s
        self._io = s.makefile("rwb", buffering=0)
        self._reader = FrameReader(self._io)

    def close(self) -> None:
        try:
            if self._io is not None:
                self._io.close()
        finally:
            self._io = None
            if self._sock is not None:
                try:
                    self._sock.close()
                finally:
                    self._sock = None
            self._reader = None

    def _next_seq(self) -> int:
        self._seq = (self._seq + 1) & 0xFFFF
        if self._seq == 0:
            self._seq = 1
        return self._seq

    def send_json(
        self,
        *,
        msg_type: MsgType,
        flags: ProtoFlag,
        payload: dict[str, Any],
        gate_id: Optional[int] = None,
    ) -> int:
        if self._io is None:
            raise RuntimeError("GateProtoClient not connected")

        seq = self._next_seq()
        raw = encode_json_frame(
            msg_type=msg_type,
            flags=flags,
            gate_id=int(self._cfg.gate_id if gate_id is None else gate_id),
            seq=seq,
            payload_obj=payload,
        )
        self._io.write(raw)
        return seq

    def send_cmd(self, cmd: Cmd, *, ack_req: bool = True) -> int:
        flags = ProtoFlag.ACK_REQ if ack_req else ProtoFlag.NONE
        return self.send_json(msg_type=MsgType.CMD, flags=flags, payload=cmd.to_payload())

    def wait_for(self, *, seq: int, want_types: set[MsgType], timeout_s: float) -> Frame:
        if self._reader is None or self._sock is None:
            raise RuntimeError("GateProtoClient not connected")

        deadline = time.time() + float(timeout_s)
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError("gate response timeout")

            self._sock.settimeout(remaining)
            try:
                fr = self._reader.read_frame()
            except StreamClosedError as e:
                raise ConnectionError(str(e)) from e

            if fr.seq != int(seq):
                continue
            if fr.msg_type not in want_types:
                continue
            return fr

    def wait_cmd_ack(self, *, seq: int, timeout_s: float = 2.0) -> dict[str, Any]:
        fr = self.wait_for(seq=seq, want_types={MsgType.CMD_ACK}, timeout_s=timeout_s)
        return self.payload_json(fr)

    @staticmethod
    def payload_json(frame: Frame) -> dict[str, Any]:
        if not frame.payload:
            return {}
        return json.loads(frame.payload.decode("utf-8"))
