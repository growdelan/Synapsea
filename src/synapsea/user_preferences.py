from __future__ import annotations

from dataclasses import dataclass


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
