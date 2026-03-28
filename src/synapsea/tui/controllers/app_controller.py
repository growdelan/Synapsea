from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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


@dataclass(slots=True)
class BatchActionReport:
    action_name: str
    requested_count: int
    succeeded_count: int
    failed_count: int
    moved: int = 0
    skipped: int = 0
    errors: int = 0
    failures: list[str] | None = None

    def summary_lines(self) -> list[str]:
        lines = [
            f"Akcja: {self.action_name}",
            f"Wybranych pozycji: {self.requested_count}",
            f"Zakonczonych sukcesem: {self.succeeded_count}",
            f"Nieudanych pozycji: {self.failed_count}",
        ]
        if self.action_name == "apply":
            lines.extend(
                [
                    f"Moved: {self.moved}",
                    f"Skipped: {self.skipped}",
                    f"Errors: {self.errors}",
                ]
            )
        if self.failures:
            lines.append("Bledy:")
            lines.extend(self.failures)
        return lines


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

    def get_review_items(
        self,
        *,
        show_all_statuses: bool = False,
        text_filter: str = "",
        sort_by: str = "default",
    ) -> list[ReviewItemSnapshot]:
        items = self.app.list_review_items()
        if not show_all_statuses:
            items = [item for item in items if item.status == "pending"]
        snapshots = [
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
        query = text_filter.strip().lower()
        if query:
            snapshots = [
                item
                for item in snapshots
                if query in item.item_id.lower()
                or query in item.parent_category.lower()
                or query in item.proposed_category.lower()
                or query in item.target_path.lower()
                or query in item.reason.lower()
            ]
        if sort_by == "confidence":
            snapshots.sort(key=lambda item: (-item.confidence, item.item_id))
        if sort_by == "candidate_count":
            snapshots.sort(key=lambda item: (-item.candidate_count, item.item_id))
        return snapshots

    def apply_selected(self, item_ids: list[str]) -> BatchActionReport:
        report = BatchActionReport(
            action_name="apply",
            requested_count=len(item_ids),
            succeeded_count=0,
            failed_count=0,
            failures=[],
        )
        for item_id in item_ids:
            try:
                _item, move_report = self.app.apply_review_item(item_id)
            except Exception as exc:
                report.failed_count += 1
                report.failures.append(f"{item_id}: {exc}")
                continue
            report.succeeded_count += 1
            report.moved += move_report.moved
            report.skipped += move_report.skipped
            report.errors += move_report.errors
        self.last_operation_status = "success" if report.failed_count == 0 else "partial"
        self.last_operation_message = (
            f"Batch apply: ok={report.succeeded_count}, failed={report.failed_count}, "
            f"moved={report.moved}, skipped={report.skipped}, errors={report.errors}"
        )
        return report

    def reject_selected(self, item_ids: list[str]) -> BatchActionReport:
        report = BatchActionReport(
            action_name="reject",
            requested_count=len(item_ids),
            succeeded_count=0,
            failed_count=0,
            failures=[],
        )
        for item_id in item_ids:
            try:
                self.app.reject_review_item(item_id)
            except Exception as exc:
                report.failed_count += 1
                report.failures.append(f"{item_id}: {exc}")
                continue
            report.succeeded_count += 1
        self.last_operation_status = "success" if report.failed_count == 0 else "partial"
        self.last_operation_message = (
            f"Batch reject: ok={report.succeeded_count}, failed={report.failed_count}"
        )
        return report

    def run_with_options(self, payload: dict[str, str | bool]) -> DashboardSnapshot:
        source_dir = Path(str(payload.get("source_dir") or self.config.source_dir)).expanduser()
        data_dir = Path(str(payload.get("data_dir") or self.config.data_dir)).expanduser()
        enable_ai_review = not bool(payload.get("skip_ai", not self.config.enable_ai_review))
        ollama_model = str(payload.get("ollama_model") or self.config.ollama_model)
        ai_budget = self._coerce_optional_int(payload.get("ai_budget"), self.config.ai_budget_per_cycle)
        ai_max_examples = self._coerce_optional_int(
            payload.get("ai_max_examples"),
            self.config.ai_max_examples,
        )
        self.config = AppConfig(
            source_dir=source_dir,
            data_dir=data_dir,
            ollama_endpoint=self.config.ollama_endpoint,
            ollama_model=ollama_model,
            ollama_timeout_seconds=self.config.ollama_timeout_seconds,
            enable_ai_review=enable_ai_review,
            ai_budget_per_cycle=ai_budget,
            ai_max_examples=ai_max_examples,
            watch_poll_interval_seconds=self.config.watch_poll_interval_seconds,
        )
        self.app = SynapseaApp.from_config(self.config)
        return self.run_now()

    def _coerce_optional_int(self, raw_value: object, fallback: int) -> int:
        text = str(raw_value).strip() if raw_value is not None else ""
        if not text:
            return fallback
        return int(text)
