# Tasks — 0001-foundation (source-decay-ledger)

Ordered for the first two to three PRs after this scaffold lands.

## PR 1 — registry plus OPML import

- [ ] Add `pyproject.toml` with `pydantic`, `pyyaml`, `polars`, `pytest`, `ruff`.
- [ ] Add `schemas/source.schema.json` and `schemas/ledger-row.schema.json`.
- [ ] Add `src/sdl/registry/loader.py` plus pydantic models.
- [ ] Add `src/sdl/registry/opml_import.py`.
- [ ] Add `data/sources.yaml` populated from a small hand-built fixture (~10 sources).
- [ ] Add `tests/test_registry_loader.py` and `tests/test_opml_import.py`.
- [ ] Add `scripts/validate_registry.py`.
- [ ] Add `decisions/DEC-SDL-001-yield-thresholds.md` with the v0 KEEP/PROBATION/DROP cutoffs.

## PR 2 — backfill plus scoring

- [ ] Add `src/sdl/backfill/brief_items.py` reading a fixture brief tree under `tests/fixtures/briefs/`.
- [ ] Add `src/sdl/scoring/yield.py`.
- [ ] Add `src/sdl/scoring/verdicts.py`.
- [ ] Add `tests/test_yield.py` covering 30-day and 90-day windows.
- [ ] Add `tests/test_verdicts.py` covering each verdict boundary.
- [ ] Add `scripts/validate_ledger.py` and `scripts/append_only_check.py`.

## PR 3 — ledger writer plus first weekly memo

- [ ] Add `src/sdl/ledger/writer.py` (idempotent on `(item, source)`).
- [ ] Add `src/sdl/render/weekly_memo.py` plus the Jinja template.
- [ ] Add `decisions/source-registry/2026-W25.md` (the first real memo).
- [ ] Add `data/ledger/2026-W25.jsonl`.
- [ ] Add `scripts/voice_lint.py` and wire it as a gate on `decisions/source-registry/`.
- [ ] Update README to point at the first published memo.
