"""End-to-end: nest MindCart in a Cognee clone and run configure scripts.

Opt-in: ``pytest --run-e2e tests/test_e2e_cognee_host.py`` (or ``MINDCART_E2E=1``).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

COGNEE_GIT = "https://github.com/topoteretes/cognee.git"
MINDCART_ROOT = Path(__file__).resolve().parents[1]
CLONE_TIMEOUT = 300

_OVERLAY_SKIP = {
    ".git",
    ".venv",
    ".mindcart",
    ".pytest_cache",
    ".env",
    "__pycache__",
    "agent.jar",
    "mindcart.code-workspace",
}


def _git() -> str:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is required for the Cognee host e2e test")
    return git


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 60,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _clone(url: str, dest: Path, *, extra: list[str] | None = None) -> None:
    cmd = [_git(), "clone", *(extra or []), url, str(dest)]
    _run(cmd, timeout=CLONE_TIMEOUT)


def _overlay_worktree(src: Path, dest: Path) -> None:
    """Copy this worktree over a clone so uncommitted cartridge files are tested."""
    for item in src.iterdir():
        if item.name in _OVERLAY_SKIP or item.name.endswith(".egg-info"):
            continue
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv", ".mindcart"),
            )
        else:
            shutil.copy2(item, target)


@pytest.mark.e2e
@pytest.mark.network
def test_clone_cognee_nest_mindcart_and_run_configure_scripts(tmp_path):
    host = tmp_path / "cognee"
    _clone(COGNEE_GIT, host, extra=["--depth", "1", "--single-branch"])
    assert (host / "README.md").is_file()

    cartridge = host / "mindcart"
    _clone(str(MINDCART_ROOT), cartridge, extra=["--depth", "1"])
    _overlay_worktree(MINDCART_ROOT, cartridge)
    assert (cartridge / "scripts" / "configure_env.py").is_file()
    assert (cartridge / "scripts" / "configure_cursor.py").is_file()

    env = os.environ.copy()
    env.pop("PROJECT_ROOT", None)

    _run(
        [sys.executable, "-u", str(cartridge / "scripts" / "configure_env.py")],
        cwd=cartridge,
        env=env,
    )
    cursor = _run(
        [sys.executable, "-u", str(cartridge / "scripts" / "configure_cursor.py")],
        cwd=cartridge,
        env=env,
    )

    assert (cartridge / ".env").is_file()
    assert (host / ".cursor" / "skills" / "ask" / "SKILL.md").is_file()
    assert (host / ".cursor" / "skills" / "remember" / "SKILL.md").is_file()
    assert (host / ".cursor" / "skills" / "improve" / "SKILL.md").is_file()
    rule = host / ".cursor" / "rules" / "recall-first.mdc"
    assert rule.is_file()
    assert "mindcart ask" in rule.read_text(encoding="utf-8")
    assert not (host / ".cursor" / "skills" / "mindcart-todo").exists()
    assert "Installed skill ask" in cursor.stdout
    assert "Installed rule recall-first" in cursor.stdout
