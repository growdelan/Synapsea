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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig.from_args(
        source=args.source,
        data_dir=args.data_dir,
        enable_ai_review=not getattr(args, "skip_ai", False),
    )
    app = SynapseaApp.from_config(config)

    if args.command == "run":
        processed = app.run_once()
        print(f"Processed {processed} file(s).")
        return 0

    parser.error(f"Nieznana komenda: {args.command}")
    return 2
