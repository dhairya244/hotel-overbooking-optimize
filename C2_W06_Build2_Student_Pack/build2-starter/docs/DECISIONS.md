# What did we decide, and why?

Two tables. The first is the Week 1 decisions log for the data: every cleaning or filtering choice, its reason and how many rows it touched. The second records team decisions and objections under the rule in `docs/ROLES.md`. Add rows; never delete them.

## Which data decisions did we make?

**Owner:** Data Lead.

| Date | Decision | Reason, with the number that justified it | Rows touched | Logged by |
|---|---|---|---|---|
| 2026-11-17 | Drop bookings with no guests (adults + children + babies = 0) | A booking with no guests cannot fill a room. | 180 | |
| 2026-11-17 | Drop the booking with a negative `adr` | A negative rate is a billing error; it would give a negative stay value. | 1 | |
| 2026-11-17 | Fill missing `children` with 0 | Too few to matter, and 0 is the most common value. | 4 | |
| 2026-11-17 | Fill missing `country` with "Unknown" | Kept as its own label. `country` is no longer a model input. | 488 | |
| 2026-11-17 | Fill missing `agent` and `company` with 0 | An empty cell means "booked without one", which is a category, not a gap (`docs/DOMAIN.md`). | 16,340 (`agent`), 112,593 (`company`) | |

## Which team decisions and objections did we log?

**Owner:** whoever made the decision. An objection is three lines: what I object to, why, what I propose.

| Date | Artifact | Decision or objection | Raised by | Answer, within 15 minutes | Settled by |
|---|---|---|---|---|---|
| 2026-11-17 | notebooks/03_model_logistic_regression.ipynb | Logistic regression: C = 0.01334. Chosen from 19 trials of C (0.0001 to 100) on train only, 3 forward-in-time folds, scored by log loss. Rule: lowest log loss. Cross-validated log loss 0.4065 against 0.4419 for the default C = 1. | | | |
| 2026-11-17 | src/features.py, docs/COLUMNS.md | Move `country` and `adr` from bin 1 to bin 2; the model now reads 14 columns. `country`: inside Groups and Offline TA/TO, 95–97% of cancelled bookings are PRT against 27–31% of stays, which fits a default corrected at check-in. `adr`: built from lodging transactions during the stay. On the choose period the forest's AUC fell from 0.843 to 0.792 and its cost rose by EUR 177k, and it still beats the lookup table. **These columns were changed after the team had seen proof-period results, so slide 5 reports both runs.** | | | |
| 2026-11-17 | src/features.py | Keep `adults`, `children` and `babies` in bin 1 with a caveat. They can be amended, but removing them raised the choose-period cost by EUR 22k. | | | |
| 2026-11-17 | src/features.py | Remove `arrival_month`, `arrival_weekday`, `is_agent` and `is_company` from `add_features`. No model read them, and arrival month and weekday made the forest EUR 305k worse on the choose period, because train holds only one year of each month. | | | |
| 2026-11-17 | notebooks/04, notebooks/05 | Point both notebooks at `src/features.py`. They read `notes/features_simple.py`, which still listed `country` and `adr`, so the tree and the forest had been tuned on a different feature list from the one `backtest.py` trains. | | | |
| 2026-11-17 | models/hyperparams.json | Re-tuned all three models on the 14 columns, train only, 3 forward-in-time folds, lowest log loss. Logistic regression: C from 0.0133 to 0.0316. Decision tree: depth 6, leaf 200, entropy to depth 3, leaf 10, gini. Random forest: 300 trees, depth 14, leaf 2, max_features 0.2 to 500 trees, depth 12, leaf 3, max_features 0.3 (101 trials, log loss 0.3924). | | | |
| 2026-11-17 | src/backtest.py, models/chosen.joblib | Ran the proof period once with the 14 columns. Random forest won on the choose period (EUR 1,193,673, z = 0.9). On proof: EUR 2,040,111, 62 walked guests, 2.49 walks per 1,000; EUR 1,894,131 below the flat rule. The 16-column run is kept in `evidence/backtest_before_feature_change.txt`, and both runs go on slide 5. | | | |
