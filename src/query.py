"""Query client: ask Cognee and merge shared repo memory with tenant memory."""


def ask(question: str, tenant_id: str) -> str:
    """Return a contextual answer from shared repo memory plus tenant memory."""
    raise NotImplementedError("ask is not implemented yet")


def remember(text: str, tenant_id: str) -> None:
    """Store a personal note in the tenant's private memory layer."""
    raise NotImplementedError("remember is not implemented yet")
