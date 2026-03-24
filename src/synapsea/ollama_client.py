from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import request

from synapsea.models import CandidateCluster, CategoryProposal


class OllamaTransport(Protocol):
    def send(self, payload: dict[str, object]) -> dict[str, object]:
        pass


@dataclass(slots=True)
class HttpOllamaTransport:
    endpoint: str
    model: str

    def send(self, payload: dict[str, object]) -> dict[str, object]:
        request_payload: dict[str, Any] = {
            "model": self.model,
            "prompt": json.dumps(payload, ensure_ascii=False),
            "stream": False,
        }
        body = json.dumps(request_payload).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=10) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if "response" in parsed:
            return json.loads(parsed["response"])
        return parsed


class OllamaClient:
    def __init__(self, transport: OllamaTransport) -> None:
        self.transport = transport

    def propose_category(self, cluster: CandidateCluster) -> CategoryProposal:
        payload = {
            "cluster": cluster.to_dict(),
            "instructions": (
                "Oceń czy warto utworzyć kategorię. "
                "Odpowiedz JSON-em z polami should_create_category, "
                "proposed_category, reason, confidence."
            ),
        }
        response_payload = self.transport.send(payload)
        return CategoryProposal.from_dict(response_payload)
