from __future__ import annotations

from pathlib import Path
from time import sleep
from typing import Callable

from synapsea.bootstrap_segregator import BootstrapSegregationReport
from synapsea.pipeline import SynapseaApp


class WatchService:
    def __init__(
        self,
        app: SynapseaApp,
        source_dir: Path,
        poll_interval_seconds: float = 2.0,
        on_bootstrap_report: Callable[[BootstrapSegregationReport], None] | None = None,
    ) -> None:
        self.app = app
        self.source_dir = source_dir
        self.poll_interval_seconds = max(0.2, poll_interval_seconds)
        self._snapshot: dict[str, tuple[int, int]] | None = None
        self.on_bootstrap_report = on_bootstrap_report

    def run_forever(self) -> None:
        while True:
            self.poll_once()
            sleep(self.poll_interval_seconds)

    def poll_once(self) -> int:
        if self._snapshot is None:
            bootstrap = getattr(self.app, "bootstrap_segregate_root_files", None)
            if callable(bootstrap):
                report = bootstrap()
                if self.on_bootstrap_report is not None and isinstance(report, BootstrapSegregationReport):
                    self.on_bootstrap_report(report)
            current = self._scan_snapshot()
            self._snapshot = current
            if self.app.input_state_repository is not None:
                paths = self.app._collect_current_paths()
                self.app.input_state_repository.save(self.app._build_input_state(paths))
            return 0

        current = self._scan_snapshot()

        if current == self._snapshot:
            return 0

        self._snapshot = current
        try:
            return self.app.run_once()
        except Exception:
            # Błędy pojedynczego przebiegu nie mogą zatrzymać watchera.
            return 0

    def _scan_snapshot(self) -> dict[str, tuple[int, int]]:
        snapshot: dict[str, tuple[int, int]] = {}
        for path in self.app.iter_files():
            if not isinstance(path, Path):
                continue
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            snapshot[str(path)] = (int(stat.st_mtime_ns), int(stat.st_size))
        return snapshot
