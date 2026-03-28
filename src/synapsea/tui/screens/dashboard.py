from __future__ import annotations

from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from synapsea.tui.controllers.app_controller import DashboardSnapshot


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("q", "app.quit", "Wyjscie"),
    ]

    def __init__(self, snapshot: DashboardSnapshot) -> None:
        super().__init__(id="dashboard")
        self.snapshot = snapshot

    def compose(self):
        yield Header(show_clock=False)
        with Container(id="dashboard-container"):
            yield Static("Synapsea TUI", id="dashboard-title")
            yield Static(self._build_summary(), id="dashboard-summary")
        yield Footer()

    def _build_summary(self) -> str:
        ai_state = "wlaczone" if self.snapshot.ai_enabled else "wylaczone"
        return (
            f"source_dir: {self.snapshot.source_dir}\n"
            f"data_dir: {self.snapshot.data_dir}\n"
            f"AI review: {ai_state}\n"
            f"Ollama model: {self.snapshot.ollama_model}\n"
            f"pending: {self.snapshot.pending_count}\n"
            f"applied: {self.snapshot.applied_count}\n"
            f"rejected: {self.snapshot.rejected_count}\n"
            f"last_run_at: {self.snapshot.last_run_at}\n"
            f"last_operation: {self.snapshot.last_operation_status} - {self.snapshot.last_operation_message}"
        )
