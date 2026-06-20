# Requirements — 0002-design (v0.1 narrow)

Brand prefix: `SDL`. v0.1 narrows the foundation's 12 requirements to the smallest end-to-end loop: one weekly pass that consumes a sources registry, appends one or more typed ledger rows, computes scores, and writes one memo.

This v0.1 lets a real human run the loop on their own desk before any of the registry-management or OPML-import surface lands.

## Scope cuts vs spec 0001

- No OPML import yet (R-SDL-003 deferred to spec 0003).
- No parquet output for scores yet — JSONL is the v0.1 output. Parquet lands once we have ≥4 weeks of data and a real reader (R-SDL-006 reframed as JSONL for v0.1).
- No CI workflow yet — gates run locally, CI is spec 0004.
- voice_lint runs but uses procurement-lab's banlist for now (R-SDL-010 deferred to ship the lab's prompts; v0.1 includes a minimum vendored list).

## v0.1 requirements

- R-SDL-V1-001: `data/sources.yaml` carries 5–20 source entries with `{slug, name, category, fetch_kind, fetch_target, added_on, verdict}` per R-SDL-001.
- R-SDL-V1-002: `python -m source_decay_ledger validate` exits non-zero on any registry violation. Errors point to the offending entry.
- R-SDL-V1-003: `python -m source_decay_ledger append --week YYYY-Wnn --source <slug> --evidence-url URL [--published-on YYYY-MM-DD]` appends one row to `data/ledger/<YYYY-Wnn>.jsonl` with the schema `{item_slug, published_on, source_slug, evidence_url, appended_at}`.
- R-SDL-V1-004: `python -m source_decay_ledger append-only-check` exits non-zero if any committed ledger file has been rewritten (compares each existing row's content hash against a parallel manifest at `data/ledger/.manifest.jsonl`).
- R-SDL-V1-005: `python -m source_decay_ledger score --week YYYY-Wnn` produces `data/scores/<YYYY-Wnn>.jsonl` with one row per source: `{source_slug, count_90d, count_30d, last_seen_at}`.
- R-SDL-V1-006: `python -m source_decay_ledger memo --week YYYY-Wnn` writes `decisions/source-registry/<YYYY-Wnn>.md` with a ranked yield table + KEEP/PROBATION/DROP lists per `DEC-SDL-001` thresholds. The memo ends with a `## What changed since last week` section that diffs verdict assignments.
- R-SDL-V1-007: `python -m source_decay_ledger --week YYYY-Wnn --dry-run` runs validate → score → memo in order, prints what would be written, exits 0.
- R-SDL-V1-008: `DEC-SDL-001-yield-thresholds.md` documents the KEEP/PROBATION/DROP cutoffs. v0.1 cutoffs (subject to revision after 4 weeks of data): KEEP if count_90d ≥ 3, DROP if count_90d == 0 AND added more than 60 days ago, PROBATION otherwise.
- R-SDL-V1-009: Every CLI command produces typed output (success, error code, JSON-safe diagnostic). The CLI does not log secrets and does not fetch from networks.
- R-SDL-V1-010: tests cover registry validation, ledger append + read, append-only check, scoring, memo generation, and the orchestrated dry-run.
- R-SDL-V1-011: README documents installation (uv sync) + first-run walkthrough (validate a sample registry → append a fake row → score → memo).
- R-SDL-V1-012: voice_lint check on README + memo template + DEC-SDL-001 (uses a vendored minimal banlist for v0.1; will hook to lab voice_lint in v0.2).
