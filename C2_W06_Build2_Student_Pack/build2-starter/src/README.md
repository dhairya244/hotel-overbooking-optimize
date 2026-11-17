# What lives in src, and who writes it?

Feature code now lives in `src/features.py` (bins, cleaning, clue columns, encoding). `notes/features_simple.py` is kept untouched as a reference copy.

| File | Status | Owner | Its one job |
|---|---|---|---|
| `src/data.py` | Given | | Download the bookings and read them exactly as exported |
| `src/contract.py` | Given, never edited | | The client's scoring rule |
| `src/features.py` | Yours | Data Lead | The Bin 1 / 2 / 3 column lists, `clean_bookings`, `add_features`, and the encoding (`make_preparer`). Every choice is logged in `docs/DECISIONS.md` |
| `notes/features_simple.py` | Reference | Data Lead | The original all-in-one script, including the logistic-regression Run A / Run B / random-time-split experiments. Kept untouched; the working code is now in `src/features.py` |
| `src/data_loader.py` | Yours | Data Lead | Load, clean, split by time (train / choose / proof), and add features |
| `src/all_models.py` | Yours | Model Lead | Logistic regression, decision tree and random forest, loads the hyper-parameters the notebooks saved to `models/hyperparams.json` (defaults if none), and the scores |
| `src/k_calculator.py` | Yours | Model Lead | Turn expected cancellations into extra rooms to sell: `k = floor(expected - z x spread)` for models (z = standard deviations), `k = floor(expected) - margin` for the client's flat rule; pick the cheapest buffer inside the walk ceiling on the choose period |
| `src/backtest.py` | Yours | Model Lead | Fit every method on train, choose each buffer on the choose period, run the proof once, print the method table, and save the winner to `models/chosen.joblib`, which you commit. `RUN_PROOF` switch at the top. Trains with the settings tuned in notebooks 03 / 04 / 05 |
| `src/nightly.py` | Yours | Build Lead | Read the saved method and write the oversell table for the nights asked for |

The project ends with these two commands working from a fresh Codespace. Commit `models/` after the final `backtest.py` run, so that `nightly.py` runs from a fresh checkout without retraining, which is how slide 7 runs live:

```bash
python src/backtest.py
python src/nightly.py --from 2017-08-18 --nights 14
```
