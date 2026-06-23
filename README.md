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

v0.1 — first end-to-end loop ships. The registry, append-only ledger,
weekly scoring, and KEEP/PROBATION/DROP memo all work from the CLI.
8 seed sources are committed. 34 tests pass.

OPML import and backfill are deferred to spec 0003. See
`specs/0002-design/` for the v0.1 scope cuts.

## How to run

```bash
uv sync

# 1. Validate the source registry
python -m source_decay_ledger validate

# 2. Append one brief-item-to-source row
python -m source_decay_ledger append \
  --week 2026-W25 \
  --source ai-daily-brief \
  --evidence-url https://example.com/brief-item \
  --published-on 2026-06-19

# 3. Verify the append-only invariant
python -m source_decay_ledger append-only-check

# 4. Score this week's sources
python -m source_decay_ledger score --week 2026-W25

# 5. Write the weekly verdict memo
python -m source_decay_ledger memo --week 2026-W25
cat decisions/source-registry/2026-W25.md

# Or: dry-run the whole loop without touching disk
python -m source_decay_ledger --week 2026-W26 --dry-run
```

## Layout

```
src/source_decay_ledger/
  registry.py    typed Source model + load/validate
  ledger.py      append-only writer + sha256 manifest
  score.py       per-source 90d / 30d counts
  memo.py        ranked yield + KEEP/PROBATION/DROP + diff vs prior week
  cli.py         argparse subcommands; composes the loop
data/
  sources.yaml   the registry (8 seed sources)
  ledger/        weekly JSONL files + .manifest.jsonl
  scores/        weekly per-source score files
decisions/
  DEC-SDL-001-yield-thresholds.md
  source-registry/YYYY-Wnn.md   the weekly memo
scripts/
  voice_lint.py  vendored minimum banlist
specs/
  0001-foundation/   the original 12 R-SDL-* requirements
  0002-design/       v0.1 narrowed scope (this is what shipped)
tests/               34 tests across 5 files
```

## Tests + lint

```bash
uv run pytest -q
# expect: 34 passed

uv run ruff check src tests
# expect: All checks passed

python scripts/voice_lint.py decisions/ README.md
# expect: voice_lint: clean
```

## See it without running the loop

```bash
# print a ranked, readable verdict view of the latest committed week
uv run sdl show
# (or, without an installed entrypoint)
PYTHONPATH=src python -m source_decay_ledger show
```

`show` reads the committed `data/scores/<latest>.jsonl` + `data/sources.yaml`,
ranks every source by 90-day yield, and prints the keep / probation / drop
verdicts plus a headline finding. Read-only, offline, exits 0.

## live demo

A one-page browser over the same committed data: pick which verdicts to show,
read the per-source yield table, and see the kill list.

```bash
# local
pip install -r requirements.txt
streamlit run streamlit_app.py
```

`streamlit_app.py` reads `data/scores/*.jsonl` + `data/sources.yaml` relative to
the repo root — no network, no secrets. Deploy on Streamlit Community Cloud:
New app -> repo `AthenaTheOwl/source-decay-ledger`, branch `main`, main file
`streamlit_app.py`.

<!-- live url: https://share.streamlit.io/... (fill in after first deploy) -->

## Compounds with

- Feeds the AI Field Brief pipeline with a typed source-quality input.
- Provides the ground-truth source layer the Brief Calibration Harness
  uses for per-category Brier scoring.
- The provenance ledger gives any downstream brief publication app
  a real item-to-source graph instead of a flat reading list.

## License

MIT. See [LICENSE](LICENSE).
