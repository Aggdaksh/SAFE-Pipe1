from __future__ import annotations

import re

_LIMIT = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([KMGT]?B)\s*$", re.IGNORECASE)
_MULT = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}


def parse_bytes(limit: str) -> int:
    match = _LIMIT.match(limit)
    if not match:
        raise ValueError(f"unrecognized memory_limit: {limit!r}")
    amount = float(match.group(1))
    unit = match.group(2).upper()
    return int(amount * _MULT[unit])


def parse_gb(limit: str) -> float:
    return parse_bytes(limit) / (1024**3)
