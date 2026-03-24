from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    source_dir: Path
    data_dir: Path
    ollama_endpoint: str = "http://localhost:11434/api/generate"
    ollama_model: str = "gemma3:4b-it-qat"
    enable_ai_review: bool = True

    @classmethod
    def from_args(
        cls,
        source: Path | None,
        data_dir: Path | None,
        enable_ai_review: bool = True,
    ) -> "AppConfig":
        source_dir = (source or Path("~/Downloads")).expanduser()
        resolved_data_dir = (data_dir or Path("data")).expanduser()
        return cls(
            source_dir=source_dir,
            data_dir=resolved_data_dir,
            ollama_endpoint="http://localhost:11434/api/generate",
            ollama_model="gemma3:4b-it-qat",
            enable_ai_review=enable_ai_review,
        )
