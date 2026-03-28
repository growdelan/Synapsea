from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
import shutil


DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "txt",
    "rtf",
    "md",
    "odt",
    "csv",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
}
PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic", "heif", "bmp", "tif", "tiff", "avif"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v", "mpg", "mpeg"}
AUDIO_EXTENSIONS = {"mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff"}
INSTALLER_EXTENSIONS = {"dmg", "pkg", "mpkg", "msi", "exe"}
ARCHIVE_EXTENSIONS = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tgz", "tbz2"}

CANONICAL_STORAGE_DIRS = {
    "documents": "Dokumenty",
    "images": "Zdjęcia",
    "videos": "Filmy",
    "audio": "Audio",
    "installers": "Instalatory",
    "archives": "Archiwa",
    "uncategorized": "Inne",
}
ROOT_DIR_ALIASES = {
    "documents": "documents",
    "document": "documents",
    "dokumenty": "documents",
    "images": "images",
    "image": "images",
    "zdjęcia": "images",
    "zdjecia": "images",
    "videos": "videos",
    "video": "videos",
    "filmy": "videos",
    "audio": "audio",
    "music": "audio",
    "muzyka": "audio",
    "installers": "installers",
    "installer": "installers",
    "instalatory": "installers",
    "archives": "archives",
    "archive": "archives",
    "archiwa": "archives",
    "uncategorized": "uncategorized",
    "other": "uncategorized",
    "inne": "uncategorized",
}
MIGRATION_SOURCE_DIR_ALIASES = {
    "documents": "documents",
    "document": "documents",
    "images": "images",
    "image": "images",
    "videos": "videos",
    "video": "videos",
    "audio": "audio",
    "music": "audio",
    "installers": "installers",
    "installer": "installers",
    "archives": "archives",
    "archive": "archives",
    "uncategorized": "uncategorized",
    "other": "uncategorized",
}


@dataclass(slots=True)
class BootstrapSegregationReport:
    requested: int = 0
    moved: int = 0
    skipped: int = 0
    errors: int = 0


class BootstrapSegregator:
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir

    def segregate_root_files(self) -> BootstrapSegregationReport:
        report = BootstrapSegregationReport()
        self._migrate_legacy_english_roots(report)
        try:
            candidates = sorted(self.source_dir.iterdir())
        except FileNotFoundError:
            return report

        for path in candidates:
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue

            report.requested += 1
            category = self._category_for_extension(path.suffix.lower().lstrip("."))
            destination_dir = self.source_dir / category
            destination_path = destination_dir / path.name

            if destination_path.exists():
                report.skipped += 1
                continue

            try:
                destination_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(destination_path))
                report.moved += 1
            except OSError:
                report.errors += 1
        return report

    def _migrate_legacy_english_roots(self, report: BootstrapSegregationReport) -> None:
        for alias_name, logical_name in MIGRATION_SOURCE_DIR_ALIASES.items():
            legacy_dir = self.source_dir / alias_name
            if not legacy_dir.exists() or not legacy_dir.is_dir():
                continue
            destination_root = self.source_dir / CANONICAL_STORAGE_DIRS[logical_name]
            for legacy_file in sorted(legacy_dir.rglob("*")):
                if not legacy_file.is_file():
                    continue
                relative = legacy_file.relative_to(legacy_dir)
                if any(part.startswith(".") for part in relative.parts):
                    continue
                report.requested += 1
                destination_path = destination_root / relative
                if destination_path.exists():
                    report.skipped += 1
                    continue
                try:
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(legacy_file), str(destination_path))
                    report.moved += 1
                except OSError:
                    report.errors += 1

    def _category_for_extension(self, extension: str) -> str:
        if extension in DOCUMENT_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["documents"]
        if extension in PHOTO_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["images"]
        if extension in VIDEO_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["videos"]
        if extension in AUDIO_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["audio"]
        if extension in INSTALLER_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["installers"]
        if extension in ARCHIVE_EXTENSIONS:
            return CANONICAL_STORAGE_DIRS["archives"]
        return CANONICAL_STORAGE_DIRS["uncategorized"]


def normalize_target_path_for_storage(target_path: str) -> Path:
    raw_parts = [part for part in PurePosixPath(target_path).parts if part and part != "/"]
    if not raw_parts:
        return Path(CANONICAL_STORAGE_DIRS["uncategorized"])
    normalized_root = _normalize_root_segment(raw_parts[0])
    return Path(normalized_root, *raw_parts[1:])


def _normalize_root_segment(segment: str) -> str:
    logical = ROOT_DIR_ALIASES.get(segment.strip().lower())
    if logical is None:
        return CANONICAL_STORAGE_DIRS["uncategorized"]
    return CANONICAL_STORAGE_DIRS[logical]
