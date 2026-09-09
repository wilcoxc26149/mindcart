# MindCart

A portable cognitive cartridge for any codebase.

MindCart is a repo-native cognitive module that gives any project long-term memory, skills, rules, and contextual intelligence. Drop it into a repo, connect it to a Cognee backend, and your project instantly gains a shared knowledge graph, semantic memory, and multi-tenant reasoning.

MindCart is a bolt-on brain that travels with the repo.

## Features

### Repo-Local Cognitive Cartridge

MindCart lives inside your repo. Clone the repo → you clone the brain.

### Automatic Repo Ingestion

MindCart extracts documentation, code structure, architecture notes, workflows, skills, and rules, then sends them to the Cognee backend for indexing.

### Connects to Cognee Stack (Docker)

MindCart communicates with a Cognee instance that provides:

- FalkorDB (graph memory)
- Postgres + pgvector (metadata + embeddings)
- Qdrant (optional vector store)
- Cognee API server

### Multi-Tenant Memory

Each user or agent gets:

- Shared read access to repo memory
- Private write access to their own memory layer

### Skill + Rule Installation

Cartridge YAML in `/skills/*.yaml` and `/rules/*.yaml` is validated, then:

- Indexed as structured blurbs on `mindcart ingest` (not a raw YAML dump)
- Installed into the **host** project for Cursor:

```bash
mindcart install
# or: mindcart install --target C:\work\other-app
```

That writes `$PROJECT_ROOT/.cursor/skills/{id}/SKILL.md` and `$PROJECT_ROOT/.cursor/rules/{id}.mdc`.

`PROJECT_ROOT` is the project Cursor should see. Resolution order: `--target`, then `PROJECT_ROOT` env, then `project_root` in `config/mindcart.yaml`, then the parent of the `mindcart/` cartridge.

Shipped catalog: `ask`, `remember`, `improve`, and an always-on `recall-first` rule (`mindcart ask` before answering from the model). The `mindcart-todo` skill stays in this repo only — it is not installed into the host.

### Query Engine

Ask the repo questions using natural language:

```bash
mindcart ask "How does the ingestion pipeline work?"
```

MindCart merges shared repo memory with tenant-specific memory and returns a contextual answer.

## Quick Start

### 1. Clone your repo

Your project contains a `/mindcart` directory:

```text
/my-project
   /mindcart
```

### 2. Configure MindCart

Copy `.env.sample` to `.env` and set `LLM_API_KEY` (required for ingest/ask). Optional overrides:

```bash
COGNEE_API_URL=http://localhost:8000
TENANT_ID=admin
# Host project for Cursor skills/rules (default: parent of this cartridge)
# PROJECT_ROOT=C:\work\other-app
```

### 3. Start the Cognee Stack

```bash
mindcart stack up
# equivalent: docker compose up -d falkordb postgres redis cognee
```

This launches MindCart's own infra (independent volumes from cognee_falkordb):

- FalkorDB (graph; UI on port 3001)
- Postgres + pgvector (metadata + embeddings) on port 5433
- Redis (session cache) on port 6381
- Cognee API server on port 8000

Host ports are offset so cognee_falkordb can stay up for `project_memory` while you develop MindCart. Qdrant is optional (`mindcart stack up --qdrant`, host 6334).

### 4. Ingest the repo

```bash
mindcart ingest .
```

### 5. Query the repo brain

```bash
mindcart ask "Where is the deployment workflow defined?"
```

### 6. Add personal memory

Text **or** a file (not both). Both land in tenant memory:

```bash
mindcart remember "We use uv for local dev setup."
mindcart remember --file docs/note.md
```

### 7. Update memory when the repo changes

```bash
mindcart update
```

### 8. Install Cursor skills and rules into the host

```bash
mindcart install
```

Agents should recall first (`mindcart ask "…"`) before answering from the model. If memory is missing or stale, run `mindcart ingest` or `mindcart update`. Enrich an existing dataset with `mindcart improve` (shared `repo_memory` by default).

## Architecture

```text
                          ┌───────────────────────────┐
                          │        Your Repo           │
                          │  (code, docs, skills)      │
                          └──────────────┬────────────┘
                                         │ ingest
                                         ▼
                     ┌──────────────────────────────────────┐
                     │              MINDCART                 │
                     │      (Repo Cognitive Cartridge)       │
                     ├──────────────────────────────────────┤
                     │  Ingestion Client                     │
                     │  Skill Loader                         │
                     │  Rule Loader                          │
                     │  Tenant Router                        │
                     │  Query Client                         │
                     └──────────────┬───────────────────────┘
                                    │ HTTP
                                    ▼
                     ┌──────────────────────────────────────┐
                     │            COGNEE STACK               │
                     │        (Docker Container)             │
                     ├──────────────────────────────────────┤
                     │  Cognee API Server                    │
                     │  FalkorDB (graph)                     │
                     │  Postgres + pgvector (metadata/embeds)│
                     │  Qdrant (optional vector store)       │
                     └──────────────┬───────────────────────┘
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────────────┐
       │                         MEMORY LAYER                             │
       ├──────────────────────────────────────────────────────────────────┤
       │  Shared Repo Memory (global)                                     │
       │  Tenant Memory (private per user)                                │
       └──────────────┬───────────────────────────────────────────────────┘
                      │
                      ▼
          ┌──────────────────────────────────────────────┐
          │                USERS / AGENTS                │
          ├──────────────────────────────────────────────┤
          │  tenant: admin                               │
          │  tenant: teammate1                           │
          │  tenant: agent42                             │
          └──────────────────────────────────────────────┘
```

## Recommended Project Structure

```text
mindcart/
  config/
    mindcart.yaml
  skills/
    *.yaml
  rules/
    *.yaml
  workflows/
    *.md
  src/
    catalog.py
    configure.py
    ingestion.py
    tenants.py
    query.py
    api.py
    utils.py
  cli/
    mindcart.py
  scripts/
    configure.py
    configure_env.py
    configure_cursor.py
```

Working checklist: [TODO.md](TODO.md).

## Testing

From the cartridge root, create a venv and install the dev extra (includes pytest):

```bash
uv venv
uv pip install -e ".[dev]"
source .venv/bin/activate          # WSL / macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell
```

Then:

```bash
pytest
pytest --run-e2e tests/test_e2e_cognee_host.py
```

Without activating: `.venv/bin/pytest` (or `.venv\Scripts\pytest.exe` on Windows). Do not `apt install python3-pytest` — that is a different, system-wide package.

The e2e test clones [cognee](https://github.com/topoteretes/cognee.git), clones this cartridge into it, and runs `scripts/configure_env.py` plus `scripts/configure_cursor.py`.

## Roadmap

- Skill/rule validation
- Repo-diff incremental ingestion
- Remote Cognee support
- Agent SDK
- VSCode extension
- Multi-repo federation
- MindCart cartridge marketplace

## License

MIT (or your preferred license)

## Contributing

MindCart is designed to be simple, modular, and hackable.

PRs, issues, and discussions are welcome.
