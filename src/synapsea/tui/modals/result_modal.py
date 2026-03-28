from __future__ import annotations

from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ResultModal(ModalScreen[None]):
    BINDINGS = [
        ("escape,enter", "close_modal", "Zamknij"),
    ]

    def __init__(self, *, title: str, body_lines: list[str]) -> None:
        super().__init__()
        self.title = title
        self.body_lines = body_lines

    def compose(self):
        with Container(id="result-modal"):
            yield Static(self.title, id="result-title")
            yield Static("\n".join(self.body_lines), id="result-body")
            yield Button("Zamknij", id="result-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "result-close":
            self.dismiss()

    def action_close_modal(self) -> None:
        self.dismiss()
