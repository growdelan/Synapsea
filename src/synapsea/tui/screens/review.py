from __future__ import annotations

from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, SelectionList, Static

from synapsea.tui.controllers.app_controller import ReviewItemSnapshot


class ReviewScreen(Screen[None]):
    BINDINGS = [
        ("space", "toggle_current", "Zaznacz"),
        ("x", "select_all_visible", "Zaznacz wszystkie"),
        ("u", "clear_selection", "Wyczysc zaznaczenie"),
        ("a", "apply_selected", "Apply"),
        ("r", "reject_selected", "Reject"),
        ("p", "show_pending", "Pending"),
        ("A", "show_all", "Wszystkie"),
        ("d,escape", "show_dashboard", "Dashboard"),
    ]

    def __init__(self, items: list[ReviewItemSnapshot]) -> None:
        super().__init__(id="review")
        self.show_all_statuses = False
        self.items = items
        self.selected_ids: set[str] = set()

    def compose(self):
        yield Header(show_clock=False)
        with Horizontal(id="review-layout"):
            yield SelectionList(id="review-list")
            yield Static(id="review-detail")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_items(self.items, show_all_statuses=self.show_all_statuses)

    def refresh_items(self, items: list[ReviewItemSnapshot], *, show_all_statuses: bool) -> None:
        self.show_all_statuses = show_all_statuses
        self.items = items
        visible_ids = {item.item_id for item in items}
        self.selected_ids.intersection_update(visible_ids)
        options = []
        for item in items:
            label = (
                f"{item.item_id} | {item.status} | {item.parent_category} | "
                f"{item.proposed_category} | {item.confidence:.2f} | {item.candidate_count}"
            )
            options.append((label, item.item_id, item.item_id in self.selected_ids))
        selection_list = self.query_one(SelectionList)
        selection_list.clear_options()
        selection_list.add_options(options)
        if items:
            selection_list.highlighted = 0
            self._update_detail(0)
        else:
            self.query_one("#review-detail", Static).update("Brak pozycji review dla biezacego filtra.")

    def action_toggle_current(self) -> None:
        selection_list = self.query_one(SelectionList)
        highlighted = selection_list.highlighted
        if highlighted is None or highlighted < 0 or highlighted >= len(self.items):
            return
        selection_list.toggle(self.items[highlighted].item_id)

    def action_select_all_visible(self) -> None:
        selection_list = self.query_one(SelectionList)
        selection_list.select_all()
        self.selected_ids = {item.item_id for item in self.items}

    def action_clear_selection(self) -> None:
        selection_list = self.query_one(SelectionList)
        selection_list.deselect_all()
        self.selected_ids.clear()

    def action_show_pending(self) -> None:
        self.app.apply_review_filter(show_all_statuses=False)

    def action_show_all(self) -> None:
        self.app.apply_review_filter(show_all_statuses=True)

    def action_show_dashboard(self) -> None:
        self.app.action_show_dashboard()

    def action_apply_selected(self) -> None:
        self.app.action_apply_selected()

    def action_reject_selected(self) -> None:
        self.app.action_reject_selected()

    def get_selected_ids(self) -> list[str]:
        return [item.item_id for item in self.items if item.item_id in self.selected_ids]

    def on_selection_list_selection_highlighted(self, message: SelectionList.SelectionHighlighted) -> None:
        self._update_detail(message.selection_index)

    def on_selection_list_selected_changed(self, message: SelectionList.SelectedChanged) -> None:
        self.selected_ids = set(message.selection_list.selected)

    def _update_detail(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            return
        item = self.items[index]
        detail = (
            f"id: {item.item_id}\n"
            f"status: {item.status}\n"
            f"target_path: {item.target_path}\n"
            f"confidence: {item.confidence:.2f}\n"
            f"candidate_files: {item.candidate_count}\n"
            f"reason: {item.reason}\n"
            f"preview: {', '.join(item.candidate_files[:3]) if item.candidate_files else 'brak'}"
        )
        self.query_one("#review-detail", Static).update(detail)
