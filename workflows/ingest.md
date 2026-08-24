# Ingest and query

1. Copy `.env.sample` to `.env` and set `LLM_API_KEY`. Optional: `COGNEE_API_URL`, `TENANT_ID`.
2. Start the Cognee stack in this repo (`mindcart stack up`, or `docker compose up -d falkordb postgres redis cognee`). Host ports are offset (8000 / 5433 / 6381 / 6382 / 3001) so cognee_falkordb can stay up for `project_memory`.
3. Run `mindcart ingest .` to index README, docs, skills, rules, and workflows into shared `repo_memory`.
4. Ask questions with `mindcart ask "…"`.
5. Store a personal note with `mindcart remember "…"`.
6. After repo changes, run `mindcart update` (or `mindcart update .`). Unchanged files are skipped. Added files are remembered, changed files are patched via Cognee `data_id`, and removed files are forgotten. MindCart stores that mapping in `.mindcart/ingest_index.json` (gitignored). If the index is missing, `update` runs a full ingest first.
