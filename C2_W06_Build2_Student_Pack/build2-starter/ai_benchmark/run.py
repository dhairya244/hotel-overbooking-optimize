"""Cancellation-aware overbooking: the approved plan, end to end.

Run from build2-starter:  python ai_benchmark/run.py
Prints choose- and proof-period results and writes ai_benchmark/oversell_table_2017-08-18_to_31.csv.
Uses src/contract.py unchanged for every score.
"""
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import contract  # noqa: E402
import data  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent
TABLE_PATH = OUT / "oversell_table_2017-08-18_to_31.csv"
CEILING = contract.WALK_CEILING  # approved: the contract's 10 per 1,000, no tighter internal target
# Cancellations are correlated (group blocks), so the independence spread understates the risk and
# the buffer must reach well beyond 2-3 spreads; the grid runs to 20.
Z_GRID = np.round(np.arange(0.0, 20.0001, 0.1), 1)
M_GRID = np.arange(0, 41)
RARE_MIN = 50  # agent/company IDs seen fewer times than this in the fit data become "other"

NUM = ["lead_time", "arrival_date_week_number", "stays_in_weekend_nights", "stays_in_week_nights",
       "adults", "children", "babies", "is_repeated_guest", "previous_cancellations",
       "previous_bookings_not_canceled", "adr", "total_of_special_requests"]
CAT = ["hotel", "arrival_month", "arrival_dow", "meal", "reserved_room_type", "market_segment",
       "distribution_channel", "customer_type", "deposit_type", "agent_g", "company_g"]
# Excluded as leakage (see plan): reservation_status, reservation_status_date, assigned_room_type,
# booking_changes, days_in_waiting_list, country, required_car_parking_spaces (0% cancellation
# among 7,416 bookings with parking: recorded at arrival). arrival_date_year never used.


# ---------------------------------------------------------------- data and scored set
def load():
    df = data.read_raw(ROOT / "data" / data.FILE)
    df["arrival_date"] = data.arrival_date(df)
    df["nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["children"] = df["children"].fillna(0)
    log = [("raw rows", len(df))]
    rules = [
        ("0-night stays", df["nights"] == 0),
        ("negative adr", df["adr"] < 0),
        ("extreme adr (> 1,000)", df["adr"] > 1000),
        ("no guests", (df["adults"] + df["children"] + df["babies"]) == 0),
    ]
    drop = pd.Series(False, index=df.index)
    for name, mask in rules:
        log.append((f"dropped: {name}", int((mask & ~drop).sum())))
        drop |= mask
    df = df[~drop].reset_index(drop=True)
    log.append(("scored rows", len(df)))
    df["arrival_month"] = df["arrival_date_month"]
    df["arrival_dow"] = df["arrival_date"].dt.day_name()
    return df, log


def group_ids(fit, other):
    """Group rare agent/company IDs using the fit data only."""
    out = []
    for col in ["agent", "company"]:
        s = fit[col].fillna(-1).astype(int).astype(str).replace("-1", "none")
        keep = set(s.value_counts()[lambda v: v >= RARE_MIN].index)
        out.append((col, keep))
    res = []
    for frame in [fit] + other:
        f = frame.copy()
        for col, keep in out:
            s = f[col].fillna(-1).astype(int).astype(str).replace("-1", "none")
            f[col + "_g"] = s.where(s.isin(keep), "other")
        res.append(f)
    return res


# ---------------------------------------------------------------- models
def make_model(kind, num):
    if kind == "logit":
        pre = ColumnTransformer([("n", StandardScaler(), num),
                                 ("c", OneHotEncoder(handle_unknown="ignore", min_frequency=20), CAT)])
        return make_pipeline(pre, LogisticRegression(C=0.5, max_iter=3000))
    pre = ColumnTransformer([("n", "passthrough", num),
                             ("c", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                                  encoded_missing_value=-1), CAT)])
    return make_pipeline(pre, HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=40,
        categorical_features=list(range(len(num), len(num) + len(CAT))), random_state=0))


class Fitted:
    """Model fitted on the earlier part of its window, isotonic-calibrated on the last 3 months."""

    def __init__(self, kind, num, fit_df, calib_start):
        self.kind, self.num = kind, num
        a = fit_df[fit_df["arrival_date"] < calib_start]
        b = fit_df[fit_df["arrival_date"] >= calib_start]
        a, b = group_ids(a, [b])
        self.ref = a
        self.model = make_model(kind, num).fit(a[num + CAT], a["is_canceled"])
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
            self.model.predict_proba(b[num + CAT])[:, 1], b["is_canceled"])

    def predict(self, df):
        (_, d) = group_ids(self.ref, [df])
        raw = self.model.predict_proba(d[self.num + CAT])[:, 1]
        return np.clip(self.iso.predict(raw), 0.0, 1.0)


def segment_rates(fit, df):
    keys = ["hotel", "deposit_type", "market_segment"]
    r = fit.groupby(keys)["is_canceled"].mean().rename("r")
    hotel_r = fit.groupby("hotel")["is_canceled"].mean()
    p = df.join(r, on=keys)["r"]
    return p.fillna(df["hotel"].map(hotel_r)).to_numpy()


# ---------------------------------------------------------------- rules
def k_model(nights, z):
    zz = np.asarray(nights.index.get_level_values("hotel").map(z), dtype=float)
    return np.maximum(0, np.floor(nights["expected"] - zz * nights["spread"])).to_numpy()


def k_flat(nights, rate, m):
    h = nights.index.get_level_values("hotel")
    rr = np.asarray(h.map(rate), dtype=float)
    mm = np.asarray(h.map(m), dtype=float)
    return np.maximum(0, np.floor(rr * nights["book"].to_numpy()) - mm)


def fast_score(nights, k):
    a = nights["cancelled"].to_numpy()
    empty = np.clip(a - k, 0, None)
    walks = np.clip(k - a, 0, None)
    return (empty * nights["stay_value"].to_numpy()).sum() + 300.0 * walks.sum(), walks


def pick(nights, grid, kfun):
    """Choose a shared or per-hotel setting: lowest choose cost with walks/1000 <= ceiling.
    Ties (within EUR 1) go to the shared setting (fewer parameters)."""
    hotels = list(nights.index.get_level_values("hotel").unique())
    arrivals = (nights["book"] - nights["cancelled"]).sum()
    hmask = {h: (nights.index.get_level_values("hotel") == h) for h in hotels}
    per = {}  # per hotel: grid value -> (cost, walks) on that hotel's nights
    for g in grid:
        k = kfun({h: g for h in hotels})
        for h in hotels:
            c, w = fast_score(nights[hmask[h]], k[hmask[h]])
            per.setdefault(h, {})[g] = (c, w.sum())
    best_shared = None
    for g in grid:
        c = sum(per[h][g][0] for h in hotels)
        w = sum(per[h][g][1] for h in hotels)
        if 1000 * w / arrivals <= CEILING and (best_shared is None or c < best_shared[0]):
            best_shared = (c, {h: g for h in hotels})
    best_joint = None
    h1, h2 = hotels
    for g1 in grid:
        for g2 in grid:
            c = per[h1][g1][0] + per[h2][g2][0]
            w = per[h1][g1][1] + per[h2][g2][1]
            if 1000 * w / arrivals <= CEILING and (best_joint is None or c < best_joint[0]):
                best_joint = (c, {h1: g1, h2: g2})
    if best_joint is None:
        raise RuntimeError("no setting on the grid meets the walk ceiling on choose; widen the grid")
    if best_shared is None or best_joint[0] < best_shared[0] - 1.0:
        return best_joint[1], "per hotel"
    return best_shared[1], "shared"


# ---------------------------------------------------------------- reporting helpers
def by_hotel(nights, k, label):
    rows = []
    k = pd.Series(k, index=nights.index)
    for h in list(nights.index.get_level_values("hotel").unique()) + ["Total"]:
        sel = nights if h == "Total" else nights.xs(h, level="hotel", drop_level=False)
        r = contract.night_cost(sel, k.loc[sel.index])
        rows.append({"rule": label, "hotel": h, **r})
    return rows


def fmt(rows):
    t = pd.DataFrame(rows)
    t["cost_eur"] = t["cost_eur"].map(lambda v: f"{v:,.0f}")
    return t[["rule", "hotel", "cost_eur", "empty_rooms", "walked_guests", "walks_per_1000",
              "ceiling_met", "nights"]].to_string(index=False)


def model_metrics(name, df, p):
    nt = contract.nightly_table(df, p)
    err = nt["expected"] - nt["cancelled"]
    return {"model": name, "log_loss": round(log_loss(df["is_canceled"], p), 4),
            "brier": round(brier_score_loss(df["is_canceled"], p), 4),
            "night_mean_err": round(err.mean(), 2), "night_MAE": round(err.abs().mean(), 2)}


# ---------------------------------------------------------------- main
def main():
    pd.set_option("display.width", 160)
    df, log = load()
    train, choose, proof = contract.split_periods(df)
    print("=== Scored set ===")
    for name, n in log:
        print(f"  {name:<28}{n:>8,}")
    print(f"  train {len(train):,} | choose {len(choose):,} | proof {len(proof):,}")

    print("\n=== Non Refund bookings (train): cancellation rate ===")
    print(train.groupby(["hotel", "deposit_type"])["is_canceled"].agg(rate="mean", bookings="size")
          .round(3).to_string())

    # ---- model selection on choose (fit on train: Jul 2015-Mar 2016, calibrate Apr-Jun 2016)
    num_full = NUM
    num_nospec = [c for c in NUM if c != "total_of_special_requests"]
    cands = {}
    for kind in ["logit", "hgb"]:
        for tag, num in [("all", num_full), ("no_special_requests", num_nospec)]:
            cands[f"{kind}/{tag}"] = Fitted(kind, num, train, "2016-04-01")
    seg_choose = segment_rates(train, choose)
    flat_rate = train.groupby("hotel")["is_canceled"].mean().to_dict()

    print("\n=== Choose period: model calibration (accuracy deliberately not reported) ===")
    metrics, probs = [], {}
    for name, f in cands.items():
        probs[name] = f.predict(choose)
        metrics.append(model_metrics(name, choose, probs[name]))
    probs["segment_rate"] = seg_choose
    metrics.append(model_metrics("segment_rate", choose, seg_choose))
    print(pd.DataFrame(metrics).to_string(index=False))

    # ---- buffer selection on choose for every candidate, and for the flat rule
    print("\n=== Choose period: each rule at its chosen buffer (ceiling 10 per 1,000) ===")
    choose_rows, chosen = [], {}
    base_nights = contract.nightly_table(choose, np.zeros(len(choose)))
    m, mstruct = pick(base_nights, M_GRID, lambda mm: k_flat(base_nights, flat_rate, mm))
    choose_rows += by_hotel(base_nights, k_flat(base_nights, flat_rate, m), f"flat m={m} ({mstruct})")
    flat_choose_cost = contract.night_cost(base_nights, k_flat(base_nights, flat_rate, m))["cost_eur"]
    for name, p in probs.items():
        nt = contract.nightly_table(choose, p)
        z, zstruct = pick(nt, Z_GRID, lambda zz: k_model(nt, zz))
        r = contract.night_cost(nt, k_model(nt, z))
        chosen[name] = (z, zstruct, r["cost_eur"])
        choose_rows += [x for x in by_hotel(nt, k_model(nt, z), f"{name} z={z} ({zstruct})")
                        if x["hotel"] == "Total"]
    print(fmt(choose_rows))

    best = min((n for n in chosen if n != "segment_rate"), key=lambda n: chosen[n][2])
    z_best, zstruct, _ = chosen[best]
    print(f"\nSelected on choose: {best}, buffer z={z_best} ({zstruct}); "
          f"flat rule margin m={m} ({mstruct}). Flat choose cost EUR {flat_choose_cost:,.0f}.")

    # ---- freeze settings, refit on train+choose, run proof once
    kind, tag = best.split("/")
    num = num_full if tag == "all" else num_nospec
    fit_all = pd.concat([train, choose])
    final = Fitted(kind, num, fit_all, "2016-10-01")
    flat_rate_all = fit_all.groupby("hotel")["is_canceled"].mean().to_dict()
    p_proof = final.predict(proof)
    seg_proof = segment_rates(fit_all, proof)
    seg_z = chosen["segment_rate"][0]

    nt = contract.nightly_table(proof, p_proof)
    nt_seg = contract.nightly_table(proof, seg_proof)
    k_ours = k_model(nt, z_best)
    k_fl = k_flat(nt, flat_rate_all, m)
    rows = []
    rows += by_hotel(nt, k_fl, "Flat rule (client)")
    rows += by_hotel(nt, k_ours, f"Model rule ({best})")
    rows += by_hotel(nt_seg, k_model(nt_seg, seg_z), "Segment-rate rule")
    rows += by_hotel(nt, np.zeros(len(nt)), "Oversell nothing")
    rows += by_hotel(nt, nt["cancelled"].to_numpy(), "Perfect foresight (unattainable)")

    print("\n" + "=" * 100)
    print("PROOF PERIOD: arrivals 1 Jan - 31 Aug 2017 (run once; settings frozen from choose)")
    print("=" * 100)
    print(f"Flat rate (train+choose): " + ", ".join(f"{h} {r:.3f}" for h, r in flat_rate_all.items()))
    print(fmt(rows))
    print("\nModel calibration on proof:")
    print(pd.DataFrame([model_metrics(best, proof, p_proof),
                        model_metrics("segment_rate", proof, seg_proof)]).to_string(index=False))

    fl = contract.night_cost(nt, k_fl)
    ou = contract.night_cost(nt, k_ours)
    print("\nSaving against the flat rule (proof):")
    print(f"  EUR {fl['cost_eur'] - ou['cost_eur']:,.0f}  "
          f"({100 * (fl['cost_eur'] - ou['cost_eur']) / fl['cost_eur']:.1f}% of flat-rule cost)")
    print(f"  empty rooms {fl['empty_rooms']:,} -> {ou['empty_rooms']:,} "
          f"({fl['empty_rooms'] - ou['empty_rooms']:+,} fewer)")
    print(f"  walked guests {fl['walked_guests']:,} -> {ou['walked_guests']:,}; "
          f"walks per 1,000 {fl['walks_per_1000']} -> {ou['walks_per_1000']} (ceiling {CEILING:g})")

    print("\nWalks per 1,000 by month (proof):")
    month = nt.index.get_level_values("arrival_date").to_period("M")
    mrows = []
    for mo in month.unique():
        sel = month == mo
        a = contract.night_cost(nt[sel], k_fl[sel])
        b = contract.night_cost(nt[sel], k_ours[sel])
        mrows.append({"month": str(mo), "flat_walks_per_1000": a["walks_per_1000"],
                      "model_walks_per_1000": b["walks_per_1000"],
                      "flat_cost_eur": round(a["cost_eur"]), "model_cost_eur": round(b["cost_eur"])})
    print(pd.DataFrame(mrows).to_string(index=False))

    # ---- morning table: the last 14 arrival nights, final book treated as known
    days = (nt.index.get_level_values("arrival_date") >= "2017-08-18") & \
           (nt.index.get_level_values("arrival_date") <= "2017-08-31")
    t = nt[days].reset_index()
    zz = t["hotel"].map(z_best).astype(float)
    table = pd.DataFrame({
        "hotel": t["hotel"],
        "night": t["arrival_date"].dt.date,
        "bookings_on_book": t["book"],
        "expected_cancellations": t["expected"].round(1),
        "buffer_rooms": (zz * t["spread"]).round(1),
        "oversell_rooms": k_ours[days].astype(int),
        "flat_rule_oversell": k_fl[days].astype(int),
        "stay_value_eur": t["stay_value"].round(0),
    }).sort_values(["hotel", "night"])
    table.to_csv(TABLE_PATH, index=False)
    print(f"\nOversell table, 18-31 Aug 2017 ({len(table)} rows; final book treated as known):")
    print(table.to_string(index=False))
    print(f"\nWrote {TABLE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
