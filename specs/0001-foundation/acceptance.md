# Acceptance — 0001-foundation (source-decay-ledger)

v0 is done when the following commands all succeed on a clean clone.

## Commands

```powershell
uv sync
uv run sdl import opml tests/fixtures/sources.opml
uv run sdl backfill items tests/fixtures/briefs --since 2026-01-01
uv run sdl score --as-of 2026-06-19 --window 90d
uv run sdl report --week 2026-W25
uv run pytest
uv run python scripts/validate_registry.py
uv run python scripts/validate_ledger.py
uv run python scripts/append_only_check.py
uv run python scripts/voice_lint.py
```

## Gates that must pass

- All tests pass under `pytest`.
- `validate_registry.py` exits 0: every source has the required fields
  and a valid `verdict`.
- `validate_ledger.py` exits 0: every JSONL row parses and references
  a known source slug.
- `append_only_check.py` exits 0: no ledger row has been rewritten
  or removed since the prior commit on `main`.
- `voice_lint.py` exits 0 against `decisions/source-registry/2026-W25.md`.

## Artifacts produced

- `data/sources.yaml` is populated from the OPML import.
- `data/scores/2026-W25.parquet` is written and matches the schema.
- `data/ledger/2026-W25.jsonl` is written and append-only-safe.
- `decisions/source-registry/2026-W25.md` exists and lints clean.
- `decisions/DEC-SDL-001-yield-thresholds.md` is present and linked
  from the memo.

## What v0 explicitly does not promise

- An on-network fetcher. Item extraction happens against the brief
  repo on disk.
- A scheduler. Weekly cadence is the author's responsibility in v0.
- A UI beyond markdown memos.
- Per-category Brier scoring — that lives in the Brief Calibration
  Harness, which consumes the ledger emitted here.
