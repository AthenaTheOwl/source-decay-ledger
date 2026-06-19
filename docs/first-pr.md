# First PR — source-decay-ledger

The literal first PR after the scaffold. Narrow scope: stand up the
registry, the OPML importer, and the verdict thresholds.

## Title

`feat(SDL): typed source registry plus OPML import (PR 1)`

## Goal

Land the typed registry (`data/sources.yaml`), the loader that gives
the rest of the pipeline typed access to it, and the OPML import that
backfills the registry from the author's existing brief reading list.

## Files added

- `pyproject.toml` — deps: `pydantic`, `pyyaml`, `polars`, `pytest`, `ruff`.
- `src/sdl/__init__.py`
- `src/sdl/registry/__init__.py`
- `src/sdl/registry/loader.py` — pydantic `RegistryEntry` and
  `Registry`; `load(path) -> Registry`; validates slug shape and
  required fields.
- `src/sdl/registry/opml_import.py` — reads an OPML XML file and
  returns a list of `RegistryEntry`. Dedupes by `fetch_target`,
  records duplicate human names as `aliases`.
- `data/sources.yaml` — hand-curated fixture with ten entries spanning
  the categories `semis`, `power`, `agent-ops`, `civic`. Marked as
  a fixture in the file's header comment; the real registry replaces
  it after the OPML import lands.
- `tests/fixtures/sources.opml` — small OPML, ten outlines.
- `tests/test_registry_loader.py` — round-trips the fixture YAML,
  asserts pydantic catches a missing field and a bad slug.
- `tests/test_opml_import.py` — parses the fixture OPML, asserts the
  expected dedupe behavior on a duplicate-target case.
- `schemas/source.schema.json` — JSON Schema for one registry entry;
  paired with the pydantic model in `loader.py`.
- `scripts/validate_registry.py` — walks `data/sources.yaml`,
  validates each row against `schemas/source.schema.json`, exits 1
  on any failure.
- `decisions/DEC-SDL-001-yield-thresholds.md` — the v0 KEEP /
  PROBATION / DROP thresholds for the weekly scoring pass.

## Files not in this PR

- The backfill walker over brief items. PR 2.
- The scoring functions. PR 2.
- The ledger writer. PR 3.
- The first weekly memo. PR 3.
- Any voice-lint script — lands with the first memo.

## Verification

Reviewer runs:

```powershell
uv sync
uv run pytest
uv run python scripts/validate_registry.py
```

Expected: all tests pass; `validate_registry.py` exits 0 against the
ten-row fixture.

## Review checklist

- [ ] Slug regex matches the requirement R-SDL-002.
- [ ] OPML importer dedupes by `fetch_target`, not by human name.
- [ ] No source in the fixture has a `verdict` other than `keep`,
      `probation`, or `drop`.
- [ ] `schemas/source.schema.json` declares `$id` and `$schema`.
- [ ] No marketing words in any added markdown.

## After merge

PR 2 lands the brief-item walker, the yield computation, and the
verdict function. PR 3 wires the ledger writer and ships the first
real weekly memo at `decisions/source-registry/2026-W25.md`.
