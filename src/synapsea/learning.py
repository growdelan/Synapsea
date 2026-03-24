from __future__ import annotations

import json
from pathlib import Path

from synapsea.models import LearningSignal


class LearningSignalRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"signals": []})

    def list_signals(self) -> list[LearningSignal]:
        payload = self._read()
        return [
            LearningSignal(
                signal_id=item["signal_id"],
                signal_type=item["signal_type"],
                category=item["category"],
                file_path=item["file_path"],
                details=dict(item.get("details", {})),
            )
            for item in payload.get("signals", [])
        ]

    def add_signal(self, signal: LearningSignal) -> None:
        payload = self._read()
        payload.setdefault("signals", []).append(signal.to_dict())
        self._write(payload)

    def _read(self) -> dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, object]) -> None:
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


class SnapshotRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save({})

    def load(self) -> dict[str, str]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, snapshot: dict[str, str]) -> None:
        self.path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
