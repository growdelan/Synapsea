from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from synapsea.ai_state import AiProposalCacheRepository, DeferredClusterRepository
from synapsea.candidate_clusters import CandidateClusterRepository
from synapsea.cluster_engine import ClusterEngine
from synapsea.feature_extractor import FeatureExtractor
from synapsea.models import CandidateCluster, CategoryProposal
from synapsea.ollama_client import OllamaClient
from synapsea.pipeline import SynapseaApp
from synapsea.review_queue import ReviewQueueRepository
from synapsea.storage import DecisionLogRepository


class FakeProposalInterpreter:
    def __init__(self) -> None:
        self.calls = 0

    def build_cluster_fingerprint(self, cluster: CandidateCluster) -> str:
        return f"{cluster.parent_category}:{cluster.cluster_type}:{'|'.join(cluster.top_tokens)}:{cluster.file_count}"

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        self.calls += 1
        token = cluster.top_tokens[0] if cluster.top_tokens else "group"
        return CategoryProposal(
            should_create_category=True,
            proposed_category=f"{token}_group",
            reason="Powtarzalny wzorzec klastrow.",
            confidence=0.9,
        )


class CaptureTransport:
    def __init__(self) -> None:
        self.last_payload: dict[str, object] | None = None

    def send(self, payload: dict[str, object], format_schema="json") -> dict[str, object]:
        self.last_payload = payload
        return {
            "should_create_category": True,
            "proposed_category": "screenshots",
            "reason": "wzor",
            "confidence": 0.9,
        }


class Milestone8AiOptimizationTest(unittest.TestCase):
    def test_budget_and_cache_reduce_repeated_ai_calls(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "downloads"
            source_dir.mkdir()
            (source_dir / "Screenshot-2026-03-24.png").write_text("stub", encoding="utf-8")
            (source_dir / "Screenshot-2026-03-25.png").write_text("stub", encoding="utf-8")
            (source_dir / "invoice_v1.pdf").write_text("stub", encoding="utf-8")
            (source_dir / "invoice_v2.pdf").write_text("stub", encoding="utf-8")

            decision_log = DecisionLogRepository(root / "classification_log.db")
            cluster_repository = CandidateClusterRepository(root / "candidate_clusters.json")
            review_repository = ReviewQueueRepository(root / "review_queue.json")
            deferred_repository = DeferredClusterRepository(root / "deferred_clusters.json")
            cache_repository = AiProposalCacheRepository(root / "ai_proposal_cache.json")
            interpreter = FakeProposalInterpreter()

            app = SynapseaApp(
                source_dir=source_dir,
                decision_log=decision_log,
                feature_extractor=FeatureExtractor(),
                cluster_engine=ClusterEngine(),
                candidate_clusters=cluster_repository,
                review_queue=review_repository,
                proposal_interpreter=interpreter,
                deferred_clusters=deferred_repository,
                ai_proposal_cache=cache_repository,
                ai_budget_per_cycle=1,
            )

            app.run_once()
            first_calls = interpreter.calls
            self.assertEqual(first_calls, 1)
            self.assertGreater(len(deferred_repository.load()), 0)

            app.run_once()
            self.assertGreater(interpreter.calls, first_calls)

            calls_after_second = interpreter.calls
            impacted = {decision.category for decision in decision_log.list_all()}
            app.refresh_candidate_clusters(impacted)
            self.assertEqual(interpreter.calls, calls_after_second)

    def test_ollama_payload_uses_compact_cluster_summary(self) -> None:
        transport = CaptureTransport()
        client = OllamaClient(transport, max_examples=2)
        cluster = CandidateCluster(
            cluster_id="cluster_001",
            parent_category="images",
            file_count=4,
            dominant_extensions=["png"],
            top_tokens=["screenshot", "2026"],
            pattern_signals={"pattern_similarity": 0.9},
            example_files=["/tmp/a.png", "/tmp/b.png", "/tmp/c.png"],
            candidate_files=["/tmp/a.png", "/tmp/b.png", "/tmp/c.png", "/tmp/d.png"],
            heuristic_score=0.9,
            cluster_type="token",
        )

        client.propose_category(cluster)

        assert transport.last_payload is not None
        payload_cluster = transport.last_payload["cluster"]
        self.assertIsInstance(payload_cluster, dict)
        payload_cluster_dict = json.loads(json.dumps(payload_cluster))
        self.assertNotIn("candidate_files", payload_cluster_dict)
        self.assertEqual(len(payload_cluster_dict["example_files"]), 2)


if __name__ == "__main__":
    unittest.main()
