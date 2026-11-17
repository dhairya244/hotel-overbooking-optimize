# Where do our screenshots go?

Every number on a slide needs a screenshot that shows the line of code and the output that produced it. Save each one here as `slideNN_what.png`, for example `slide05_method_table.png`, and commit it before Friday's deadline.

## What is already here, and which command makes it?

| File | Made by | What it shows |
|---|---|---|
| `backtest_output.txt` | `python src/backtest.py > evidence/backtest_output.txt` | The proof-period method table with 14 columns (the official run) |
| `backtest_before_feature_change.txt` | the same command, run with the old 16-column `features.py` | The first proof run, kept because the columns changed after it (slide 5 shows both) |
| `late_columns_auc.csv` | `python src/late_columns.py` | Runs A, B and C for `docs/COLUMNS.md` and slide 4 |
| `full_night_share.csv` | `python src/full_night.py` | Share of nearly-full nights per hotel, for slide 10 |
| `tuning_<model>.json`, `tuning_<model>_trials.csv` | notebooks 03, 04 and 05 with `TUNE = True` | How each model's settings were chosen |

Screenshots still to take: none are saved yet.
