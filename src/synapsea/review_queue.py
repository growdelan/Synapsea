from __future__ import annotations

import json
import re
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
        candidate = item.to_dict()
        candidate_key = _semantic_key(candidate)
        replaced = False
        for index, existing in enumerate(items):
            if existing["cluster_id"] == item.cluster_id:
                items[index] = _merge_review_items(existing, candidate)
                replaced = True
                break
            if _semantic_key(existing) == candidate_key:
                items[index] = _merge_review_items(existing, candidate)
                replaced = True
                break
        if not replaced:
            items.append(candidate)
        self._write(payload)

    def update_status(self, item_id: str, status: str) -> ReviewItem:
        payload = self._read()
        items = payload.setdefault("items", [])
        for item in items:
            if item["id"] == item_id:
                item["status"] = status
                self._write(payload)
                return ReviewItem(
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
        raise KeyError(f"Nie znaleziono review item: {item_id}")

    def get_by_id(self, item_id: str) -> ReviewItem:
        for item in self.list_items():
            if item.item_id == item_id:
                return item
        raise KeyError(f"Nie znaleziono review item: {item_id}")

    def _read(self) -> dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, object]) -> None:
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _semantic_key(item: dict[str, object]) -> str:
    parent = str(item.get("parent_category", "")).strip().lower()
    proposed = str(item.get("proposed_category", "")).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", proposed).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return f"{parent}::{normalized}"


def _merge_review_items(existing: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    merged = dict(existing)
    existing_conf = float(existing.get("confidence", 0.0))
    incoming_conf = float(incoming.get("confidence", 0.0))
    if incoming_conf >= existing_conf:
        merged["confidence"] = incoming["confidence"]
        merged["reason"] = incoming["reason"]
        merged["cluster_id"] = incoming["cluster_id"]
    merged["status"] = existing.get("status", incoming.get("status", "pending"))
    merged["candidate_files"] = sorted(
        {
            *[str(path) for path in existing.get("candidate_files", [])],
            *[str(path) for path in incoming.get("candidate_files", [])],
        }
    )
    merged["target_path"] = str(existing.get("target_path") or incoming.get("target_path"))
    return merged
