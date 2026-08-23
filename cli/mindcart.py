"""CLI entrypoint: ingest, ask, remember, update."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ingestion import ingest, update
from src.query import ask, remember


def _not_implemented(exc: NotImplementedError) -> int:
    print(f"not implemented: {exc}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mindcart", description="MindCart repo cognitive cartridge")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_p = sub.add_parser("ingest", help="Index the repo into Cognee")
    ingest_p.add_argument("path", nargs="?", default=".", help="Repo path to ingest")

    ask_p = sub.add_parser("ask", help="Ask a question against repo + tenant memory")
    ask_p.add_argument("question", help="Natural-language question")

    remember_p = sub.add_parser("remember", help="Store a personal note in tenant memory")
    remember_p.add_argument("text", help="Note to remember")

    sub.add_parser("update", help="Re-ingest changed repo files")

    args = parser.parse_args(argv)

    try:
        if args.command == "ingest":
            ingest(args.path)
        elif args.command == "ask":
            print(ask(args.question, tenant_id=""))
        elif args.command == "remember":
            remember(args.text, tenant_id="")
        elif args.command == "update":
            update()
    except NotImplementedError as exc:
        return _not_implemented(exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
