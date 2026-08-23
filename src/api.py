"""HTTP wrappers for the Cognee API (remember/recall endpoints)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.utils import load_config

REMEMBER_TIMEOUT = 600.0
RECALL_TIMEOUT = 120.0


def _base_url() -> str:
    return str(load_config()["cognee_api_url"]).rstrip("/")


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    raise RuntimeError(
        f"Cognee API {response.request.method} {response.request.url} "
        f"-> {response.status_code}: {response.text}"
    )


def remember(docs: str | list[str], dataset_name: str) -> None:
    """Send documents to Cognee ``remember`` for ``dataset_name``."""
    items = [docs] if isinstance(docs, str) else list(docs)
    items = [item for item in items if str(item).strip()]
    if not items:
        raise RuntimeError("remember requires at least one document")

    files = [
        ("data", (f"doc_{index}.txt", text.encode("utf-8"), "text/plain"))
        for index, text in enumerate(items)
    ]
    url = f"{_base_url()}/api/v1/remember"
    try:
        with httpx.Client(timeout=REMEMBER_TIMEOUT) as client:
            response = client.post(
                url,
                data={"datasetName": dataset_name, "run_in_background": "false"},
                files=files,
            )
    except httpx.RequestError as exc:
        raise RuntimeError(f"Cognee API unreachable at {_base_url()}: {exc}") from exc
    _raise_for_status(response)


def recall(query: str, datasets: list[str]) -> str:
    """Call Cognee ``recall`` across ``datasets`` and return the combined result."""
    url = f"{_base_url()}/api/v1/recall"
    payload = {
        "query": query,
        "datasets": datasets,
        "search_type": "GRAPH_COMPLETION",
    }
    try:
        with httpx.Client(timeout=RECALL_TIMEOUT) as client:
            response = client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Cognee API unreachable at {_base_url()}: {exc}") from exc
    _raise_for_status(response)
    return _format_results(response.json())


def _item_text(item: Any) -> str:
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "answer", "search_result", "result"):
            if item.get(key):
                return _item_text(item[key])
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def _format_results(payload: Any) -> str:
    items: Any = payload
    if isinstance(payload, dict):
        items = payload.get("result") or payload.get("results") or payload.get("data") or payload
    if not isinstance(items, list):
        items = [items]
    lines: list[str] = []
    for index, item in enumerate(items, 1):
        text = _item_text(item).strip()
        if text:
            lines.append(f"[{index}] {text}")
    return "\n\n".join(lines) if lines else "(no results)"
