from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.scanner import FileScanner


class FileScannerHiddenFilesTest(unittest.TestCase):
    def test_scan_ignores_hidden_files_and_directories(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            visible = root / "visible.txt"
            hidden_file = root / ".DS_Store"
            hidden_dir_file = root / ".cache" / "x.txt"
            nested_hidden_file = root / "docs" / ".keep"

            visible.write_text("ok", encoding="utf-8")
            hidden_file.write_text("hidden", encoding="utf-8")
            hidden_dir_file.parent.mkdir(parents=True, exist_ok=True)
            hidden_dir_file.write_text("hidden", encoding="utf-8")
            nested_hidden_file.parent.mkdir(parents=True, exist_ok=True)
            nested_hidden_file.write_text("hidden", encoding="utf-8")

            scanned = list(FileScanner().scan(root))
            self.assertEqual(scanned, [visible])
