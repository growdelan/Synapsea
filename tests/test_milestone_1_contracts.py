from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from synapsea.cluster_engine import ClusterEngine
from synapsea.models import CandidateCluster, CategoryProposal, ClassificationDecision, ReviewItem, TaxonomyNode
from synapsea.ollama_client import HttpOllamaTransport, OllamaClient
from synapsea.review_queue import ReviewQueueRepository
from synapsea.taxonomy import TaxonomyRepository


class FakeTransport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.payloads: list[dict[str, object]] = []

    def send(self, payload: dict[str, object]) -> dict[str, object]:
        self.payloads.append(payload)
        return self.response


class Milestone1ContractsTest(unittest.TestCase):
    def test_cluster_engine_detects_three_pattern_types(self) -> None:
        decisions = [
            ClassificationDecision(
                file_path="/virtual/Screenshot-2026-03-24.png",
                category="images",
                reason="image",
                confidence=0.9,
                extension="png",
                tokens=["screenshot", "2026", "03", "24"],
            ),
            ClassificationDecision(
                file_path="/virtual/Screenshot-2026-03-25.png",
                category="images",
                reason="image",
                confidence=0.9,
                extension="png",
                tokens=["screenshot", "2026", "03", "25"],
            ),
            ClassificationDecision(
                file_path="/virtual/invoice_v1.pdf",
                category="documents",
                reason="doc",
                confidence=0.9,
                extension="pdf",
                tokens=["invoice", "v1"],
            ),
            ClassificationDecision(
                file_path="/virtual/invoice_v2.pdf",
                category="documents",
                reason="doc",
                confidence=0.9,
                extension="pdf",
                tokens=["invoice", "v2"],
            ),
            ClassificationDecision(
                file_path="/virtual/archive_001.zip",
                category="archives",
                reason="archive",
                confidence=0.9,
                extension="zip",
                tokens=["archive", "001"],
            ),
            ClassificationDecision(
                file_path="/virtual/archive_002.zip",
                category="archives",
                reason="archive",
                confidence=0.9,
                extension="zip",
                tokens=["archive", "002"],
            ),
        ]

        clusters = ClusterEngine().build_clusters(decisions)

        cluster_types = {cluster.cluster_type for cluster in clusters}
        self.assertIn("token", cluster_types)
        self.assertIn("extension", cluster_types)
        self.assertIn("name_pattern", cluster_types)

    def test_ollama_response_can_be_mapped_to_review_item_and_saved(self) -> None:
        cluster = CandidateCluster(
            cluster_id="cluster_001",
            parent_category="images",
            file_count=2,
            dominant_extensions=["png"],
            top_tokens=["screenshot"],
            pattern_signals={"pattern_similarity": 0.9},
            example_files=["/virtual/Screenshot-2026-03-24.png"],
            candidate_files=[
                "/virtual/Screenshot-2026-03-24.png",
                "/virtual/Screenshot-2026-03-25.png",
            ],
            heuristic_score=0.88,
            cluster_type="name_pattern",
        )
        transport = FakeTransport(
            {
                "should_create_category": True,
                "proposed_category": "screenshots",
                "reason": "Powtarzalny wzorzec nazw i rozszerzen.",
                "confidence": 0.92,
            }
        )

        proposal = OllamaClient(transport).propose_category(cluster)
        review_item = ReviewItem.from_cluster(cluster, proposal, item_id="rev_001")

        self.assertEqual(proposal, CategoryProposal(True, "screenshots", "Powtarzalny wzorzec nazw i rozszerzen.", 0.92))
        self.assertEqual(review_item.status, "pending")
        self.assertEqual(review_item.target_path, "images/screenshots")

        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_repository = ReviewQueueRepository(root / "review_queue.json")
            taxonomy_repository = TaxonomyRepository(root / "taxonomy.json")
            review_repository.add_item(review_item)
            taxonomy_repository.save(
                {"images": TaxonomyNode(children=["screenshots"], status="stable")}
            )

            stored_items = review_repository.list_items()
            stored_taxonomy = taxonomy_repository.load()

            self.assertEqual(len(stored_items), 1)
            self.assertEqual(stored_items[0].proposed_category, "screenshots")
            self.assertIn("images", stored_taxonomy)
            self.assertEqual(stored_taxonomy["images"].children, ["screenshots"])

    def test_invalid_ollama_response_raises_clear_error(self) -> None:
        cluster = CandidateCluster(
            cluster_id="cluster_002",
            parent_category="documents",
            file_count=2,
            dominant_extensions=["pdf"],
            top_tokens=["invoice"],
            pattern_signals={"shared_token_ratio": 1.0},
            example_files=["/virtual/invoice_v1.pdf"],
            candidate_files=["/virtual/invoice_v1.pdf", "/virtual/invoice_v2.pdf"],
            heuristic_score=0.84,
            cluster_type="token",
        )
        client = OllamaClient(FakeTransport({"reason": "brak pol"}))

        with self.assertRaisesRegex(ValueError, "Brak pol w odpowiedzi AI"):
            client.propose_category(cluster)

    def test_http_transport_sends_model_and_parses_wrapped_response(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "response": json.dumps(
                    {
                        "should_create_category": True,
                        "proposed_category": "screenshots",
                        "reason": "Powtarzalny wzorzec.",
                        "confidence": 0.91,
                    }
                )
            }
        ).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with patch("synapsea.ollama_client.request.urlopen", return_value=response) as mocked_urlopen:
            transport = HttpOllamaTransport(
                endpoint="http://localhost:11434/api/generate",
                model="llama3.2",
            )
            payload = {"cluster": {"cluster_id": "cluster_003"}}

            parsed = transport.send(payload)

            self.assertEqual(parsed["proposed_category"], "screenshots")
            http_request = mocked_urlopen.call_args.args[0]
            sent_payload = json.loads(http_request.data.decode("utf-8"))
            self.assertEqual(sent_payload["model"], "llama3.2")
            self.assertEqual(json.loads(sent_payload["prompt"]), payload)
