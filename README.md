# Source Decay Ledger

Typed registry over the ~170 brief sources. Scores each source weekly
by signal-yield against the user's own published brief items. Emits
KEEP / DROP / PROBATION verdicts plus an immutable item-to-source
provenance ledger.

## What this is

The author's weekly brief draws on roughly 170 RSS feeds, newsletters,
and crawled sources. Most don't earn their slot. Without a forcing
function the reading list grows monotonically; signal-to-noise rots
in the dark.

Source Decay Ledger fixes that with three things:

- A typed source registry (`sources.yaml`) — every source has a slug,
  a category, a fetch shape, and a current verdict.
- A weekly scoring pass that joins published brief items back to the
  sources they came from and computes a 90-day rolling yield.
- An append-only provenance ledger that records the
  brief-item → source(s) edge whenever a brief publishes.

The artifact each week is a single markdown memo:
`decisions/source-registry/YYYY-Wnn.md`. Ranked yield. A kill list. A
probation list. No dashboard.

Bucket: daily. Cadence: weekly. Brand prefix: `SDL`.

## Who this is for

- The author. This is a personal forcing function over the brief.
- Anyone else running a high-volume reading list who wants the same
  discipline — the registry shape and the scoring script are reusable.

## Status

v0 scaffold. No implementation yet. The first PR after the scaffold
backfills the OPML and the last six months of brief items and ships
the first KEEP/DROP/PROBATION report; see `docs/first-pr.md`.

## How to run

Placeholder. Run commands will land in spec `0002-weekly-pass`.
The shape will be:

```powershell
uv sync
uv run sdl import opml ../ai-field-brief/sources.opml
uv run sdl backfill items ../ai-field-brief/briefs --since 2026-01-01
uv run sdl score --window 90d
uv run sdl report --week 2026-W25
```

## Layout

```
source-decay-ledger/
  AGENTS.md
  LICENSE
  README.md
  specs/
    0001-foundation/
      requirements.md
      design.md
      tasks.md
      acceptance.md
  docs/
    first-pr.md
  src/
    registry/           # sources.yaml loader, validators
    backfill/           # OPML import, brief-item harvester
    scoring/            # 90-day yield computation
    ledger/             # append-only provenance writer
    render/             # weekly report template
  data/
    sources.yaml        # the registry (checked in)
    items/              # parquet of harvested brief items (gitignored cache)
    ledger/             # append-only YYYY-Wnn.jsonl files (checked in)
  decisions/
    source-registry/    # weekly KEEP/DROP/PROBATION memos
    DEC-SDL-*           # architectural choices
```

## Compounds with

- Feeds the AI Field Brief pipeline with a typed source-quality input.
- Provides the ground-truth source layer the Brief Calibration Harness
  uses for per-category Brier scoring.
- The provenance ledger gives any downstream brief publication app
  a real item-to-source graph instead of a flat reading list.

## License

MIT. See [LICENSE](LICENSE).
