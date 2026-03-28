from __future__ import annotations

from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmBatchActionModal(ModalScreen[bool]):
    BINDINGS = [
        ("escape", "cancel", "Anuluj"),
        ("enter", "confirm", "Potwierdz"),
    ]

    def __init__(self, *, action_name: str, selected_count: int, warning: str) -> None:
        super().__init__()
        self.action_name = action_name
        self.selected_count = selected_count
        self.warning = warning

    def compose(self):
        with Container(id="confirm-batch-modal"):
            yield Static(f"Potwierdz batch {self.action_name}", id="confirm-title")
            yield Static(f"Wybranych pozycji: {self.selected_count}", id="confirm-count")
            yield Static(self.warning, id="confirm-warning")
            yield Button("Potwierdz", id="confirm-yes", variant="error")
            yield Button("Anuluj", id="confirm-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-yes":
            self.dismiss(True)
        if event.button.id == "confirm-no":
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
