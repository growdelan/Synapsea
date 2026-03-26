from __future__ import annotations

from pathlib import Path
from typing import Iterable


class FileScanner:
    def scan(self, source_dir: Path) -> Iterable[Path]:
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source_dir)
            # Ignorujemy ukryte pliki/katalogi (np. .DS_Store), aby nie generowac falszywych delt.
            if any(part.startswith(".") for part in relative.parts):
                continue
            yield path
