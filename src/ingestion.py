"""Repo ingestion client: extract files, docs, skills, and rules, then push to Cognee."""


def ingest(path: str) -> None:
    """Extract documentation and code structure from ``path`` and send them to Cognee."""
    raise NotImplementedError("ingest is not implemented yet")


def update() -> None:
    """Re-ingest changed repo files into Cognee."""
    raise NotImplementedError("update is not implemented yet")
