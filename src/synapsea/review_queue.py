from __future__ import annotations

import json
from pathlib import Path

from synapsea.models import ReviewItem


class ReviewQueueRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"items": []})

    def list_items(self) -> list[ReviewItem]:
        payload = self._read()
        items: list[ReviewItem] = []
        for item in payload.get("items", []):
            items.append(
                ReviewItem(
                    item_id=item["id"],
                    item_type=item["type"],
                    status=item["status"],
                    confidence=float(item["confidence"]),
                    parent_category=item["parent_category"],
                    proposed_category=item["proposed_category"],
                    target_path=item["target_path"],
                    candidate_files=list(item["candidate_files"]),
                    reason=item["reason"],
                    cluster_id=item["cluster_id"],
                )
            )
        return items

    def add_item(self, item: ReviewItem) -> None:
        payload = self._read()
        items = payload.setdefault("items", [])
        items.append(item.to_dict())
        self._write(payload)

    def _read(self) -> dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, object]) -> None:
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
