from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class FileFeatures:
    path: str
    extension: str
    tokens: list[str]


@dataclass(slots=True)
class ClassificationDecision:
    file_path: str
    category: str
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
