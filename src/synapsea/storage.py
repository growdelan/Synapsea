from __future__ import annotations

import json
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
                    confidence REAL NOT NULL,
                    extension TEXT NOT NULL DEFAULT '',
                    tokens_json TEXT NOT NULL DEFAULT '[]',
                    keywords_json TEXT NOT NULL DEFAULT '[]',
                    pattern_signals_json TEXT NOT NULL DEFAULT '{}',
                    heuristic_classes_json TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            self._ensure_column(connection, "extension", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "tokens_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "keywords_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "pattern_signals_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(connection, "heuristic_classes_json", "TEXT NOT NULL DEFAULT '[]'")

    def _ensure_column(self, connection: sqlite3.Connection, column_name: str, definition: str) -> None:
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(classification_log)").fetchall()
        }
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE classification_log ADD COLUMN {column_name} {definition}"
            )

    def record(self, decision: ClassificationDecision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO classification_log (
                    file_path,
                    category,
                    reason,
                    confidence,
                    extension,
                    tokens_json,
                    keywords_json,
                    pattern_signals_json,
                    heuristic_classes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    category = excluded.category,
                    reason = excluded.reason,
                    confidence = excluded.confidence,
                    extension = excluded.extension,
                    tokens_json = excluded.tokens_json,
                    keywords_json = excluded.keywords_json,
                    pattern_signals_json = excluded.pattern_signals_json,
                    heuristic_classes_json = excluded.heuristic_classes_json
                """,
                (
                    decision.file_path,
                    decision.category,
                    decision.reason,
                    decision.confidence,
                    decision.extension,
                    json.dumps(decision.tokens),
                    json.dumps(decision.keywords),
                    json.dumps(decision.pattern_signals),
                    json.dumps(decision.heuristic_classes),
                ),
            )

    def list_all(self) -> list[ClassificationDecision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    file_path,
                    category,
                    reason,
                    confidence,
                    extension,
                    tokens_json,
                    keywords_json,
                    pattern_signals_json,
                    heuristic_classes_json
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
                extension=row[4],
                tokens=json.loads(row[5]),
                keywords=json.loads(row[6]),
                pattern_signals=json.loads(row[7]),
                heuristic_classes=json.loads(row[8]),
            )
            for row in rows
        ]
