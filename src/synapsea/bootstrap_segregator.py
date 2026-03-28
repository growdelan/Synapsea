from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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

    def _category_for_extension(self, extension: str) -> str:
        if extension in DOCUMENT_EXTENSIONS:
            return "Dokumenty"
        if extension in PHOTO_EXTENSIONS:
            return "Zdjęcia"
        if extension in VIDEO_EXTENSIONS:
            return "Filmy"
        if extension in AUDIO_EXTENSIONS:
            return "Audio"
        if extension in INSTALLER_EXTENSIONS:
            return "Instalatory"
        if extension in ARCHIVE_EXTENSIONS:
            return "Archiwa"
        return "Inne"
