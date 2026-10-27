from __future__ import annotations

import re
import math

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


def dask_memory_bytes(limit: str) -> int:
    """Dask-compatible SI/IEC units for new resource accounting.

    Keep parse_bytes/parse_gb unchanged: main-v1 model features used their
    legacy binary interpretation of GB. Changing those would change inference.
    """
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([KMGT]?I?B)\s*", limit, re.IGNORECASE)
    if not match:
        raise ValueError(f"unrecognized explicit memory limit: {limit!r}")
    amount = float(match.group(1))
    unit = match.group(2).upper()
    units = {"B": 1}
    for exponent, prefix in enumerate("KMGT", 1):
        units[prefix + "B"] = 1000**exponent
        units[prefix + "IB"] = 1024**exponent
    if unit not in units or not math.isfinite(amount) or amount <= 0:
        raise ValueError("memory limit must be finite and positive")
    raw_bytes = amount * units[unit]
    if not math.isfinite(raw_bytes):
        raise ValueError("memory limit is too large")
    value = int(raw_bytes)
    if value <= 0:
        raise ValueError("memory limit must be at least one byte")
    return value
