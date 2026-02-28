from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict

from .ops import Op


class CmdPayload(TypedDict, total=False):
    v: int
    op: int
    params: Dict[str, Any]


class CmdAckPayload(TypedDict, total=False):
    v: int
    op: int
    ok: bool
    code: int
    msg: str
    data: Dict[str, Any]


@dataclass(frozen=True, slots=True)
class Cmd:
    op: Op
    params: Dict[str, Any]

    def to_payload(self) -> CmdPayload:
        return {"v": 1, "op": int(self.op), "params": dict(self.params)}


@dataclass(frozen=True, slots=True)
class CmdAck:
    op: Op
    ok: bool
    code: int = 0
    msg: str = "OK"
    data: Optional[Dict[str, Any]] = None

    def to_payload(self) -> CmdAckPayload:
        p: CmdAckPayload = {
            "v": 1,
            "op": int(self.op),
            "ok": bool(self.ok),
            "code": int(self.code),
            "msg": str(self.msg),
        }
        if self.data is not None:
            p["data"] = dict(self.data)
        return p
