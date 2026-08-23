MindCart
A portable cognitive cartridge for any codebase.
MindCart is a repo‑native cognitive module that gives any project long‑term memory, skills, rules, and contextual intelligence. Drop it into a repo, connect it to a Cognee backend, and your project instantly gains a shared knowledge graph, semantic memory, and multi‑tenant reasoning.

MindCart is a bolt‑on brain that travels with the repo.

Features
Repo‑Local Cognitive Cartridge
MindCart lives inside your repo. Clone the repo → you clone the brain.

Automatic Repo Ingestion
MindCart extracts documentation, code structure, architecture notes, workflows, skills, and rules, then sends them to the Cognee backend for indexing.

Connects to Cognee Stack (Docker)
MindCart communicates with a Cognee instance that provides:

FalkorDB (graph memory)

Postgres + pgvector (metadata + embeddings)

Qdrant (optional vector store)

Cognee API server

Multi‑Tenant Memory
Each user or agent gets:

Shared read access to repo memory

Private write access to their own memory layer

Skill + Rule Installation
MindCart automatically loads:

/skills/*.yaml

/rules/*.yaml

/workflows/*.md

and registers them with the Cognee backend.

Query Engine
Ask the repo questions using natural language:

Code
mindcart ask "How does the ingestion pipeline work?"
MindCart merges shared repo memory with tenant‑specific memory and returns a contextual answer.

Quick Start
1. Clone your repo
Your project contains a /mindcart directory:

Code
/my-project
   /mindcart
2. Start the Cognee Stack
Code
docker compose up -d
This launches:

Cognee API

FalkorDB

Postgres + pgvector

Qdrant (optional)

3. Configure MindCart
Set environment variables:

Code
COGNEE_API_URL=http://localhost:8000
TENANT_ID=chris
4. Ingest the repo
Code
mindcart ingest .
5. Query the repo brain
Code
mindcart ask "Where is the deployment workflow defined?"
6. Add personal memory
Code
mindcart remember "We use uv for local dev setup."
7. Update memory when the repo changes
Code
mindcart update
Architecture
Code
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
          │  tenant: chris                               │
          │  tenant: teammate1                           │
          │  tenant: agent42                             │
          └──────────────────────────────────────────────┘
Recommended Project Structure
Code
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
    ingestion.py
    tenants.py
    query.py
    api.py
    utils.py
  cli/
    mindcart.py
Roadmap
CLI polish

Skill/rule validation

Repo‑diff incremental ingestion

Remote Cognee support

Agent SDK

VSCode extension

Multi‑repo federation

MindCart cartridge marketplace

License
MIT (or your preferred license)

Contributing
MindCart is designed to be simple, modular, and hackable.
PRs, issues, and discussions are welcome.
