from __future__ import annotations

import json
from pathlib import Path

from synapsea.models import CandidateCluster


class CandidateClusterRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save([])

    def load(self) -> list[CandidateCluster]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        clusters: list[CandidateCluster] = []
        for item in payload:
            clusters.append(
                CandidateCluster(
                    cluster_id=item["cluster_id"],
                    parent_category=item["parent_category"],
                    file_count=int(item["file_count"]),
                    dominant_extensions=list(item["dominant_extensions"]),
                    top_tokens=list(item["top_tokens"]),
                    pattern_signals=dict(item["pattern_signals"]),
                    example_files=list(item["example_files"]),
                    candidate_files=list(item["candidate_files"]),
                    heuristic_score=float(item["heuristic_score"]),
                    cluster_type=item["cluster_type"],
                )
            )
        return clusters

    def save(self, clusters: list[CandidateCluster]) -> None:
        payload = [cluster.to_dict() for cluster in clusters]
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
