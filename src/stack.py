"""Docker Compose wrapper: bring Cognee infra (FalkorDB, Postgres, Redis) online."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "docker-compose.yaml"
CORE_SERVICES = ("falkordb", "postgres", "redis")

PORT_CONFLICT_HINT = (
    "A MindCart host port is already in use (5433, 6381, 6382, or 3001). "
    "These are offset from cognee_falkordb (5432/6379/6380/3000) so both "
    "stacks can run at once. Check `docker compose ps` in this repo."
)

_PORT_CONFLICT_MARKERS = (
    "port is already allocated",
    "address already in use",
    "bind: address already in use",
    "failed to bind",
)


def _compose_base(*, qdrant: bool = False) -> list[str]:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    if qdrant:
        cmd.extend(["--profile", "qdrant"])
    return cmd


def ensure_compose() -> None:
    """Require Docker Compose v2 (`docker compose version`)."""
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not on PATH.")
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError("Docker Compose v2 is required (`docker compose version`).") from exc
    if result.returncode != 0:
        raise RuntimeError("Docker Compose v2 is required (`docker compose version`).")


def _is_port_conflict(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _PORT_CONFLICT_MARKERS)


def _run_compose(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _print_banner(*, qdrant: bool) -> None:
    print("\n=== Cognee stack ===")
    print("  graph       FalkorDB @ localhost:6382")
    print("  vector      pgvector @ localhost:5433/cognee")
    print("  relational  Postgres @ localhost:5433/cognee")
    print("  cache       Redis @ localhost:6381")
    print("  ui          http://localhost:3001  (FalkorDB Browser)")
    if qdrant:
        print("  qdrant      Qdrant @ localhost:6334")
    print()


def stack_up(*, qdrant: bool = False) -> int:
    """Start core infra (and optional Qdrant), wait until healthy, print a banner."""
    ensure_compose()
    services = list(CORE_SERVICES)
    if qdrant:
        services.append("qdrant")

    cmd = [*_compose_base(qdrant=qdrant), "up", "-d", "--wait", "--wait-timeout", "120", *services]
    result = _run_compose(cmd, capture=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        combined = f"{result.stdout or ''}{result.stderr or ''}"
        if _is_port_conflict(combined):
            print(PORT_CONFLICT_HINT, file=sys.stderr)
        return result.returncode or 1

    _print_banner(qdrant=qdrant)
    return 0


def stack_down() -> int:
    """Stop containers; keep named volumes (no `-v`)."""
    ensure_compose()
    # Include the qdrant profile so a previously started Qdrant is torn down too.
    cmd = [*_compose_base(qdrant=True), "down"]
    result = _run_compose(cmd)
    return result.returncode


def stack_status() -> int:
    """Show `docker compose ps` for this project."""
    ensure_compose()
    cmd = [*_compose_base(qdrant=True), "ps"]
    result = _run_compose(cmd)
    return result.returncode
