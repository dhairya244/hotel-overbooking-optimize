# Three models: Logistic Regression, Decision Tree, Random Forest.
# Each one learns from the train bookings, then gives every booking a chance (0 to 1) of cancelling.
#
# The hyper-parameters are tested in notebooks 03 / 04 / 05 (time-ordered cross-validation on TRAIN only).
# A notebook saves its best settings with save_hyperparams(); the train_* functions below load them with
# load_hyperparams(). If nothing has been saved yet, the model's built-in defaults are used.

import json
import pathlib

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

import features
from features import make_preparer    # the encoding lives in features.py

# One small file, committed with models/. Names start with "model__" = the step called "model" in the pipeline.
# Example: {"logistic regression": {"model__C": 0.3}, "decision tree": {"model__max_depth": 8, ...}}
HYPERPARAMS_FILE = pathlib.Path(__file__).resolve().parent.parent / "models" / "hyperparams.json"


def load_hyperparams(model_name):
    """The settings the notebook chose for this model ('logistic regression', 'decision tree' or
       'random forest'), or {} if none were saved yet."""
    if not HYPERPARAMS_FILE.exists():
        return {}
    return json.loads(HYPERPARAMS_FILE.read_text()).get(model_name, {})


def save_hyperparams(model_name, params):
    """Called by a notebook after tuning: store the best settings for this model, keep the others."""
    saved = json.loads(HYPERPARAMS_FILE.read_text()) if HYPERPARAMS_FILE.exists() else {}
    saved[model_name] = params
    HYPERPARAMS_FILE.parent.mkdir(exist_ok=True)
    HYPERPARAMS_FILE.write_text(json.dumps(saved, indent=2, default=lambda v: v.item() if hasattr(v, "item") else str(v)))


class LookupTable:
    """Baseline: the cancellation rate of past bookings in the same cell of a small table.
       Cell = hotel x deposit type x lead-time band (all Bin 1 columns, so known on the day of booking).
       Rates are learned on TRAIN only. A cell with fewer than MIN_CELL bookings falls back to the
       rate of its hotel x deposit type; a cell never seen in train falls back to the overall rate.
       It has fit / predict_proba like a scikit-learn model, so the rest of the code treats it the same."""

    LEAD_BANDS = [-1, 7, 30, 90, 180, float("inf")]     # days: 0-7, 8-30, 31-90, 91-180, 181+
    MIN_CELL = 30

    def _cells(self, X):
        band = pd.cut(X["lead_time"], bins=self.LEAD_BANDS, labels=False)
        return pd.DataFrame({"hotel": X["hotel"].astype(str).values,
                             "deposit": X["deposit_type"].astype(str).values,
                             "band": band.values}, index=X.index)

    def fit(self, X, y):
        cells = self._cells(X)
        y = pd.Series(y.values, index=cells.index)
        self.overall_ = float(y.mean())
        parent = y.groupby([cells["hotel"], cells["deposit"]])
        self.parent_ = parent.mean().to_dict()
        cell = y.groupby([cells["hotel"], cells["deposit"], cells["band"]]).agg(["mean", "size"])
        self.cell_ = cell[cell["size"] >= self.MIN_CELL]["mean"].to_dict()
        return self

    def predict_proba(self, X):
        cells = self._cells(X)
        p = []
        for hotel, deposit, band in zip(cells["hotel"], cells["deposit"], cells["band"]):
            rate = self.cell_.get((hotel, deposit, band))
            if rate is None:
                rate = self.parent_.get((hotel, deposit), self.overall_)
            p.append(rate)
        p = np.clip(np.array(p, dtype=float), 0.0, 1.0)
        return np.column_stack([1 - p, p])


def train_lookup(train):
    return LookupTable().fit(train[features.bin1_features], train["is_canceled"])


def train_logistic(train):
    model = Pipeline([
        ("prepare", make_preparer(scale_numbers=True)),
        ("model", LogisticRegression(max_iter=1000)),
    ])
    model.set_params(**load_hyperparams("logistic regression"))
    model.fit(train[features.bin1_features], train["is_canceled"])
    return model


def train_tree(train):
    model = Pipeline([
        ("prepare", make_preparer(scale_numbers=False)),
        ("model", DecisionTreeClassifier(max_depth=6, min_samples_leaf=100, random_state=0)),
    ])
    model.set_params(**load_hyperparams("decision tree"))
    model.fit(train[features.bin1_features], train["is_canceled"])
    return model


def train_forest(train):
    model = Pipeline([
        ("prepare", make_preparer(scale_numbers=False)),
        ("model", RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=10,
                                         n_jobs=-1, random_state=0)),
    ])
    model.set_params(**load_hyperparams("random forest"))
    model.fit(train[features.bin1_features], train["is_canceled"])
    return model


def predict_chances(model, df):
    clues = df[features.bin1_features]
    both_columns = model.predict_proba(clues)    # column 0 = chance of staying, column 1 = chance of cancelling
    return both_columns[:, 1]


def get_scores(df, chances):
    answers = df["is_canceled"]
    guesses = (chances >= 0.5).astype(int)

    true_stays, false_cancels, missed_cancels, true_cancels = confusion_matrix(answers, guesses).ravel()

    return {
        "accuracy": accuracy_score(answers, guesses),    # share of bookings guessed right
        "always_stays": 1 - answers.mean(),              # accuracy if we just said "nobody cancels"
        "auc": roc_auc_score(answers, chances),          # 0.5 = guessing, 1.0 = perfect
        "precision": precision_score(answers, guesses),  # of the bookings we said would cancel, how many did
        "recall": recall_score(answers, guesses),        # of the bookings that cancelled, how many we caught
        "f1": f1_score(answers, guesses),                # one number mixing precision and recall
        "true_stays": true_stays,
        "false_cancels": false_cancels,
        "missed_cancels": missed_cancels,
        "true_cancels": true_cancels,
    }
