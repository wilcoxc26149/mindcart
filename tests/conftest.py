"""Pytest hooks: opt-in end-to-end tests that clone remotes."""

from __future__ import annotations

import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests that clone remotes (or set MINDCART_E2E=1)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "e2e: host-cartridge end-to-end tests (clone remotes; use --run-e2e)",
    )
    config.addinivalue_line("markers", "network: tests that need network access")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    enabled = config.getoption("--run-e2e") or os.getenv("MINDCART_E2E") == "1"
    if enabled:
        return
    skip_e2e = pytest.mark.skip(reason="need --run-e2e or MINDCART_E2E=1")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
