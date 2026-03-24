from __future__ import annotations

import json
from pathlib import Path

from synapsea.models import TaxonomyNode


class TaxonomyRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def load(self) -> dict[str, TaxonomyNode]:
        payload = self._read()
        return {
            key: TaxonomyNode(
                children=list(value.get("children", [])),
                status=str(value.get("status", "stable")),
            )
            for key, value in payload.items()
        }

    def save(self, taxonomy: dict[str, TaxonomyNode]) -> None:
        payload = {key: node.to_dict() for key, node in taxonomy.items()}
        self._write(payload)

    def _read(self) -> dict[str, dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, object]) -> None:
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
