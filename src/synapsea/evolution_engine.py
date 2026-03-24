from __future__ import annotations

from collections import Counter

from synapsea.models import LearningSignal, ReviewItem, TaxonomyNode


class EvolutionEngine:
    def build_proposals(
        self,
        signals: list[LearningSignal],
        taxonomy: dict[str, TaxonomyNode],
        start_index: int = 1,
    ) -> list[ReviewItem]:
        proposals: list[ReviewItem] = []
        next_index = start_index

        rename_tokens = [
            signal.details.get("suggested_category")
            for signal in signals
            if signal.signal_type == "manual_rename" and signal.details.get("suggested_category")
        ]
        for token, count in Counter(rename_tokens).items():
            if count < 1:
                continue
            proposals.append(
                ReviewItem(
                    item_id=f"evo_{next_index:03d}",
                    item_type="create_subcategory",
                    status="pending",
                    confidence=0.75,
                    parent_category="images" if "screen" in token else "documents",
                    proposed_category=str(token),
                    target_path=f"evolved/{token}",
                    candidate_files=[],
                    reason="Wykryto powtarzalne sygnaly recznego rename.",
                    cluster_id=f"evolution_{next_index:03d}",
                )
            )
            next_index += 1

        rejected_categories = Counter(
            signal.details.get("proposed_category")
            for signal in signals
            if signal.signal_type == "review_rejected" and signal.details.get("proposed_category")
        )
        for category_name, count in rejected_categories.items():
            if count < 1 or not category_name:
                continue
            proposals.append(
                ReviewItem(
                    item_id=f"evo_{next_index:03d}",
                    item_type="merge_category",
                    status="pending",
                    confidence=0.72,
                    parent_category="documents",
                    proposed_category=str(category_name),
                    target_path=f"merge/{category_name}",
                    candidate_files=[],
                    reason="Powtarzalne odrzucenia sugeruja potrzebe merge zamiast nowej kategorii.",
                    cluster_id=f"evolution_{next_index:03d}",
                )
            )
            next_index += 1

        for name, node in taxonomy.items():
            if node.status == "proposed" and not node.children:
                proposals.append(
                    ReviewItem(
                        item_id=f"evo_{next_index:03d}",
                        item_type="dead_category",
                        status="pending",
                        confidence=0.7,
                        parent_category=name,
                        proposed_category=name,
                        target_path=f"dead/{name}",
                        candidate_files=[],
                        reason="Kategoria pozostaje pusta i kwalifikuje sie jako martwa.",
                        cluster_id=f"evolution_{next_index:03d}",
                    )
                )
                next_index += 1

        return proposals
