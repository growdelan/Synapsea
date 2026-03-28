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
        "--ollama-model",
        type=str,
        default=None,
        help="Nazwa modelu Ollama uzywanego podczas interpretacji AI.",
    )
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
        "--ollama-model",
        type=str,
        default=None,
        help="Nazwa modelu Ollama uzywanego podczas interpretacji AI.",
    )
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
    review_parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="Pokaz wszystkie pozycje review, nie tylko pending.",
    )

    apply_parser = subparsers.add_parser("apply", help="Zatwierdz propozycje review.")
    apply_parser.add_argument("item_ids", nargs="+", help="Id propozycji review.")
    apply_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")

    reject_parser = subparsers.add_parser("reject", help="Odrzuc propozycje review.")
    reject_parser.add_argument("item_ids", nargs="+", help="Id propozycji review.")
    reject_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")

    preferences_parser = subparsers.add_parser("preferences", help="Pokaz podsumowanie preferencji.")
    preferences_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    preferences_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Pokaz dodatkowe szczegoly i liczniki sygnalow.",
    )
    preferences_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maksymalna liczba pozycji w sekcji podsumowania.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig.from_args(
        source=getattr(args, "source", None),
        data_dir=getattr(args, "data_dir", None),
        enable_ai_review=not getattr(args, "skip_ai", False),
        ollama_model=getattr(args, "ollama_model", None),
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
        if not getattr(args, "all_statuses", False):
            items = [item for item in items if item.status == "pending"]
        _print_review_items(items, verbose=getattr(args, "verbose", False))
        return 0
    if args.command == "apply":
        requested = len(args.item_ids)
        succeeded = 0
        failed = 0
        moved = 0
        skipped = 0
        errors = 0
        for item_id in args.item_ids:
            try:
                applied, report = app.apply_review_item(item_id)
            except Exception as exc:
                failed += 1
                print(f"Apply failed {item_id}: {exc}")
                continue
            succeeded += 1
            moved += report.moved
            skipped += report.skipped
            errors += report.errors
            print(
                f"Applied {applied.item_id} -> {applied.target_path} "
                f"(moved={report.moved}, skipped={report.skipped}, errors={report.errors})"
            )
        print(
            f"Batch apply requested={requested} succeeded={succeeded} failed={failed} "
            f"moved={moved} skipped={skipped} errors={errors}"
        )
        return 0 if failed == 0 else 1
    if args.command == "reject":
        requested = len(args.item_ids)
        succeeded = 0
        failed = 0
        for item_id in args.item_ids:
            try:
                rejected = app.reject_review_item(item_id)
            except Exception as exc:
                failed += 1
                print(f"Reject failed {item_id}: {exc}")
                continue
            succeeded += 1
            print(f"Rejected {rejected.item_id}")
        print(f"Batch reject requested={requested} succeeded={succeeded} failed={failed}")
        return 0 if failed == 0 else 1
    if args.command == "watch":
        watcher = WatchService(
            app=app,
            source_dir=config.source_dir,
            poll_interval_seconds=config.watch_poll_interval_seconds,
        )
        watcher.run_forever()
        return 0
    if args.command == "preferences":
        lines = app.preferences_summary(
            limit=max(1, int(getattr(args, "limit", 10))),
            verbose=getattr(args, "verbose", False),
        )
        for line in lines:
            print(line)
        return 0

    parser.error(f"Nieznana komenda: {args.command}")
    return 2


def _print_review_items(items, verbose: bool = False, out: TextIO | None = None) -> None:
    output = out or StringIO()
    for item in items:
        line = (
            f"{item.item_id}\t{item.status}\t{item.parent_category}\t"
            f"{item.proposed_category}\t{item.confidence:.2f}\t"
            f"{item.target_path}\t{len(item.candidate_files)}"
        )
        if out is None:
            print(line)
        else:
            output.write(f"{line}\n")
