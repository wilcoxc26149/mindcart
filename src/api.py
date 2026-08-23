"""HTTP wrappers for the Cognee API (auth, retries, remember/recall endpoints)."""


def remember(docs: str | list[str], dataset_name: str) -> None:
    """Send documents to Cognee ``remember`` for ``dataset_name``."""
    raise NotImplementedError("remember is not implemented yet")


def recall(query: str, datasets: list[str]) -> str:
    """Call Cognee ``recall`` across ``datasets`` and return the combined result."""
    raise NotImplementedError("recall is not implemented yet")
