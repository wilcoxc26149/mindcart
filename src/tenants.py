"""Tenant routing: shared repo memory vs private per-user memory."""


def shared_dataset(tenant_id: str) -> str:
    """Return the shared repo-memory dataset name for ``tenant_id``."""
    raise NotImplementedError("shared_dataset is not implemented yet")


def tenant_dataset(tenant_id: str) -> str:
    """Return the private tenant-memory dataset name for ``tenant_id``."""
    raise NotImplementedError("tenant_dataset is not implemented yet")
