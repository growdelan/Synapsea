from __future__ import annotations

import re
from pathlib import Path

from synapsea.models import FileFeatures


TOKEN_SPLIT_PATTERN = re.compile(r"[^a-zA-Z0-9]+")
DATE_PATTERN = re.compile(r"\d{4}[-_]\d{2}[-_]\d{2}")
VERSION_PATTERN = re.compile(r"(?:^|[_-])v(?:er)?[_-]?\d+(?:$|[_-])")
NUMBERING_PATTERN = re.compile(r"\d{2,}")


class FeatureExtractor:
    def extract(self, path: Path) -> FileFeatures:
        extension = path.suffix.lower().lstrip(".")
        stem = path.stem.lower()
        tokens = [token for token in TOKEN_SPLIT_PATTERN.split(stem) if token]
        keywords = [token for token in tokens if len(token) >= 4][:5]
        heuristic_classes = self._detect_heuristic_classes(stem, extension)
        pattern_signals = {
            "has_date_ratio": 1.0 if DATE_PATTERN.search(stem) else 0.0,
            "has_version_ratio": 1.0 if VERSION_PATTERN.search(stem) else 0.0,
            "has_numbering_ratio": 1.0 if NUMBERING_PATTERN.search(stem) else 0.0,
        }
        return FileFeatures(
            path=str(path),
            extension=extension,
            tokens=tokens,
            keywords=keywords,
            pattern_signals=pattern_signals,
            heuristic_classes=heuristic_classes,
        )

    def _detect_heuristic_classes(self, stem: str, extension: str) -> list[str]:
        heuristic_classes: list[str] = []
        if "screenshot" in stem or "zrzut" in stem:
            heuristic_classes.append("screenshot_like")
        if "invoice" in stem or "faktura" in stem:
            heuristic_classes.append("invoice_like")
        if extension in {"png", "jpg", "jpeg", "webp", "heic"} and "screen" in stem:
            heuristic_classes.append("screen_capture_like")
        return heuristic_classes
