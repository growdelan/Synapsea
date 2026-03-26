from __future__ import annotations

import json
from pathlib import Path


class InputStateRepository:
    """Trwały zapis stanu plików źródłowych do wyliczania delty zmian."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save({})

    def load(self) -> dict[str, dict[str, int]]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        state: dict[str, dict[str, int]] = {}
        for file_path, item in payload.items():
            state[file_path] = {
                "inode": int(item.get("inode", 0)),
                "size": int(item.get("size", 0)),
                "mtime_ns": int(item.get("mtime_ns", 0)),
            }
        return state

    def save(self, state: dict[str, dict[str, int]]) -> None:
        self.path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
