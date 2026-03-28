from __future__ import annotations

from collections import Counter
import re

from synapsea.models import LearningSignal, ReviewItem, TaxonomyNode


MIN_REPEAT_SIGNAL_COUNT = 2


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
            _normalize_token(str(signal.details.get("suggested_category", "")))
            for signal in signals
            if signal.signal_type == "manual_rename" and signal.details.get("suggested_category")
        ]
        for token, count in Counter(rename_tokens).items():
            if not token or count < MIN_REPEAT_SIGNAL_COUNT or not _is_valid_rename_token(token):
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
            if count < MIN_REPEAT_SIGNAL_COUNT or not category_name:
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


def _normalize_token(token: str) -> str:
    compact = re.sub(r"\s+", " ", token.strip())
    return compact


def _is_valid_rename_token(token: str) -> bool:
    normalized = token.strip().lower()
    if len(normalized) < 3:
        return False
    if re.fullmatch(r"\d+", normalized):
        return False
    if not re.search(r"[a-ząćęłńóśźż]", normalized):
        return False
    compact = re.sub(r"[^a-z0-9ąćęłńóśźż]", "", normalized)
    digits = sum(char.isdigit() for char in compact)
    letters = sum(char.isalpha() for char in compact)
    if digits and digits >= letters:
        return False
    return True
