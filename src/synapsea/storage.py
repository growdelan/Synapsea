from __future__ import annotations

import sqlite3
from pathlib import Path

from synapsea.models import ClassificationDecision


class DecisionLogRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS classification_log (
                    file_path TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    confidence REAL NOT NULL
                )
                """
            )

    def record(self, decision: ClassificationDecision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO classification_log (file_path, category, reason, confidence)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    category = excluded.category,
                    reason = excluded.reason,
                    confidence = excluded.confidence
                """,
                (
                    decision.file_path,
                    decision.category,
                    decision.reason,
                    decision.confidence,
                ),
            )

    def list_all(self) -> list[ClassificationDecision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT file_path, category, reason, confidence
                FROM classification_log
                ORDER BY file_path
                """
            ).fetchall()
        return [
            ClassificationDecision(
                file_path=row[0],
                category=row[1],
                reason=row[2],
                confidence=row[3],
            )
            for row in rows
        ]
