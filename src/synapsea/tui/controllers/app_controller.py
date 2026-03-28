from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp


@dataclass(slots=True)
class DashboardSnapshot:
    source_dir: str
    data_dir: str
    ai_enabled: bool
    ollama_model: str
    pending_count: int
    applied_count: int
    rejected_count: int
    last_run_at: str
    last_operation_status: str
    last_operation_message: str


@dataclass(slots=True)
class ReviewItemSnapshot:
    item_id: str
    status: str
    parent_category: str
    proposed_category: str
    confidence: float
    candidate_count: int
    target_path: str
    reason: str
    candidate_files: list[str]


class AppController:
    def __init__(self, config: AppConfig, app: SynapseaApp) -> None:
        self.config = config
        self.app = app
        self.last_run_at = "brak danych"
        self.last_operation_status = "idle"
        self.last_operation_message = "Brak wykonanych operacji."

    @classmethod
    def from_config(cls, config: AppConfig) -> "AppController":
        return cls(config=config, app=SynapseaApp.from_config(config))

    def get_dashboard_snapshot(self) -> DashboardSnapshot:
        items = self.app.list_review_items()
        counts = {"pending": 0, "applied": 0, "rejected": 0}
        for item in items:
            counts[item.status] = counts.get(item.status, 0) + 1
        return DashboardSnapshot(
            source_dir=str(self.config.source_dir),
            data_dir=str(self.config.data_dir),
            ai_enabled=self.config.enable_ai_review,
            ollama_model=self.config.ollama_model,
            pending_count=counts.get("pending", 0),
            applied_count=counts.get("applied", 0),
            rejected_count=counts.get("rejected", 0),
            last_run_at=self.last_run_at,
            last_operation_status=self.last_operation_status,
            last_operation_message=self.last_operation_message,
        )

    def run_now(self) -> DashboardSnapshot:
        try:
            processed = self.app.run_once()
        except Exception as exc:
            self.last_operation_status = "error"
            self.last_operation_message = f"Run zakonczony bledem: {exc}"
        else:
            self.last_run_at = datetime.now().isoformat(timespec="seconds")
            self.last_operation_status = "success"
            self.last_operation_message = f"Processed {processed} file(s)."
        return self.get_dashboard_snapshot()

    def get_review_items(self, *, show_all_statuses: bool = False) -> list[ReviewItemSnapshot]:
        items = self.app.list_review_items()
        if not show_all_statuses:
            items = [item for item in items if item.status == "pending"]
        return [
            ReviewItemSnapshot(
                item_id=item.item_id,
                status=item.status,
                parent_category=item.parent_category,
                proposed_category=item.proposed_category,
                confidence=item.confidence,
                candidate_count=len(item.candidate_files),
                target_path=item.target_path,
                reason=item.reason,
                candidate_files=list(item.candidate_files),
            )
            for item in items
        ]
