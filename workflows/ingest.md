# Ingest and query

1. Start the Cognee stack in this repo (`mindcart stack up`, or `docker compose up -d falkordb postgres redis`). Host ports are offset (5433 / 6381 / 6382 / 3001) so cognee_falkordb can stay up for `project_memory`.
2. Set `COGNEE_API_URL` and `TENANT_ID` (see `.env.sample`).
3. Run `mindcart ingest .` to index docs, skills, rules, and workflows.
4. Ask questions with `mindcart ask "…"`.
5. After repo changes, run `mindcart update`.
