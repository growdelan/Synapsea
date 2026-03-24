from __future__ import annotations

import json
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
    def __init__(self, transport: OllamaTransport) -> None:
        self.transport = transport

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        schema = CategoryProposalSchema.model_json_schema()
        payload = {
            "cluster": cluster.to_dict(),
            "instructions": (
                "Oceń czy warto utworzyć kategorię. "
                "Odpowiedz JSON-em z polami should_create_category, "
                "proposed_category, reason, confidence. "
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
