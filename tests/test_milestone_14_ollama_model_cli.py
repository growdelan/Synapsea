from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.cli import build_parser
from synapsea.config import AppConfig
from synapsea.ollama_client import HttpOllamaTransport
from synapsea.pipeline import SynapseaApp


class Milestone14OllamaModelCliTest(unittest.TestCase):
    def test_parser_accepts_ollama_model_for_run_and_watch(self) -> None:
        parser = build_parser()

        run_args = parser.parse_args(["run", "--ollama-model", "llama3.1:8b"])
        watch_args = parser.parse_args(["watch", "--ollama-model", "qwen2.5:7b"])

        self.assertEqual(run_args.ollama_model, "llama3.1:8b")
        self.assertEqual(watch_args.ollama_model, "qwen2.5:7b")

    def test_config_uses_custom_model_when_provided(self) -> None:
        config = AppConfig.from_args(
            source=Path("/tmp/source"),
            data_dir=Path("/tmp/data"),
            ollama_model="llama3.1:8b",
        )
        self.assertEqual(config.ollama_model, "llama3.1:8b")

    def test_config_keeps_default_model_when_not_provided(self) -> None:
        config = AppConfig.from_args(source=Path("/tmp/source"), data_dir=Path("/tmp/data"))
        self.assertEqual(config.ollama_model, "gemma3:4b-it-qat")

    def test_app_passes_configured_model_to_ollama_transport(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config = AppConfig(
                source_dir=root / "source",
                data_dir=root / "data",
                ollama_model="llama3.1:8b",
            )

            app = SynapseaApp.from_config(config)

            self.assertIsNotNone(app.proposal_interpreter)
            transport = app.proposal_interpreter.transport
            self.assertIsInstance(transport, HttpOllamaTransport)
            self.assertEqual(transport.model, "llama3.1:8b")
