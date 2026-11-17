# late_columns.py
# The experiment asked for in docs/COLUMNS.md: what happens to ONE method when late columns go in?
# Same method (logistic regression, the settings saved by notebook 03), three runs, AUC on the proof period:
#   Run A  Bin 1 only, time split      <- what we ship
#   Run B  Bins 1+2+3, time split      <- shows the leak
#   Run C  Bin 1 only, random split    <- shows what a random split does to the number
# Only AUC is computed. No euros, no buffer, no setting is chosen or changed from these numbers.
# Run once:  python src/late_columns.py      (writes evidence/late_columns_auc.csv)

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # sibling modules

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import all_models
import data_loader
import features

EVIDENCE = pathlib.Path(__file__).resolve().parent.parent / "evidence"
SEED = 0


def as_text(df, columns):
    """The late columns are not made text by features.add_features, so do it here, the same way."""
    df = df.copy()
    for c in columns:
        if df[c].dtype == object or c in features.bin1_categorical_cols or c == "arrival_date_month":
            df[c] = df[c].astype(str)
    df["reservation_status_date"] = df["reservation_status_date"].astype(str)
    return df


def fit_and_score(train, test, columns):
    """Fit logistic regression on train and return the AUC on test. Same settings in every run."""
    numeric = [c for c in columns if pd.api.types.is_numeric_dtype(train[c])]
    text = [c for c in columns if c not in numeric]
    model = Pipeline([
        ("prepare", ColumnTransformer([
            ("text", OneHotEncoder(handle_unknown="ignore", min_frequency=20), text),
            ("numbers", StandardScaler(), numeric),
        ])),
        ("model", LogisticRegression(max_iter=2000)),
    ])
    model.set_params(**all_models.load_hyperparams("logistic regression"))
    model.fit(train[columns], train["is_canceled"])
    return roc_auc_score(test["is_canceled"], model.predict_proba(test[columns])[:, 1])


def main():
    train, choose, proof = data_loader.get_ready_data()
    all_columns = features.bin1_features + features.bin2_features + features.bin3_features
    # a late column is numeric or text; fix the types once for every column we may use
    train, choose, proof = (as_text(d, all_columns) for d in (train, choose, proof))
    # the contract lets us refit on train + choose before the proof run, so every run does the same
    fit_time = pd.concat([train, choose])

    auc_a = fit_and_score(fit_time, proof, features.bin1_features)
    auc_b = fit_and_score(fit_time, proof, all_columns)

    # Run C: same bookings, same three sizes, but rows are shuffled, so the test rows sit next to training rows in time
    everything = pd.concat([train, choose, proof]).sample(frac=1.0, random_state=SEED)
    n_fit, n_test = len(fit_time), len(proof)
    rand_fit, rand_test = everything.iloc[:n_fit], everything.iloc[n_fit:n_fit + n_test]
    auc_c = fit_and_score(rand_fit, rand_test, features.bin1_features)

    table = pd.DataFrame([
        {"run": "A", "columns": "First bin only", "split": "Time", "auc_on_proof": round(auc_a, 3)},
        {"run": "B", "columns": "All three bins", "split": "Time", "auc_on_proof": round(auc_b, 3)},
        {"run": "C", "columns": "First bin only", "split": "Random", "auc_on_proof": round(auc_c, 3)},
    ])
    print(table.to_string(index=False))
    EVIDENCE.mkdir(exist_ok=True)
    table.to_csv(EVIDENCE / "late_columns_auc.csv", index=False)
    print("Saved to evidence/late_columns_auc.csv")


if __name__ == "__main__":
    main()
