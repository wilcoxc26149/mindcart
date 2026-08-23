"""CLI entrypoint: stack, ingest, ask, remember, update."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ingestion import ingest, update
from src.query import ask, remember
from src.stack import stack_down, stack_status, stack_up


def _not_implemented(exc: NotImplementedError) -> int:
    print(f"not implemented: {exc}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mindcart", description="MindCart repo cognitive cartridge")
    sub = parser.add_subparsers(dest="command", required=True)

    stack_p = sub.add_parser("stack", help="Start/stop Cognee infra (Docker)")
    stack_sub = stack_p.add_subparsers(dest="stack_command", required=True)
    up_p = stack_sub.add_parser("up", help="Bring FalkorDB, Postgres, and Redis online")
    up_p.add_argument("--qdrant", action="store_true", help="Also start optional Qdrant")
    stack_sub.add_parser("down", help="Stop containers (keep named volumes)")
    stack_sub.add_parser("status", help="Show container status")

    ingest_p = sub.add_parser("ingest", help="Index the repo into Cognee")
    ingest_p.add_argument("path", nargs="?", default=".", help="Repo path to ingest")

    ask_p = sub.add_parser("ask", help="Ask a question against repo + tenant memory")
    ask_p.add_argument("question", help="Natural-language question")

    remember_p = sub.add_parser("remember", help="Store a personal note in tenant memory")
    remember_p.add_argument("text", help="Note to remember")

    sub.add_parser("update", help="Re-ingest changed repo files")

    args = parser.parse_args(argv)

    try:
        if args.command == "stack":
            if args.stack_command == "up":
                return stack_up(qdrant=args.qdrant)
            if args.stack_command == "down":
                return stack_down()
            return stack_status()
        if args.command == "ingest":
            ingest(args.path)
        elif args.command == "ask":
            print(ask(args.question, tenant_id=""))
        elif args.command == "remember":
            remember(args.text, tenant_id="")
        elif args.command == "update":
            update()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except NotImplementedError as exc:
        return _not_implemented(exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
