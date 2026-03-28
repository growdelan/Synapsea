from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def conservative_evidence_weight(total_count: int) -> float:
    if total_count <= 1:
        return 0.1
    if total_count == 2:
        return 0.35
    if total_count == 3:
        return 0.7
    return 1.0


@dataclass(slots=True)
class PreferenceStats:
    accept_count: int = 0
    reject_count: int = 0
    score: float = 0.0

    def record_accept(self, amount: int = 1) -> None:
        self.accept_count += max(0, amount)
        self.recalculate()

    def record_reject(self, amount: int = 1) -> None:
        self.reject_count += max(0, amount)
        self.recalculate()

    def recalculate(self) -> None:
        total = self.accept_count + self.reject_count
        if total == 0:
            self.score = 0.0
            return
        raw = (self.accept_count - (0.7 * self.reject_count)) / (total + 1.0)
        weighted = raw * conservative_evidence_weight(total)
        self.score = clamp(weighted, -1.0, 1.0)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PreferenceStats":
        stats = cls(
            accept_count=int(payload.get("accept_count", 0)),
            reject_count=int(payload.get("reject_count", 0)),
            score=float(payload.get("score", 0.0)),
        )
        stats.recalculate()
        return stats

    def to_dict(self) -> dict[str, object]:
        return {
            "accept_count": self.accept_count,
            "reject_count": self.reject_count,
            "score": self.score,
        }


@dataclass(slots=True)
class UserPreferencesSnapshot:
    token_preferences: dict[str, dict[str, PreferenceStats]]
    heuristic_preferences: dict[str, dict[str, PreferenceStats]]
    pattern_preferences: dict[str, dict[str, PreferenceStats]]
    proposal_preferences: dict[str, PreferenceStats]


class UserPreferencesRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._default_payload())

    def load_snapshot(self) -> UserPreferencesSnapshot:
        payload = self._read()
        return UserPreferencesSnapshot(
            token_preferences=self._read_nested(payload, "token_preferences"),
            heuristic_preferences=self._read_nested(payload, "heuristic_preferences"),
            pattern_preferences=self._read_nested(payload, "pattern_preferences"),
            proposal_preferences=self._read_flat(payload, "proposal_preferences"),
        )

    def record_token(self, token: str, category_key: str, *, accepted: bool) -> None:
        self._record_nested("token_preferences", token, category_key, accepted=accepted)

    def record_heuristic(self, heuristic: str, category_key: str, *, accepted: bool) -> None:
        self._record_nested("heuristic_preferences", heuristic, category_key, accepted=accepted)

    def record_pattern(self, pattern: str, category_key: str, *, accepted: bool) -> None:
        self._record_nested("pattern_preferences", pattern, category_key, accepted=accepted)

    def record_proposal_pair(self, pair_key: str, *, accepted: bool) -> None:
        payload = self._read()
        proposal = payload.setdefault("proposal_preferences", {})
        stats_payload = dict(proposal.get(pair_key, {}))
        stats = PreferenceStats.from_dict(stats_payload)
        if accepted:
            stats.record_accept()
        else:
            stats.record_reject()
        proposal[pair_key] = stats.to_dict()
        self._write(payload)

    def _record_nested(self, group: str, signal: str, category_key: str, *, accepted: bool) -> None:
        payload = self._read()
        root = payload.setdefault(group, {})
        signal_map = root.setdefault(signal, {})
        stats_payload = dict(signal_map.get(category_key, {}))
        stats = PreferenceStats.from_dict(stats_payload)
        if accepted:
            stats.record_accept()
        else:
            stats.record_reject()
        signal_map[category_key] = stats.to_dict()
        self._write(payload)

    def _read_nested(self, payload: dict[str, Any], key: str) -> dict[str, dict[str, PreferenceStats]]:
        root = payload.get(key, {})
        result: dict[str, dict[str, PreferenceStats]] = {}
        for signal, categories in root.items():
            mapped: dict[str, PreferenceStats] = {}
            for category_key, stats_payload in dict(categories).items():
                mapped[str(category_key)] = PreferenceStats.from_dict(dict(stats_payload))
            result[str(signal)] = mapped
        return result

    def _read_flat(self, payload: dict[str, Any], key: str) -> dict[str, PreferenceStats]:
        root = payload.get(key, {})
        result: dict[str, PreferenceStats] = {}
        for pair_key, stats_payload in root.items():
            result[str(pair_key)] = PreferenceStats.from_dict(dict(stats_payload))
        return result

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        payload["metadata"] = {"version": 1}
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _default_payload(self) -> dict[str, Any]:
        return {
            "token_preferences": {},
            "heuristic_preferences": {},
            "pattern_preferences": {},
            "proposal_preferences": {},
            "metadata": {"version": 1},
        }
