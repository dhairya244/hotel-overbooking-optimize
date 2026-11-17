# Which AI chats did we use, and what did we keep?

**Owner:** Data Lead. One row per file in this folder. Files are named `YYYYMMDD_role_tool_purpose.md` and hold the share link and the pasted text.

| File | Role | Tool | Artifact it fed | What we kept | What we discarded |
|---|---|---|---|---|---|
| Grill run 1 (required) | Client Lead | | `docs/grill_01_charter.md` | | |
| Grill run 2 (required) | Build Lead | | `docs/grill_02_prd.md` | | |
| `karpathy_effect.md` (required) | Build Lead | | `AGENTS.md` | | |
| AI benchmark chat (required) | Data Lead | | `ai-benchmark` branch | | |
| `20261117_build-lead_claude-code_review-and-fixes.md` | Build Lead | Claude Code (VS Code) | `src/all_models.py`, `src/features.py`, `src/late_columns.py`, `src/full_night.py`, `src/nightly.py`, notebooks 01 and 03 to 05, `docs/PRD.md`, `docs/COLUMNS.md` (bins for all 32 columns), `docs/DECISIONS.md`, `docs/BUILD_PLAN.md`, `docs/ROADMAP.md`, `docs/architecture.png`, `AGENTS.md` | Lookup baseline, late-column test, full-night caveat, buffer column, `country` and `adr` moved to bin 2, re-tuned settings, notebook fixes, doc drafts | The 11-column suggestion (we kept guest counts), arrival month and weekday as inputs, the hour estimates |
| `docs/grill_02_prd.md` (retrospective summary, not a transcript) | Build Lead | Claude Code review summary and Codex follow-up | `docs/PRD.md`, `src/features.py`, `src/all_models.py`, `src/backtest.py`, `src/nightly.py` | Logged the feature-timing concern, lookup comparison, and nightly-output/live-data limitation | This does not replace a genuine grill-me session or exported transcript |
