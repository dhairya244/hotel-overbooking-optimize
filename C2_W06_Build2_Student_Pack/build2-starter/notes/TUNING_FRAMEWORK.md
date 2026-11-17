# Tuning framework for the model notebooks (03, 04, 05)

Notebook 03 (logistic regression) is the reference implementation. Notebooks 04 (decision tree) and 05 (random forest) get the same section 4, with the model-specific parts listed in the table near the end.

## What the section must achieve

1. Show **how** each hyper-parameter was chosen: every candidate tried, its score, and why the ranges are reasonable.
2. Save the choice so `src/backtest.py` trains with it. `src/all_models.py` reads `models/hyperparams.json`.
3. Keep the proof discipline: tuning uses the **train period only**, in folds that go forward in time. The choose and proof periods never influence the choice.

## Rules (the same for every model)

| Rule | Value |
|---|---|
| Data | `train` only, sorted by `arrival_date` |
| Folds | `TimeSeriesSplit(n_splits=3)`: each fold is tested on bookings after the ones it learned from |
| Score that decides | mean log loss over the folds (lower is better), because the buffer is built from the *sum* of the chances, so the chances must be honest |
| Also recorded | AUC, fit time, the score of every single fold |
| Search | stage 1 wide and coarse, stage 2 a finer search around the best region |
| Tie rule | a candidate is *tied* with the best if its mean fold-by-fold gap to the best is within one standard error of that gap. Among the tied, take the simplest model. `PREFER_SIMPLER = False` takes the lowest log loss instead |
| Duplicates | a candidate tried in both stages counts once (round the grid to 6 significant digits so equal values match) |
| `TUNE = True` | runs the searches, saves everything |
| `TUNE = False` | shows the saved results, runs no search |
| Final model | trained by `all_models.train_<model>(train)`, the same function `backtest.py` calls, so the notebook and `backtest.py` always train the same model |

## The cells, in order

Every notebook replaces its old "## 4. Train the ..." markdown cell and the code cell that starts with `def tune(` with this sequence. Keep the cells after it (the coefficient table, tree printout, forest diagnostics, and so on).

| # | Cell | What it does |
|---|---|---|
| 0 | markdown `## 4. Tune and train the <model>` | One paragraph: what the section shows, and what `TUNE = True / False` does |
| 1 | code: settings and loading | Imports (`datetime`, `json`, `all_models`, `GridSearchCV`, `cross_validate`, plus `RandomizedSearchCV` for 04 and 05). Defines `SEED`, `N_SPLITS`, `CV`, `SCORING`, `PREFER_SIMPLER`, `ordered`, `X_tune`, `y_tune`, `EVIDENCE`, `TRIALS_FILE`, `SUMMARY_FILE`. Sets `trials = summary = None`. If `TUNE` is `False`, loads the saved CSV and JSON when they exist, otherwise prints "nothing saved yet" |
| 2 | markdown `Step 1` + code | A table with one row per setting: what it controls, the range tried, why that range. Then a line saying what is *not* tuned |
| 3 | markdown `Step 2` + code | `run_search(...)` (returns one row per candidate: the settings, `log loss`, `log loss std`, `AUC`, `fit seconds`, `fold 1..3`) and the wide search. Shows every candidate, best first, and an **edge check**: "the best value is at the edge of the range, widen it" or "inside the range" |
| 4 | markdown `Step 3` + code | The finer search around the stage 1 winner. Appends to `trials` with `stage = 2`. Shows the table and the edge check again |
| 5 | markdown `Step 4` + code | Plot: score against each setting, both stages, error bars = spread across folds. Left of the minimum underfits, right overfits |
| 6 | markdown `Step 5` + code | **The best setting.** Dedupes `trials`, finds the lowest log loss, computes the fold-by-fold gap and one standard error for every candidate, keeps the tied ones, picks the simplest. Prints the best setting and the table of tied candidates. Builds `summary` (when `TUNE`) |
| 7 | markdown `Step 6` + code | **Tuned vs default** on the same folds (`cross_validate`): mean log loss and AUC, the difference, and a plain verdict (helped / tiny / worse). Stores `summary["vs_default"]` |
| 8 | markdown `Step 7` + code | When `TUNE`: writes `evidence/tuning_<model>_trials.csv`, `evidence/tuning_<model>.json` and calls `all_models.save_hyperparams("<model>", summary["chosen"])`. Always prints a ready-to-paste row for `docs/DECISIONS.md` (the team decisions table: date, artifact, decision, then three empty cells) |
| 9 | markdown + code `Train the final model` | `model = all_models.train_<model>(train)`, prints the settings used and the number of train bookings |

The edge check, the table, the plot and the tied-candidate table all work from the `trials` DataFrame, so they behave the same whether `trials` was just computed or loaded from the CSV.

## What changes per model

| | Logistic regression (03, done) | Decision tree (04) | Random forest (05) |
|---|---|---|---|
| Model name in the JSON | `"logistic regression"` | `"decision tree"` | `"random forest"` |
| Final model | `all_models.train_logistic` | `all_models.train_tree` | `all_models.train_forest` |
| `make_preparer` | `scale_numbers=True` | `scale_numbers=False` | `scale_numbers=False` |
| Settings tuned | `model__C` | `model__max_depth`, `model__min_samples_leaf`, `model__criterion` | `model__n_estimators`, `model__max_depth`, `model__min_samples_leaf`, `model__max_features` |
| Stage 1 | `GridSearchCV`, `C` from 0.0001 to 100, 13 values on a log scale | `RandomizedSearchCV`, `n_iter` around 30, over a wide space (see below) | `RandomizedSearchCV`, `n_iter` around 20, over a wide space (see below) |
| Stage 2 | 9 values of `C` within half a power of ten of the best | `GridSearchCV` over the neighbours of the stage 1 winner for each setting | `GridSearchCV` over the neighbours of the stage 1 winner for each setting |
| Simplest model among the tied | smallest `C` | smallest `max_depth`, then largest `min_samples_leaf` | smallest `max_depth`, then largest `min_samples_leaf`, then fewest trees |
| Plot | one panel | one panel per numeric setting: the best log loss reached at each value | one panel per numeric setting, same way |
| Edge check | on `C` | on every numeric setting | on every numeric setting |
| Default for "tuned vs default" | `C = 1` | `max_depth = 6`, `min_samples_leaf = 100` (the defaults in `all_models.py`) | `n_estimators = 200`, `max_depth = 12`, `min_samples_leaf = 10` (the defaults in `all_models.py`) |
| Lines to add after the final model | none | `tree = model.named_steps["model"]` and the depth and leaves printout the old cell had | `forest = model.named_steps["model"]` and the tree-count printout the old cell had |

Starting search spaces for 04 and 05. These are suggestions, so check them against the first run's edge checks:

* Decision tree: `max_depth` in 2, 3, 4, 5, 6, 8, 10, 12, 16, 20; `min_samples_leaf` in 10, 20, 50, 100, 200, 400, 800; `criterion` in gini, entropy.
* Random forest: `n_estimators` in 100, 200, 300, 500; `max_depth` in 6, 8, 12, 16, 24, None; `min_samples_leaf` in 3, 5, 10, 20, 50; `max_features` in sqrt, 0.3, 0.5.

With several settings, the trials table has one column per setting. The tied-candidate rule compares whole rows, so dedupe on all of the setting columns. A `None` value for `max_depth` is stored as JSON `null`, and `set_params` accepts it.

## Files the section reads and writes

| File | Written by | Read by | Holds |
|---|---|---|---|
| `models/hyperparams.json` | the notebooks, through `all_models.save_hyperparams` | `all_models.train_*`, so `backtest.py` | only the chosen settings, one entry per model, for example `{"model__C": 0.0133}`. Nothing else may go in an entry, because it is passed to `set_params` |
| `evidence/tuning_<model>_trials.csv` | the notebook | the notebook when `TUNE = False` | every candidate: settings, log loss, spread, AUC, fit time, the three fold scores, the stage |
| `evidence/tuning_<model>.json` | the notebook | the notebook when `TUNE = False` | how the search was run (training dates, folds, scoring, seed, the values searched, number of trials, the rule), the choice, and the tuned vs default numbers |

Commit all three kinds of file, so a fresh checkout trains with the same settings and the evidence travels with the result.

## Lessons from building notebook 03

* **Round the grid** (`float(f"{c:.6g}")`) before searching, otherwise the same value from stage 1 and stage 2 differs in the last digit and shows up twice.
* **Compare candidates fold by fold,** not by the spread of one candidate's score. The folds differ a lot (the first fold learns from very little data), and that noise is shared by all candidates.
* **With 3 folds the standard error is large,** so the tie rule keeps many candidates and can pick a more regularised model than the lowest log loss. In 03 it chose `C = 0.0032` (log loss 0.4196) where the lowest was `C = 0.0133` (log loss 0.4065). That is why `PREFER_SIMPLER` exists: read the chosen row against the plot before accepting it. More folds (`N_SPLITS = 5`) make the rule more reliable, at the cost of runtime.
* **Do not put evidence inside `hyperparams.json`.** `all_models` passes each entry straight to `set_params`, so any extra key would break training.
* **Runtime for 03 was about 15 seconds.** The forest will be much slower: lower `n_iter` for a first pass.

## How to test a notebook after applying the framework

Never test in the real project: a `TUNE = True` run writes `models/hyperparams.json` and `evidence/`.

1. Copy the project (without `.venv`) to a scratch folder.
2. Run the setup cells and every cell of section 4 in one Python process, once with `TUNE = True` and once with `TUNE = False`.
3. Check: the tables and plot appear, the best cell names a setting, the JSON and evidence files are written, the `TUNE = False` run reloads them without searching, and `all_models.train_<model>` reports the saved settings.

## Backups

The notebooks as they were before this framework, with their saved outputs, are in `notebooks/old_originals/`.
