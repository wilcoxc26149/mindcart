# Ingest and query

1. Start the Cognee stack (`docker compose up -d` in the Cognee project).
2. Set `COGNEE_API_URL` and `TENANT_ID` (see `.env.sample`).
3. Run `mindcart ingest .` to index docs, skills, rules, and workflows.
4. Ask questions with `mindcart ask "…"`.
5. After repo changes, run `mindcart update`.
