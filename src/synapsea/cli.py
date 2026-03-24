from __future__ import annotations

import argparse
from pathlib import Path

from synapsea.config import AppConfig
from synapsea.pipeline import SynapseaApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synapsea")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Uruchom pipeline klasyfikacji.")
    run_parser.add_argument("--source", type=Path, default=None, help="Katalog do analizy.")
    run_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")
    run_parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Pomin interpretacje AI i zapis propozycji do review queue.",
    )

    review_parser = subparsers.add_parser("review", help="Pokaz zapisane propozycje review.")
    review_parser.add_argument("--data-dir", type=Path, default=None, help="Katalog danych aplikacji.")

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
    )
    app = SynapseaApp.from_config(config)

    if args.command == "run":
        processed = app.run_once()
        print(f"Processed {processed} file(s).")
        return 0
    if args.command == "review":
        items = app.list_review_items()
        for item in items:
            print(
                f"{item.item_id}\t{item.status}\t{item.parent_category}\t"
                f"{item.proposed_category}\t{item.confidence:.2f}"
            )
        return 0
    if args.command == "apply":
        applied = app.apply_review_item(args.item_id)
        print(f"Applied {applied.item_id} -> {applied.target_path}")
        return 0
    if args.command == "reject":
        rejected = app.reject_review_item(args.item_id)
        print(f"Rejected {rejected.item_id}")
        return 0

    parser.error(f"Nieznana komenda: {args.command}")
    return 2
