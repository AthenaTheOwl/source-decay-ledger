# Requirements — 0001-foundation (source-decay-ledger)

Brand prefix: `SDL`.

## Scope

The foundation spec names the registry shape, the ledger shape, the
weekly memo shape, and the scoring rule. v0 covers the author's own
brief; the registry shape is generalizable.

## Requirements

- R-SDL-001: `data/sources.yaml` carries one entry per source. Required
  fields per entry: `slug`, `name`, `category`, `fetch_kind`
  (`rss` | `atom` | `html` | `manual`), `fetch_target`, `added_on`,
  `verdict` (`keep` | `probation` | `drop`).
- R-SDL-002: A source slug is `^[a-z0-9][a-z0-9-]{2,40}$` and is
  immutable once added. Renaming the human-facing `name` is allowed;
  renaming the slug is not.
- R-SDL-003: An OPML import populates the registry from the author's
  existing brief reading list. Duplicates by fetch_target merge to one
  entry with both names recorded under `aliases`.
- R-SDL-004: The provenance ledger lives at
  `data/ledger/YYYY-Wnn.jsonl`. Each row records `item_slug`,
  `published_on`, `source_slug`, `evidence_url`, `appended_at`.
- R-SDL-005: The ledger is append-only. The repo ships an
  `append_only_check` script that fails CI on any rewrite of an
  existing row.
- R-SDL-006: The weekly scoring pass computes, per source, the count
  of brief items in the last 90 days that referenced that source and
  the count of items in the last 30 days. Output goes to
  `data/scores/YYYY-Wnn.parquet`.
- R-SDL-007: A weekly memo at `decisions/source-registry/YYYY-Wnn.md`
  contains a ranked yield table, a KEEP list, a PROBATION list, and a
  DROP list. Threshold rules live in `DEC-SDL-001`.
- R-SDL-008: Every memo ends with a `## What changed since last week`
  section that diffs the verdict assignments. First-week memo says
  "no prior week" instead.
- R-SDL-009: A `validate_registry` script asserts every required field
  is present and every `verdict` is one of the three allowed values.
- R-SDL-010: A `voice_lint` pass runs against every memo.
- R-SDL-011: Decision records live under `decisions/DEC-SDL-NNN.md`.
  The first is `DEC-SDL-001-yield-thresholds.md`.
- R-SDL-012: This repo does not fetch from any source it does not have
  the right to read. RSS/Atom/HTML reads respect robots.txt and
  per-source `fetch_target` overrides.
