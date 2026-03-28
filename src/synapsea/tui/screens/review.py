from __future__ import annotations

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, SelectionList, Static

from synapsea.tui.controllers.app_controller import ReviewItemSnapshot
from synapsea.tui.modals.result_modal import ResultModal


class ReviewScreen(Screen[None]):
    BINDINGS = [
        ("space", "toggle_current", "Zaznacz"),
        ("x", "select_all_visible", "Zaznacz wszystkie"),
        ("u", "clear_selection", "Wyczysc zaznaczenie"),
        ("a", "apply_selected", "Apply"),
        ("r", "reject_selected", "Reject"),
        ("/", "focus_filter", "Filtr"),
        ("c", "sort_confidence", "Confidence"),
        ("n", "sort_candidate_count", "Candidate files"),
        ("enter", "show_full_detail", "Szczegoly"),
        ("p", "show_pending", "Pending"),
        ("A", "show_all", "Wszystkie"),
        ("d,escape", "show_dashboard", "Dashboard"),
    ]

    def __init__(self, items: list[ReviewItemSnapshot]) -> None:
        super().__init__(id="review")
        self.show_all_statuses = False
        self.items = items
        self.selected_ids: set[str] = set()
        self.text_filter = ""
        self.sort_by = "default"

    def compose(self):
        yield Header(show_clock=False)
        with Vertical():
            with Horizontal(id="review-toolbar"):
                yield Input(placeholder="Filtr tekstowy", id="review-filter")
                yield Button("Sort confidence", id="sort-confidence")
                yield Button("Sort files", id="sort-candidate-count")
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
        selection_list.focus()
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

    def action_focus_filter(self) -> None:
        self.query_one("#review-filter", Input).focus()

    def action_sort_confidence(self) -> None:
        self.sort_by = "confidence"
        self.app.apply_review_filter(show_all_statuses=self.show_all_statuses)

    def action_sort_candidate_count(self) -> None:
        self.sort_by = "candidate_count"
        self.app.apply_review_filter(show_all_statuses=self.show_all_statuses)

    def action_show_dashboard(self) -> None:
        self.app.action_show_dashboard()

    def action_apply_selected(self) -> None:
        self.app.action_apply_selected()

    def action_reject_selected(self) -> None:
        self.app.action_reject_selected()

    def get_selected_ids(self) -> list[str]:
        return [item.item_id for item in self.items if item.item_id in self.selected_ids]

    def action_show_full_detail(self) -> None:
        selection_list = self.query_one(SelectionList)
        highlighted = selection_list.highlighted
        if highlighted is None or highlighted < 0 or highlighted >= len(self.items):
            return
        item = self.items[highlighted]
        body_lines = [
            f"id: {item.item_id}",
            f"status: {item.status}",
            f"parent_category: {item.parent_category}",
            f"proposed_category: {item.proposed_category}",
            f"target_path: {item.target_path}",
            f"confidence: {item.confidence:.2f}",
            f"reason: {item.reason}",
            "candidate_files:",
            *item.candidate_files,
        ]
        self.app.push_screen(ResultModal(title=f"Szczegoly {item.item_id}", body_lines=body_lines))

    def on_selection_list_selection_highlighted(self, message: SelectionList.SelectionHighlighted) -> None:
        self._update_detail(message.selection_index)

    def on_selection_list_selected_changed(self, message: SelectionList.SelectedChanged) -> None:
        self.selected_ids = set(message.selection_list.selected)

    def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id != "review-filter":
            return
        self.text_filter = message.value
        self.app.apply_review_filter(show_all_statuses=self.show_all_statuses)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sort-confidence":
            self.action_sort_confidence()
        if event.button.id == "sort-candidate-count":
            self.action_sort_candidate_count()

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
