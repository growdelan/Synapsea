from __future__ import annotations

from pathlib import Path
from typing import Iterable


class FileScanner:
    def scan(self, source_dir: Path) -> Iterable[Path]:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                yield path
