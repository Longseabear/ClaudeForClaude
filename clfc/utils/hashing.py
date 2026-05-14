from __future__ import annotations

import hashlib
from pathlib import Path


def short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def workspace_hash(path: Path) -> str:
    normalized = str(path.expanduser().resolve()).casefold()
    return short_hash(normalized, 6)
