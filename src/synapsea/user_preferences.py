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


@dataclass(slots=True)
class PreferenceScoreBreakdown:
    base_confidence: float
    preference_delta: float
    final_confidence: float
    reasons: list[str]


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

    def score_review_item(
        self,
        *,
        parent_category: str,
        proposed_category: str,
        target_path: str,
        base_confidence: float,
        tokens: list[str],
        heuristics: list[str],
        patterns: list[str],
    ) -> PreferenceScoreBreakdown:
        snapshot = self.load_snapshot()
        pair_key = f"{parent_category}::{proposed_category}"
        pair_score = snapshot.proposal_preferences.get(pair_key, PreferenceStats()).score
        token_score = self._mean_score(snapshot.token_preferences, tokens, target_path)
        heuristic_score = self._mean_score(snapshot.heuristic_preferences, heuristics, target_path)
        pattern_score = self._mean_score(snapshot.pattern_preferences, patterns, target_path)

        pair_component = pair_score * 0.15
        token_component = token_score * 0.08
        heuristic_component = heuristic_score * 0.06
        pattern_component = pattern_score * 0.05
        delta = pair_component + token_component + heuristic_component + pattern_component
        final = clamp(base_confidence + delta, 0.0, 0.99)

        reasons: list[str] = []
        if pair_component:
            reasons.append(f"pair:{pair_component:+.3f}")
        if token_component:
            reasons.append(f"token:{token_component:+.3f}")
        if heuristic_component:
            reasons.append(f"heuristic:{heuristic_component:+.3f}")
        if pattern_component:
            reasons.append(f"pattern:{pattern_component:+.3f}")

        return PreferenceScoreBreakdown(
            base_confidence=base_confidence,
            preference_delta=delta,
            final_confidence=final,
            reasons=reasons,
        )

    def summary_lines(self, *, limit: int = 10, verbose: bool = False) -> list[str]:
        snapshot = self.load_snapshot()
        lines: list[str] = []

        positive_pairs = sorted(
            snapshot.proposal_preferences.items(),
            key=lambda entry: entry[1].score,
            reverse=True,
        )[:limit]
        negative_pairs = sorted(
            snapshot.proposal_preferences.items(),
            key=lambda entry: entry[1].score,
        )[:limit]
        lines.append("Top pozytywne pary propozycji:")
        lines.extend(self._format_pairs(positive_pairs, verbose=verbose))
        lines.append("Top negatywne pary propozycji:")
        lines.extend(self._format_pairs(negative_pairs, verbose=verbose))

        lines.append("Top preferencje tokenow:")
        lines.extend(self._format_nested(snapshot.token_preferences, limit=limit, verbose=verbose))
        lines.append("Top preferencje heurystyk:")
        lines.extend(self._format_nested(snapshot.heuristic_preferences, limit=limit, verbose=verbose))
        return lines

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

    def _mean_score(
        self,
        bucket: dict[str, dict[str, PreferenceStats]],
        signals: list[str],
        category_key: str,
    ) -> float:
        if not signals:
            return 0.0
        scores: list[float] = []
        for signal in signals:
            score = bucket.get(signal, {}).get(category_key)
            if score is not None:
                scores.append(score.score)
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _format_pairs(
        self,
        items: list[tuple[str, PreferenceStats]],
        *,
        verbose: bool,
    ) -> list[str]:
        if not items:
            return ["- brak danych"]
        lines: list[str] = []
        for key, stats in items:
            if verbose:
                lines.append(
                    f"- {key}: score={stats.score:+.3f}, "
                    f"accept={stats.accept_count}, reject={stats.reject_count}"
                )
            else:
                lines.append(f"- {key}: {stats.score:+.3f}")
        return lines

    def _format_nested(
        self,
        source: dict[str, dict[str, PreferenceStats]],
        *,
        limit: int,
        verbose: bool,
    ) -> list[str]:
        flattened: list[tuple[str, str, PreferenceStats]] = []
        for signal, categories in source.items():
            for category_key, stats in categories.items():
                flattened.append((signal, category_key, stats))
        flattened.sort(key=lambda entry: entry[2].score, reverse=True)
        flattened = flattened[:limit]
        if not flattened:
            return ["- brak danych"]
        lines: list[str] = []
        for signal, category_key, stats in flattened:
            if verbose:
                lines.append(
                    f"- {signal} -> {category_key}: score={stats.score:+.3f}, "
                    f"accept={stats.accept_count}, reject={stats.reject_count}"
                )
            else:
                lines.append(f"- {signal} -> {category_key}: {stats.score:+.3f}")
        return lines

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
