from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path
from typing import TextIO

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp
from synapsea.watcher import WatchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synapsea")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Uruchom pipeline klasyfikacji.")
    run_parser.add_argument("--source", type=Path, default=None, help="Katalog do analizy.")
    run_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    run_parser.add_argument(
        "--ai-budget",
        type=int,
        default=None,
        help="Maksymalna liczba wywolan AI na pojedynczy przebieg.",
    )
    run_parser.add_argument(
        "--ai-max-examples",
        type=int,
        default=None,
        help="Maksymalna liczba przykladowych plikow przekazywanych do AI.",
    )

    watch_parser = subparsers.add_parser("watch", help="Uruchom ciagly monitoring zmian w katalogu.")
    watch_parser.add_argument("--source", type=Path, default=None, help="Katalog do analizy.")
    watch_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    watch_parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Pomin interpretacje AI i zapis propozycji do review queue.",
    )
    watch_parser.add_argument(
        "--ai-budget",
        type=int,
        default=None,
        help="Maksymalna liczba wywolan AI na pojedynczy przebieg.",
    )
    watch_parser.add_argument(
        "--ai-max-examples",
        type=int,
        default=None,
        help="Maksymalna liczba przykladowych plikow przekazywanych do AI.",
    )
    watch_parser.add_argument(
        "--watch-interval",
        type=float,
        default=None,
        help="Interwal odswiezania watchera w sekundach.",
    )
    run_parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Pomin interpretacje AI i zapis propozycji do review queue.",
    )

    review_parser = subparsers.add_parser("review", help="Pokaz zapisane propozycje review.")
    review_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    review_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Pokaz rozszerzony widok review z pelnym uzasadnieniem i lista plikow.",
    )

    apply_parser = subparsers.add_parser("apply", help="Zatwierdz propozycje review.")
    apply_parser.add_argument("item_id", help="Id propozycji review.")
    apply_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")

    reject_parser = subparsers.add_parser("reject", help="Odrzuc propozycje review.")
    reject_parser.add_argument("item_id", help="Id propozycji review.")
    reject_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig.from_args(
        source=getattr(args, "source", None),
        data_dir=getattr(args, "data_dir", None),
        enable_ai_review=not getattr(args, "skip_ai", False),
        ai_budget_per_cycle=getattr(args, "ai_budget", None),
        ai_max_examples=getattr(args, "ai_max_examples", None),
        watch_poll_interval_seconds=getattr(args, "watch_interval", None),
    )
    app = SynapseaApp.from_config(config)

    if args.command == "run":
        processed = app.run_once()
        print(f"Processed {processed} file(s).")
        return 0
    if args.command == "review":
        items = app.list_review_items()
        _print_review_items(items, verbose=getattr(args, "verbose", False))
        return 0
    if args.command == "apply":
        applied, report = app.apply_review_item(args.item_id)
        print(
            f"Applied {applied.item_id} -> {applied.target_path} "
            f"(moved={report.moved}, skipped={report.skipped}, errors={report.errors})"
        )
        return 0
    if args.command == "reject":
        rejected = app.reject_review_item(args.item_id)
        print(f"Rejected {rejected.item_id}")
        return 0
    if args.command == "watch":
        watcher = WatchService(
            app=app,
            source_dir=config.source_dir,
            poll_interval_seconds=config.watch_poll_interval_seconds,
        )
        watcher.run_forever()
        return 0

    parser.error(f"Nieznana komenda: {args.command}")
    return 2


def _print_review_items(items, verbose: bool = False, out: TextIO | None = None) -> None:
    output = out or StringIO()
    for item in items:
        reason = item.reason if verbose else _truncate(item.reason, 60)
        base = (
            f"{item.item_id}\t{item.status}\t{item.parent_category}\t"
            f"{item.proposed_category}\t{item.confidence:.2f}\t"
            f"{item.target_path}\t{len(item.candidate_files)}\t{reason}"
        )
        if verbose:
            candidate_preview = ",".join(item.candidate_files[:3])
            line = f"{base}\t{candidate_preview}"
        else:
            line = base
        if out is None:
            print(line)
        else:
            output.write(f"{line}\n")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."
