"""Host setup helpers: copy env and install Cursor skills/rules."""

from __future__ import annotations

from pathlib import Path

from src.catalog import install
from src.utils import ROOT


def configure_env(*, root: Path | None = None) -> Path:
    """Copy ``.env.sample`` to ``.env`` when ``.env`` is missing."""
    cartridge = root or ROOT
    sample = cartridge / ".env.sample"
    dest = cartridge / ".env"
    if not sample.is_file():
        raise RuntimeError(f"Missing env sample: {sample}")
    if dest.is_file():
        print(f"Keeping existing {dest}")
        return dest
    dest.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {dest} from .env.sample")
    return dest


def configure_cursor(*, target: str | Path | None = None) -> Path:
    """Install validated skills/rules into the host ``PROJECT_ROOT``."""
    return install(target=target)


def configure(*, target: str | Path | None = None, root: Path | None = None) -> Path:
    """Run env copy then Cursor install."""
    configure_env(root=root)
    return configure_cursor(target=target)
