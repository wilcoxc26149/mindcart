# MindCart todo list

Source of truth for remaining work. Retrieve with the `mindcart-todo` skill.
After editing this file, re-ingest into Cognee `project_memory` with `remember_file` (see the skill).

Work top to bottom. Priority is P0 (next) → P1 (product holes) → P2 (roadmap).

## Done

- [x] Stack CLI (`up` / `down` / `status`) with host ports offset from cognee_falkordb
- [x] `mindcart ingest` of configured globs into shared `repo_memory`
- [x] `mindcart ask` across shared + tenant datasets
- [x] `mindcart remember` into `tenant_memory_{id}`
- [x] HTTP wrappers for Cognee `/api/v1/remember` and `/api/v1/recall`
- [x] Unit tests for api, tenants, utils
- [x] Implement `file_hash` in `src/utils.py` (SHA-256 of file contents). Prerequisite for diff-based update.
- [x] Tests for ingestion, query, stack, and CLI. Lock current behavior before `update()` lands.
- [x] Implement `update()` / `mindcart update` in `src/ingestion.py` (repo-diff incremental ingest). Depends on `file_hash`.
- [x] Validate `skills/*.yaml` and `rules/*.yaml`, install them into `$PROJECT_ROOT/.cursor/`, and add `remember --file` plus `mindcart improve`.
- [x] CLI polish (help text, errors, install path).

## Now

### P1 — claimed product that is still missing

5. [ ] Expand ingest beyond README/docs/skills/rules/workflows so code structure is actually indexed.

## Next

### P2 — later roadmap

7. [ ] Remote Cognee support
8. [ ] Agent SDK
9. [ ] VSCode extension
10. [ ] Multi-repo federation
11. [ ] Cartridge marketplace
