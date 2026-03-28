from __future__ import annotations

from textual.app import App, ComposeResult

from synapsea.config import AppConfig
from synapsea.tui.controllers.app_controller import AppController
from synapsea.tui.screens.dashboard import DashboardScreen
from synapsea.tui.screens.review import ReviewScreen


class SynapseaTuiApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #review-layout {
        height: 1fr;
    }

    #dashboard-container {
        padding: 1 2;
    }

    #dashboard-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #review-list {
        width: 2fr;
    }

    #review-detail {
        width: 1fr;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("d", "show_dashboard", "Dashboard"),
        ("w", "show_review", "Review"),
        ("r", "run_now", "Run now"),
        ("q", "quit", "Wyjscie"),
    ]

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.dashboard_screen: DashboardScreen | None = None
        self.review_screen: ReviewScreen | None = None

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaTuiApp":
        return cls(controller=AppController.from_config(config))

    def compose(self) -> ComposeResult:
        yield from ()

    def on_mount(self) -> None:
        self.dashboard_screen = DashboardScreen(self.controller.get_dashboard_snapshot())
        self.review_screen = ReviewScreen(self.controller.get_review_items(show_all_statuses=False))
        self.push_screen(self.dashboard_screen)

    def action_show_dashboard(self) -> None:
        if self.dashboard_screen is not None:
            self.dashboard_screen.update_snapshot(self.controller.get_dashboard_snapshot())
        if self.review_screen is not None and self.screen is self.review_screen:
            self.pop_screen()

    def action_show_review(self) -> None:
        if self.review_screen is None:
            return
        self.apply_review_filter(show_all_statuses=self.review_screen.show_all_statuses)
        if self.screen is not self.review_screen:
            self.push_screen(self.review_screen)

    def action_run_now(self) -> None:
        snapshot = self.controller.run_now()
        if self.dashboard_screen is not None:
            self.dashboard_screen.update_snapshot(snapshot)
        if self.review_screen is not None:
            updated_items = self.controller.get_review_items(show_all_statuses=self.review_screen.show_all_statuses)
            if self.review_screen.is_mounted:
                self.review_screen.refresh_items(
                    updated_items,
                    show_all_statuses=self.review_screen.show_all_statuses,
                )
            else:
                self.review_screen.items = updated_items

    def apply_review_filter(self, *, show_all_statuses: bool) -> None:
        if self.review_screen is None:
            return
        filtered_items = self.controller.get_review_items(show_all_statuses=show_all_statuses)
        if self.review_screen.is_mounted:
            self.review_screen.refresh_items(
                filtered_items,
                show_all_statuses=show_all_statuses,
            )
        else:
            self.review_screen.show_all_statuses = show_all_statuses
            self.review_screen.items = filtered_items
