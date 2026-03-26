from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    source_dir: Path
    data_dir: Path
    ollama_endpoint: str = "http://localhost:11434/api/generate"
    ollama_model: str = "gemma3:4b-it-qat"
    ollama_timeout_seconds: int = 60
    enable_ai_review: bool = True
    ai_budget_per_cycle: int = 20
    ai_max_examples: int = 3
    watch_poll_interval_seconds: float = 2.0

    @classmethod
    def from_args(
        cls,
        source: Path | None,
        data_dir: Path | None,
        enable_ai_review: bool = True,
        ollama_model: str | None = None,
        ai_budget_per_cycle: int | None = None,
        ai_max_examples: int | None = None,
        watch_poll_interval_seconds: float | None = None,
    ) -> "AppConfig":
        source_dir = (source or Path("~/Downloads")).expanduser()
        resolved_data_dir = (data_dir or Path("data")).expanduser()
        return cls(
            source_dir=source_dir,
            data_dir=resolved_data_dir,
            ollama_endpoint="http://localhost:11434/api/generate",
            ollama_model=ollama_model or "gemma3:4b-it-qat",
            ollama_timeout_seconds=60,
            enable_ai_review=enable_ai_review,
            ai_budget_per_cycle=ai_budget_per_cycle if ai_budget_per_cycle is not None else 20,
            ai_max_examples=ai_max_examples if ai_max_examples is not None else 3,
            watch_poll_interval_seconds=(
                watch_poll_interval_seconds if watch_poll_interval_seconds is not None else 2.0
            ),
        )
