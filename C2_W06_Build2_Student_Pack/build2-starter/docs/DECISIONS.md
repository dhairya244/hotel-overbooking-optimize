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
| 2026-11-17 | src/features.py, docs/COLUMNS.md | Moved `country` and `adr` from bin 1 to bin 2, so the model now uses 14 columns. `country`: for Groups and Offline TA/TO, 95–97% of cancellations are PRT but only 27–31% of stays, which looks like a default that gets fixed at check-in. `adr`: it's worked out from what the guest pays during the stay. On the choose period the forest's AUC dropped from 0.843 to 0.792 and it cost EUR 177k more, but it still beats the lookup table. **We changed this after seeing proof results, so slide 5 shows both runs.** | Claude Code review | | |
| 2026-11-17 | src/features.py | Kept `adults`, `children` and `babies` in bin 1 with a caveat. Guests can change them, but dropping them cost EUR 22k on the choose period. The review suggested dropping them; we decided guest count matters. | Build Lead | | |
| 2026-11-17 | src/features.py | Removed `arrival_month`, `arrival_weekday`, `is_agent` and `is_company` from `add_features`. No model used them, and arrival month and weekday made the forest EUR 305k worse on the choose period (train only has one year of each month). | Claude Code review | | |
| 2026-11-17 | notebooks/04, notebooks/05 | Switched both notebooks to `src/features.py`. They were reading `notes/features_simple.py`, which still had `country` and `adr`, so the tree and forest were tuned on different columns from the ones `backtest.py` uses. | Claude Code review | | |
| 2026-11-17 | models/hyperparams.json | Re-tuned all three models on the 14 columns (train only, 3 folds in time order, lowest log loss). Logistic regression: C 0.0133 → 0.0316. Tree: depth 6, leaf 200, entropy → depth 3, leaf 10, gini. Forest: 300 trees, depth 14, leaf 2, max_features 0.2 → 500 trees, depth 12, leaf 3, max_features 0.3 (101 trials, log loss 0.3924). | | | |
| 2026-11-17 | src/backtest.py, models/chosen.joblib | Ran the proof period with the 14 columns. The random forest won on the choose period (EUR 1,193,673, z = 0.9). On proof it cost EUR 2,040,111, with 62 walked guests (2.49 per 1,000), which is EUR 1,894,131 less than the flat rule. The 16-column run is in `evidence/backtest_before_feature_change.txt`; both go on slide 5. | | | |
