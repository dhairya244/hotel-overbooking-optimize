# What did we decide, and why?

Two tables. The first is the Week 1 decisions log for the data: every cleaning or filtering choice, its reason and how many rows it touched. The second records team decisions and objections under the rule in `docs/ROLES.md`. Add rows; never delete them.

## Which data decisions did we make?

**Owner:** Data Lead.

| Date | Decision | Reason, with the number that justified it | Rows touched | Logged by |
|---|---|---|---|---|
| | | | | |

## Which team decisions and objections did we log?

**Owner:** whoever made the decision. An objection is three lines: what I object to, why, what I propose.

| Date | Artifact | Decision or objection | Raised by | Answer, within 15 minutes | Settled by |
|---|---|---|---|---|---|
| 2026-11-17 | notebooks/03_model_logistic_regression.ipynb | Logistic regression: C = 0.01334. Chosen from 19 trials of C (0.0001 to 100) on train only, 3 forward-in-time folds, scored by log loss. Rule: lowest log loss. Cross-validated log loss 0.4065 against 0.4419 for the default C = 1. | | | |
