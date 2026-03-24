from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FileFeatures:
    path: str
    extension: str
    tokens: list[str]


@dataclass(slots=True)
class ClassificationDecision:
    file_path: str
    category: str
    reason: str
    confidence: float
    extension: str = ""
    tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CandidateCluster:
    cluster_id: str
    parent_category: str
    file_count: int
    dominant_extensions: list[str]
    top_tokens: list[str]
    pattern_signals: dict[str, float]
    example_files: list[str]
    candidate_files: list[str]
    heuristic_score: float
    cluster_type: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CategoryProposal:
    should_create_category: bool
    proposed_category: str
    reason: str
    confidence: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CategoryProposal":
        required_keys = {
            "should_create_category",
            "proposed_category",
            "reason",
            "confidence",
        }
        missing = required_keys.difference(payload)
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Brak pol w odpowiedzi AI: {missing_fields}")

        return cls(
            should_create_category=bool(payload["should_create_category"]),
            proposed_category=str(payload["proposed_category"]),
            reason=str(payload["reason"]),
            confidence=float(payload["confidence"]),
        )


@dataclass(slots=True)
class ReviewItem:
    item_id: str
    item_type: str
    status: str
    confidence: float
    parent_category: str
    proposed_category: str
    target_path: str
    candidate_files: list[str]
    reason: str
    cluster_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.item_id,
            "type": self.item_type,
            "status": self.status,
            "confidence": self.confidence,
            "parent_category": self.parent_category,
            "proposed_category": self.proposed_category,
            "target_path": self.target_path,
            "candidate_files": self.candidate_files,
            "reason": self.reason,
            "cluster_id": self.cluster_id,
        }

    @classmethod
    def from_cluster(
        cls,
        cluster: CandidateCluster,
        proposal: CategoryProposal,
        item_id: str,
    ) -> "ReviewItem":
        return cls(
            item_id=item_id,
            item_type="create_category",
            status="pending",
            confidence=proposal.confidence,
            parent_category=cluster.parent_category,
            proposed_category=proposal.proposed_category,
            target_path=f"{cluster.parent_category}/{proposal.proposed_category}",
            candidate_files=cluster.candidate_files,
            reason=proposal.reason,
            cluster_id=cluster.cluster_id,
        )


@dataclass(slots=True)
class TaxonomyNode:
    children: list[str]
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
