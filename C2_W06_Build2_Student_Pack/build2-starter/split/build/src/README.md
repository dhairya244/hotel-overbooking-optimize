# What lives in src, and who writes it?

Feature code lives in `src/features.py` (bins, cleaning, encoding). Every script and notebook uses it, including notebooks 04 and 05, which used `notes/features_simple.py` until 17 November. `notes/features_simple.py` is kept only as a reference copy and still has the old 16-column list, so don't import it.

| File | Status | Owner | Its one job |
|---|---|---|---|
| `src/data.py` | Given | | Download the bookings and read them exactly as exported |
| `src/contract.py` | Given, never edited | | The client's scoring rule |
| `src/features.py` | Yours | Data Lead | The Bin 1 / 2 / 3 column lists (14 columns in Bin 1; `country` and `adr` are Bin 2), `clean_bookings`, `add_features`, and the encoding (`make_preparer`). Every choice is logged in `docs/DECISIONS.md` |
| `notes/features_simple.py` | Reference | Data Lead | The original all-in-one script, including the first Run A / Run B / random-split experiments. Old column list; not used by any code |
| `src/data_loader.py` | Yours | Data Lead | Load, clean, split by time (train / choose / proof), and add features |
| `src/all_models.py` | Yours | Model Lead | The lookup table (hotel × deposit type × lead-time band), logistic regression, decision tree and random forest. Loads the settings the notebooks saved to `models/hyperparams.json` (defaults if none), and the scores |
| `src/k_calculator.py` | Yours | Model Lead | Turn expected cancellations into extra rooms to sell: `k = floor(expected - z x spread)` for models (z = standard deviations), `k = floor(expected) - margin` for the client's flat rule; pick the cheapest buffer inside the walk ceiling on the choose period |
| `src/backtest.py` | Yours | Model Lead | Fit every method on train, choose each buffer on the choose period, run the proof once, print the method table, and save the winner to `models/chosen.joblib`, which you commit. `RUN_PROOF` switch at the top. Trains with the settings tuned in notebooks 03 / 04 / 05 |
| `src/nightly.py` | Yours | Build Lead | Read the saved method and write the oversell table for the nights asked for, including `buffer_rooms` |
| `src/late_columns.py` | Yours | Data Lead | The three-run AUC test in `docs/COLUMNS.md` (bin 1 on a time split, all bins on a time split, bin 1 on a random split). Writes `evidence/late_columns_auc.csv` |
| `src/full_night.py` | Yours | Client Lead | The full-night caveat: the share of nights each hotel was nearly full, using an occupancy estimate. Writes `evidence/full_night_share.csv` |

The project ends with these two commands working from a fresh Codespace. Commit `models/` after the final `backtest.py` run, so that `nightly.py` runs from a fresh checkout without retraining, which is how slide 7 runs live:

```bash
python src/backtest.py
python src/nightly.py --from 2017-08-18 --nights 14
```
