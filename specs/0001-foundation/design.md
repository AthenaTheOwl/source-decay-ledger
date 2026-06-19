# Design — 0001-foundation (source-decay-ledger)

## Shape

A weekly batch over local files plus a small registry. No service,
no scheduler in v0; cron lands in spec 0003. The pipeline reads
the brief items the author has already published, joins them to the
registry by source slug, and emits a memo plus a parquet of scores.

## Components

### Registry (`src/registry/`)

- `loader.py` — reads `data/sources.yaml`, returns a typed
  `RegistryEntry` list with pydantic validation.
- `opml_import.py` — converts an OPML file into registry rows. Used
  once during backfill and again on demand when the OPML changes.
- `validators.py` — schema and slug-shape checks; powers
  `scripts/validate_registry.py`.

### Backfill (`src/backfill/`)

- `brief_items.py` — walks the author's brief repo
  (`../ai-field-brief/briefs/YYYY/*.md`), extracts each item's
  `source_slug` references, writes
  `data/items/YYYY-Wnn.parquet`.

### Scoring (`src/scoring/`)

- `yield.py` — pure function:
  `yield(source, items, window_days) -> int`. Returns the count of
  items in `items` that reference `source` within `window_days` of
  `as_of`.
- `verdicts.py` — applies the thresholds from `DEC-SDL-001` to each
  source's yield and emits a verdict per source.

### Ledger (`src/ledger/`)

- `writer.py` — appends one JSONL row per `(item, source)` edge.
  Idempotent: re-running on the same items does not add duplicate
  rows (dedupe by `item_slug` plus `source_slug`).
- `append_only_check.py` — git-aware: walks
  `data/ledger/*.jsonl` and asserts no row removed or rewritten
  since the last commit on `main`.

### Render (`src/render/`)

- `weekly_memo.py` — emits `decisions/source-registry/YYYY-Wnn.md`
  from the scores parquet and the verdicts.

## Data flow

```
sources.yaml ----+
                 |
brief-item md ---+--> backfill/brief_items.py --> data/items/*.parquet
                                                        |
                                                        v
                                                 scoring/yield.py
                                                        |
                                                        v
                                              data/scores/YYYY-Wnn.parquet
                                                        |
                                                        v
                                               scoring/verdicts.py
                                                        |
                              +-------------------------+
                              v                         v
                  ledger/writer.py            render/weekly_memo.py
                              |                         |
                              v                         v
              data/ledger/YYYY-Wnn.jsonl   decisions/source-registry/YYYY-Wnn.md
```

## Non-goals for 0001

- A fetcher that crawls sources on the network. v0 trusts the brief
  repo as the canonical source of "items the author actually
  referenced." Fetching arrives later under its own spec.
- A scheduler. The weekly pass is run by hand or by a cron line on
  the author's machine.
- Multi-user. One registry, one author.
