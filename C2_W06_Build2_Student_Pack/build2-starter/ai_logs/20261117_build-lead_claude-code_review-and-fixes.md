# Build Lead: Claude Code review and fixes, 17 November 2026

**Tool:** Claude Code in VS Code (Claude Sonnet 5.5, then Claude Opus 5.5 from the overfitting check onward).
**Who:** Build Lead.
**Full chat:** _paste the exported transcript below, or link it. In Claude Code, `/export` saves the conversation to a file._

## What we had before the session

We had already built the pipeline: `src/data_loader.py`, `src/features.py`, `src/all_models.py`, `src/k_calculator.py`, `src/backtest.py`, `src/nightly.py`, and the tuning notebooks 03 to 05. Most of the docs were still empty templates.

## What we asked, and what Claude did

| # | We asked | What Claude did | Files it changed or added |
|---|---|---|---|
| 1 | Check whether a virtual environment existed, and install requirements | Found none. Explained the setup, added `seaborn` (used in EDA) to `requirements.txt`, and later fixed the notebook kernel and import path | `requirements.txt`, `.vscode/settings.json`, README setup section |
| 2 | Review the codebase and approach against the rubric | Listed the gaps: no lookup-table baseline, no late-column experiment, no full-night caveat, no buffer column in the nightly table, cleaning not logged, empty docs | none (review only) |
| 3 | Add the lookup baseline | Added `LookupTable` (hotel × deposit type × lead-time band) and put it in `backtest.py` | `src/all_models.py`, `src/backtest.py` |
| 4 | Fix the late-column test, full-night caveat and buffer column | Wrote `late_columns.py` and `full_night.py`, and added `buffer_rooms` to the nightly table | `src/late_columns.py`, `src/full_night.py`, `src/nightly.py` |
| 5 | Fix notebooks that could not import `contract` | Added a path-setup cell to notebooks 01 and EDA, and fixed a hard-coded CSV path in EDA | `notebooks/01_baseline.ipynb`, `notebooks/EDA.ipynb` |
| 6 | Make the architecture diagram | Drew it from the code: black box, both lanes, production additions | `docs/architecture.png`, `docs/PRD.md` section 8 |
| 7 | Write the Build Lead docs | Drafted PRD, BUILD_PLAN, ROADMAP and the AGENTS.md rules. Declined to write the grill log, because it has to come from a real grilling | `docs/PRD.md`, `docs/BUILD_PLAN.md`, `docs/ROADMAP.md`, `AGENTS.md` |
| 8 | Check whether the model is overfitting, and check the features | Compared train with choose for every model. Found mostly drift, not overfitting. Flagged `country` (likely corrected at check-in), `adr` (built during the stay), unused features, and every model under-predicting cancellations | none (analysis only) |
| 9 | Compare feature sets, including our own 9-column idea | Tested 16, 14, 9, 10 and 11 columns on the choose period. Recommended 11 (no guest counts) | none (analysis only) |
| 10 | Apply the change and run everything | Moved `country` and `adr` to bin 2. Found notebooks 04 and 05 were reading an old feature list (`notes/features_simple.py`) and fixed that. Re-tuned all three models, ran the proof once, re-ran the notebooks, saved the 16-column run as evidence, and updated the docs | `src/features.py`, notebooks 03 to 05, `models/`, `evidence/`, docs |
| 11 | Make all paths relative for the team | Fixed the one absolute path (in `build/scratch.ipynb`), made `nightly.py` print a relative path, and added README setup steps | `build/scratch.ipynb`, `src/nightly.py`, `README.md` |
| 12 | Rewrite the docs in plain language, check every Markdown file, and write this log | Shortened the Build Lead docs. Filled the 27 empty rows in `docs/COLUMNS.md` from the dataset's own column definitions, matching the bins in `src/features.py`. Updated `src/README.md` and `evidence/README.md`. Left CHARTER, RFP, both grill logs and COMPARISON for their owners | `docs/*.md`, `src/README.md`, `evidence/README.md`, `README.md`, `ai_logs/` |

## What we kept

- The lookup baseline, the late-column test, the full-night caveat and the `buffer_rooms` column.
- Moving `country` and `adr` to bin 2. Claude's review raised it, and the evidence convinced us: for tour operators, 97% of cancellations are PRT but only 27% of stays.
- The re-tuned settings, and the fix for notebooks 04 and 05.
- The doc drafts, which we then edited.

## What we discarded or changed

- **We kept the guest counts.** Claude suggested 11 columns without `adults`, `children` and `babies`. We kept them because we think party size matters. It costs about EUR 22k on the choose period.
- **We didn't add arrival month and weekday.** We had wanted them in bin 1, but the test showed they made the forest EUR 305k worse.
- **We didn't use the hour estimates in BUILD_PLAN and ROADMAP as they were.** _Replace them with the team's own._
- _Add anything else the team changed or threw away._

## What we checked ourselves

_Write what you verified by hand. For example: re-ran `python src/backtest.py` and `python src/nightly.py --from 2017-08-18 --nights 14`, checked the PRD numbers against `evidence/backtest_output.txt`, and read through `src/all_models.py` `LookupTable` line by line._
