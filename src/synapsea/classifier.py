from __future__ import annotations

from synapsea.models import ClassificationDecision, FileFeatures


IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "rtf", "md"}
ARCHIVE_EXTENSIONS = {"zip", "rar", "7z", "tar", "gz"}


class FileClassifier:
    """Minimalna heurystyka kategorii dla bootstrapu projektu."""

    def classify(self, features: FileFeatures) -> ClassificationDecision:
        extension = features.extension.lower()
        if extension in IMAGE_EXTENSIONS:
            category = "images"
            reason = "Rozszerzenie wskazuje na plik graficzny."
        elif extension in DOCUMENT_EXTENSIONS:
            category = "documents"
            reason = "Rozszerzenie wskazuje na dokument."
        elif extension in ARCHIVE_EXTENSIONS:
            category = "archives"
            reason = "Rozszerzenie wskazuje na archiwum."
        else:
            category = "uncategorized"
            reason = "Brak reguly dla rozszerzenia."

        return ClassificationDecision(
            file_path=features.path,
            category=category,
            reason=reason,
            confidence=0.9 if category != "uncategorized" else 0.4,
            extension=features.extension,
            tokens=features.tokens,
            keywords=features.keywords,
            pattern_signals=features.pattern_signals,
            heuristic_classes=features.heuristic_classes,
        )
