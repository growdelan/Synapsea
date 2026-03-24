from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from synapsea.models import CandidateCluster, ClassificationDecision


class ClusterEngine:
    """Buduje kandydatow klastrow z prostych, heurystycznych sygnalow."""

    def build_clusters(
        self,
        decisions: Iterable[ClassificationDecision],
    ) -> list[CandidateCluster]:
        by_category: dict[str, list[ClassificationDecision]] = defaultdict(list)
        for decision in decisions:
            by_category[decision.category].append(decision)

        clusters: list[CandidateCluster] = []
        cluster_counter = 1
        for category, category_decisions in sorted(by_category.items()):
            clusters.extend(
                self._build_token_clusters(category, category_decisions, start_index=cluster_counter)
            )
            cluster_counter += len(clusters)
            clusters.extend(
                self._build_extension_clusters(category, category_decisions, start_index=cluster_counter)
            )
            cluster_counter += len(clusters)
            clusters.extend(
                self._build_pattern_clusters(category, category_decisions, start_index=cluster_counter)
            )
            cluster_counter += len(clusters)
        return clusters

    def _build_token_clusters(
        self,
        category: str,
        decisions: list[ClassificationDecision],
        start_index: int,
    ) -> list[CandidateCluster]:
        token_map: dict[str, list[ClassificationDecision]] = defaultdict(list)
        for decision in decisions:
            for token in set(decision.tokens):
                if len(token) >= 3:
                    token_map[token].append(decision)

        clusters: list[CandidateCluster] = []
        for index, (token, grouped) in enumerate(sorted(token_map.items()), start=start_index):
            if len(grouped) < 2:
                continue
            clusters.append(
                self._build_cluster(
                    cluster_id=f"cluster_{index:03d}",
                    cluster_type="token",
                    category=category,
                    grouped=grouped,
                    signals={"shared_token_ratio": 1.0},
                    top_tokens=[token],
                )
            )
        return clusters

    def _build_extension_clusters(
        self,
        category: str,
        decisions: list[ClassificationDecision],
        start_index: int,
    ) -> list[CandidateCluster]:
        extension_map: dict[str, list[ClassificationDecision]] = defaultdict(list)
        for decision in decisions:
            if decision.extension:
                extension_map[decision.extension].append(decision)

        clusters: list[CandidateCluster] = []
        for index, (extension, grouped) in enumerate(
            sorted(extension_map.items()),
            start=start_index,
        ):
            if len(grouped) < 2:
                continue
            clusters.append(
                self._build_cluster(
                    cluster_id=f"cluster_{index:03d}",
                    cluster_type="extension",
                    category=category,
                    grouped=grouped,
                    signals={"dominant_extension_ratio": 1.0},
                    top_tokens=[extension],
                )
            )
        return clusters

    def _build_pattern_clusters(
        self,
        category: str,
        decisions: list[ClassificationDecision],
        start_index: int,
    ) -> list[CandidateCluster]:
        pattern_map: dict[str, list[ClassificationDecision]] = defaultdict(list)
        for decision in decisions:
            pattern = self._detect_name_pattern(decision.file_path)
            if pattern:
                pattern_map[pattern].append(decision)

        clusters: list[CandidateCluster] = []
        for index, (pattern, grouped) in enumerate(
            sorted(pattern_map.items()),
            start=start_index,
        ):
            if len(grouped) < 2:
                continue
            clusters.append(
                self._build_cluster(
                    cluster_id=f"cluster_{index:03d}",
                    cluster_type="name_pattern",
                    category=category,
                    grouped=grouped,
                    signals={"pattern_similarity": 0.9},
                    top_tokens=[pattern],
                )
            )
        return clusters

    def _build_cluster(
        self,
        cluster_id: str,
        cluster_type: str,
        category: str,
        grouped: list[ClassificationDecision],
        signals: dict[str, float],
        top_tokens: list[str],
    ) -> CandidateCluster:
        extension_counter = Counter(decision.extension for decision in grouped if decision.extension)
        dominant_extensions = [extension for extension, _ in extension_counter.most_common(3)]
        token_counter = Counter(token for decision in grouped for token in decision.tokens)
        candidate_files = [decision.file_path for decision in grouped]
        example_files = candidate_files[:3]
        combined_tokens = top_tokens[:]
        for token, _ in token_counter.most_common(3):
            if token not in combined_tokens:
                combined_tokens.append(token)
        heuristic_score = round(min(0.99, 0.55 + (len(grouped) * 0.1)), 2)
        return CandidateCluster(
            cluster_id=cluster_id,
            parent_category=category,
            file_count=len(grouped),
            dominant_extensions=dominant_extensions,
            top_tokens=combined_tokens[:3],
            pattern_signals=signals,
            example_files=example_files,
            candidate_files=candidate_files,
            heuristic_score=heuristic_score,
            cluster_type=cluster_type,
        )

    def _detect_name_pattern(self, file_path: str) -> str | None:
        lower_path = file_path.lower()
        if any(char.isdigit() for char in lower_path):
            if "-" in lower_path or "_" in lower_path:
                return "dated_or_numbered"
            return "numbered"
        if "screenshot" in lower_path or "zrzut" in lower_path:
            return "screenshot_like"
        if "v" in lower_path:
            return "versioned"
        return None
