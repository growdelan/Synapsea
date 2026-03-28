from __future__ import annotations

from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from synapsea.tui.controllers.app_controller import DashboardSnapshot


class DashboardScreen(Screen[None]):
    BINDINGS = [
        ("w", "show_review", "Review"),
        ("r", "run_now", "Run now"),
        ("R", "run_with_options", "Run options"),
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
            with Horizontal(id="dashboard-actions"):
                yield Button("Review", id="show-review")
                yield Button("Run now", id="run-now", variant="primary")
                yield Button("Run with options", id="run-with-options")
                yield Button("Wyjscie", id="quit-app")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "show-review":
            self.action_show_review()
        if event.button.id == "run-now":
            self.action_run_now()
        if event.button.id == "run-with-options":
            self.action_run_with_options()
        if event.button.id == "quit-app":
            self.app.exit()

    def action_run_now(self) -> None:
        self.app.action_run_now()

    def action_show_review(self) -> None:
        self.app.action_show_review()

    def action_run_with_options(self) -> None:
        self.app.action_show_run_options()

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self.snapshot = snapshot
        self.query_one("#dashboard-summary", Static).update(self._build_summary())

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
