from __future__ import annotations

import json
from pathlib import Path

from synapsea.models import CategoryProposal


class AiProposalCacheRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def load(self) -> dict[str, CategoryProposal]:
        payload = self._read()
        cache: dict[str, CategoryProposal] = {}
        for fingerprint, item in payload.items():
            cache[fingerprint] = CategoryProposal.from_dict(item)
        return cache

    def get(self, fingerprint: str) -> CategoryProposal | None:
        return self.load().get(fingerprint)

    def set(self, fingerprint: str, proposal: CategoryProposal) -> None:
        payload = self._read()
        payload[fingerprint] = {
            "should_create_category": proposal.should_create_category,
            "proposed_category": proposal.proposed_category,
            "reason": proposal.reason,
            "confidence": proposal.confidence,
        }
        self._write(payload)

    def _read(self) -> dict[str, dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, dict[str, object]]) -> None:
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class DeferredClusterRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save([])

    def load(self) -> list[str]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [str(item) for item in payload.get("cluster_ids", [])]

    def save(self, cluster_ids: list[str]) -> None:
        payload = {"cluster_ids": sorted(set(cluster_ids))}
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
