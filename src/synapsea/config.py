from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    source_dir: Path
    data_dir: Path

    @classmethod
    def from_args(cls, source: Path | None, data_dir: Path | None) -> "AppConfig":
        source_dir = (source or Path("~/Downloads")).expanduser()
        resolved_data_dir = (data_dir or Path("data")).expanduser()
        return cls(source_dir=source_dir, data_dir=resolved_data_dir)
