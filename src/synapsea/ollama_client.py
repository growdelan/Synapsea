from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import request

from pydantic import BaseModel, ValidationError

from synapsea.models import CandidateCluster, CategoryProposal


class OllamaTransport(Protocol):
    def send(
        self,
        payload: dict[str, object],
        format_schema: dict[str, object] | str = "json",
    ) -> dict[str, object]:
        pass


class CategoryProposalSchema(BaseModel):
    should_create_category: bool
    proposed_category: str
    reason: str
    confidence: float


@dataclass(slots=True)
class HttpOllamaTransport:
    endpoint: str
    model: str
    timeout_seconds: int = 60

    def send(
        self,
        payload: dict[str, object],
        format_schema: dict[str, object] | str = "json",
    ) -> dict[str, object]:
        request_payload: dict[str, Any] = {
            "model": self.model,
            "prompt": json.dumps(payload, ensure_ascii=False),
            "format": format_schema,
            "stream": False,
            "options": {"temperature": 0},
        }
        body = json.dumps(request_payload).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if "response" in parsed:
            return _parse_json_response(parsed["response"])
        return parsed


class OllamaClient:
    def __init__(self, transport: OllamaTransport, max_examples: int = 3) -> None:
        self.transport = transport
        self.max_examples = max(1, max_examples)

    def build_cluster_fingerprint(self, cluster: CandidateCluster) -> str:
        summary = self._build_cluster_summary(cluster)
        raw = json.dumps(summary, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _build_cluster_summary(self, cluster: CandidateCluster) -> dict[str, object]:
        return {
            "parent_category": cluster.parent_category,
            "file_count": cluster.file_count,
            "dominant_extensions": cluster.dominant_extensions,
            "top_tokens": cluster.top_tokens,
            "pattern_signals": cluster.pattern_signals,
            "example_files": cluster.example_files[: self.max_examples],
            "cluster_type": cluster.cluster_type,
            "heuristic_score": cluster.heuristic_score,
        }

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        schema = CategoryProposalSchema.model_json_schema()
        payload = {
            "cluster": self._build_cluster_summary(cluster),
            "instructions": (
                "Jesteś klasyfikatorem propozycji kategorii plików dla lokalnej aplikacji CLI. "
                "Oceń spójność klastra i zdecyduj, czy warto utworzyć nową podkategorię. "
                "Zasady decyzji: "
                "1) should_create_category=true tylko gdy klaster jest spójny semantycznie: "
                "tokeny i rozszerzenia wskazują jeden temat oraz nazwa kategorii może być konkretna i krótka. "
                "2) should_create_category=false gdy temat jest zbyt ogólny (np. misc, files, new), "
                "sygnały są mieszane lub niejednoznaczne, albo nazwa byłaby sztuczna lub oparta na pojedynczym pliku. "
                "3) proposed_category: 1-3 słowa, małe litery, bez znaków specjalnych, "
                "nazwa rzeczowa i stabilna, bez dat i numerów wersji. "
                "4) confidence: 0.0-1.0, a wartości >=0.75 tylko przy wyraźnej spójności klastra. "
                "Odpowiedz WYŁĄCZNIE poprawnym JSON zgodnym ze schematem: "
                "should_create_category, proposed_category, reason, confidence. "
                "Bez markdown, bez dodatkowych pól, bez komentarzy. "
                f"Użyj dokładnie tego schematu JSON: {json.dumps(schema, ensure_ascii=False)}"
            ),
        }
        response_payload = self.transport.send(payload, format_schema=schema)
        try:
            structured = CategoryProposalSchema.model_validate(response_payload)
        except ValidationError as exc:
            raise ValueError(f"Brak pol w odpowiedzi AI: {exc}") from exc
        return CategoryProposal(
            should_create_category=structured.should_create_category,
            proposed_category=structured.proposed_category,
            reason=structured.reason,
            confidence=structured.confidence,
        )


def _parse_json_response(response_text: str) -> dict[str, object]:
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])
