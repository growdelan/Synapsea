from __future__ import annotations

from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Static

from synapsea.config import AppConfig


class RunOptionsModal(ModalScreen[dict[str, str | bool] | None]):
    BINDINGS = [
        ("escape", "cancel", "Anuluj"),
        ("enter", "submit", "Uruchom"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config

    def compose(self):
        with Container(id="run-options-modal"):
            yield Static("Run with options", id="run-options-title")
            yield Input(value=str(self.config.source_dir), id="run-source")
            yield Input(value=str(self.config.data_dir), id="run-data-dir")
            yield Input(value=self.config.ollama_model, id="run-ollama-model")
            yield Input(value=str(self.config.ai_budget_per_cycle), id="run-ai-budget")
            yield Input(value=str(self.config.ai_max_examples), id="run-ai-max-examples")
            yield Checkbox("Skip AI", value=not self.config.enable_ai_review, id="run-skip-ai")
            yield Button("Uruchom", id="run-submit", variant="primary")
            yield Button("Anuluj", id="run-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-submit":
            self.action_submit()
        if event.button.id == "run-cancel":
            self.action_cancel()

    def action_submit(self) -> None:
        self.dismiss(
            {
                "source_dir": self.query_one("#run-source", Input).value,
                "data_dir": self.query_one("#run-data-dir", Input).value,
                "ollama_model": self.query_one("#run-ollama-model", Input).value,
                "ai_budget": self.query_one("#run-ai-budget", Input).value,
                "ai_max_examples": self.query_one("#run-ai-max-examples", Input).value,
                "skip_ai": self.query_one("#run-skip-ai", Checkbox).value,
            }
        )

    def action_cancel(self) -> None:
        self.dismiss(None)
