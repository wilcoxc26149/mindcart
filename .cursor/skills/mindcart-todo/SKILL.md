---
name: mindcart-todo
description: >-
  Retrieve or update the MindCart work list (TODO.md). Use when the user asks
  for the mindcart todo list, remaining work, what's left, open tasks, or
  roadmap tasks.
---

# MindCart todo list

`TODO.md` at the mindcart repo root is the source of truth. Do not invent items from chat history.

## Retrieve

1. Read `TODO.md` in the mindcart workspace (`C:\Users\wilco\projects\mindcart\TODO.md` or the workspace-relative `TODO.md`).
2. Present **Now** then **Next** in file order (P0 → P1 → P2). Include **Done** only if the user asks.
3. If the file is missing, say so. Fallback from cognee_falkordb (stack must be up):

```bash
.venv/Scripts/python.exe -u scripts/ask.py "mindcart todo list remaining work"
```

On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`. Run from the cognee_falkordb repo.

## Update

When the user marks something done or adds a task:

1. Edit `TODO.md` (check boxes / add lines). Keep Done / Now / Next sections.
2. Re-ingest into Cognee `project_memory` (no dataset reset) from cognee_falkordb:

```bash
.venv/Scripts/python.exe -u scripts/remember_file.py C:\Users\wilco\projects\mindcart\TODO.md
```

3. Verify:

```bash
.venv/Scripts/python.exe -u scripts/ask.py "What is on the MindCart todo list?"
```

If the stack is down, still save `TODO.md` and tell the user how to remember later.

## Hard rules

- Call `scripts/remember_file.py` — do not call `cognee.forget` or full ingest reset.
- After MindCart repo ingest, `TODO.md` is also in shared `repo_memory` via `mindcart ingest` (glob listed in `config/mindcart.yaml`).
