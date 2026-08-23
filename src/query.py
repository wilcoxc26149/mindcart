"""Query client: ask Cognee and merge shared repo memory with tenant memory."""

from __future__ import annotations

from src.api import recall
from src.api import remember as api_remember
from src.tenants import shared_dataset, tenant_dataset


def ask(question: str, tenant_id: str) -> str:
    """Return a contextual answer from shared repo memory plus tenant memory."""
    datasets = [shared_dataset(tenant_id), tenant_dataset(tenant_id)]
    return recall(question, datasets)


def remember(text: str, tenant_id: str) -> None:
    """Store a personal note in the tenant's private memory layer."""
    note = text.strip()
    if not note:
        raise RuntimeError("remember text must be non-empty")
    dataset = tenant_dataset(tenant_id)
    api_remember(note, dataset_name=dataset)
    print(f"Remembered note in dataset '{dataset}'.")
