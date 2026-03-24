from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Iterable

from synapsea.classifier import FileClassifier
from synapsea.config import AppConfig
from synapsea.models import ClassificationDecision, FileFeatures
from synapsea.storage import DecisionLogRepository


TOKEN_SPLIT_PATTERN = re.compile(r"[^a-zA-Z0-9]+")


FileIterator = Callable[[], Iterable[Path]]


class SynapseaApp:
    def __init__(
        self,
        source_dir: Path,
        decision_log: DecisionLogRepository,
        classifier: FileClassifier | None = None,
        iter_files: FileIterator | None = None,
    ) -> None:
        self.source_dir = source_dir
        self.decision_log = decision_log
        self.classifier = classifier or FileClassifier()
        self.iter_files = iter_files or self._iter_source_files

    @classmethod
    def from_config(cls, config: AppConfig) -> "SynapseaApp":
        decision_log = DecisionLogRepository(config.data_dir / "classification_log.db")
        return cls(source_dir=config.source_dir, decision_log=decision_log)

    def run_once(self) -> int:
        processed = 0
        for path in self.iter_files():
            if not isinstance(path, Path):
                continue
            decision = self.classifier.classify(self.extract_features(path))
            self.decision_log.record(decision)
            processed += 1
        return processed

    def _iter_source_files(self) -> Iterable[Path]:
        for path in sorted(self.source_dir.iterdir()):
            if path.is_file():
                yield path

    def extract_features(self, path: Path) -> FileFeatures:
        extension = path.suffix.lower().lstrip(".")
        stem = path.stem.lower()
        tokens = [token for token in TOKEN_SPLIT_PATTERN.split(stem) if token]
        return FileFeatures(path=str(path), extension=extension, tokens=tokens)
