# source-decay-ledger

Eight sources feed the weekly brief. This week one of them produced an item; the
other seven produced nothing, and one of those seven is on the kill list. The ledger
keeps the count so the reading list can't lie about its own worth.

## What it does

The weekly brief draws on roughly 170 RSS feeds, newsletters, and crawled sources.
Most don't earn their slot. A reading list grows in one direction only — sources get
added, never removed — and the signal rots quietly in the dark while the subscriber
count climbs.

source-decay-ledger makes the list account for itself. A typed registry
(`sources.yaml`) gives every source a slug, a category, a fetch shape, and a current
verdict. A weekly scoring pass joins each published brief item back to the source it
came from and computes a 90-day rolling yield. An append-only provenance ledger
records the brief-item-to-source edge every time a brief publishes, and a sha256
manifest makes that history hard to quietly rewrite. The artifact each week is one
markdown memo at `decisions/source-registry/YYYY-Wnn.md`: ranked yield, a probation
list, a kill list. No dashboard. A source that hasn't produced in 90 days stops being
a habit and becomes a line item with a verdict next to it.

## Try it

Read-only, offline, no setup. It reads the latest committed score file and ranks
every source by 90-day yield:

```bash
uv run sdl show
# (or, without an installed entrypoint)
PYTHONPATH=src python -m source_decay_ledger show
```

```
source-decay-ledger - weekly source verdicts, 2026-W25
8 source(s), ranked by 90-day signal yield (brief items traced back to each source)

source                  90d  30d last seen    verdict
-----------------------------------------------------
The AI Daily Brief        1    1 2026-06-20   PROBATION
Anthropic News            0    0 -            PROBATION
Dwarkesh Patel Podcast    0    0 -            PROBATION
Hugging Face Papers (D    0    0 -            PROBATION
Latent Space              0    0 -            PROBATION
OpenAI Blog               0    0 -            PROBATION
Practical AI              0    0 -            PROBATION
SemiAnalysis (rumors-o    0    0 -            DROP

verdicts: 0 keep, 7 probation, 1 drop
top yield: The AI Daily Brief (1 item(s) in 90d).
kill list: SemiAnalysis (rumors-only filter).
```

The top of the list is what's pulling weight. The bottom is what you're paying
attention to out of habit.

## Live demo

A one-page browser over the same committed data: pick which verdicts to show, read
the per-source yield table, and see the kill list.

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

## How it connects

- [ai-field-brief](https://github.com/AthenaTheOwl/ai-field-brief) — the brief this
  ledger keeps honest. It gets a typed source-quality input instead of a flat
  subscription list.
- [brief-calibration](https://github.com/AthenaTheOwl/brief-calibration) — uses the
  same provenance ledger as the ground-truth source layer behind its per-category
  Brier scoring.

The item-to-source graph the ledger builds is the part the others reuse: any
downstream brief app can ask where a claim came from and get a sourced edge back,
not a guess.

## Run the loop

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

v0.1 ships the first end-to-end loop: registry, append-only ledger, weekly scoring,
and the KEEP/PROBATION/DROP memo, all from the CLI. 8 seed sources committed, 34
tests passing. OPML import and backfill land in spec 0003. See
`specs/0002-design/` for the v0.1 scope cuts.

```bash
uv run pytest -q
# expect: 34 passed

uv run ruff check src tests
# expect: All checks passed

python scripts/voice_lint.py decisions/ README.md
# expect: voice_lint: clean
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

## License

MIT. See [LICENSE](LICENSE).
</content>
</invoke>
