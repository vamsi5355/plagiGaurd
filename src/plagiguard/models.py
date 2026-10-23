from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Document:
    document_id: str
    text: str
    source_id: str | None = None


@dataclass(frozen=True)
class PairExample:
    pair_id: str
    suspicious_id: str
    source_id: str
    suspicious_text: str
    source_text: str
    label: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
