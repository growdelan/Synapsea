from __future__ import annotations

from textual.app import App, ComposeResult

from synapsea.config import AppConfig
from synapsea.tui.controllers.app_controller import AppController
from synapsea.tui.screens.dashboard import DashboardScreen


class SynapseaTuiApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #dashboard-container {
        padding: 1 2;
    }

    #dashboard-title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("d", "show_dashboard", "Dashboard"),
        ("q", "quit", "Wyjscie"),
    ]

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaTuiApp":
        return cls(controller=AppController.from_config(config))

    def compose(self) -> ComposeResult:
        yield from ()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.controller.get_dashboard_snapshot()))

    def action_show_dashboard(self) -> None:
        self.switch_screen(DashboardScreen(self.controller.get_dashboard_snapshot()))
