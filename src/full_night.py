# full_night.py
# The full-night caveat. Every euro saving in the proof assumes a cancelled room is resold the same night.
# That only holds when the hotel is full. The data has no capacity column, so we use a stated proxy:
#
#   occupancy of a night   = non-cancelled bookings whose stay covers that night (one booking = one room)
#   capacity (proxy)       = the 99th percentile of that hotel's nightly occupancy over the whole file
#   near-full night        = occupancy >= NEAR_FULL (90%) of that capacity
#
# Weak points, stated so nobody has to find them: a booking can hold more than one room, the 99th percentile
# is not the true room count, and the 90% line is our choice. Nights before 1 Sep 2015 are left out because
# stays that began before the file starts are missing.
# Run:  python src/full_night.py      (writes evidence/full_night_share.csv)

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # sibling modules

import numpy as np
import pandas as pd

import contract
import data_loader

NEAR_FULL = 0.90
CAPACITY_PERCENTILE = 99
FIRST_RELIABLE_NIGHT = "2015-09-01"
EVIDENCE = pathlib.Path(__file__).resolve().parent.parent / "evidence"


def nightly_occupancy(df):
    """Rooms occupied on every night, per hotel, from the bookings that were not cancelled."""
    stays = df[(df["is_canceled"] == 0) & (df["nights"] > 0)]
    rows = []
    for hotel, group in stays.groupby("hotel"):
        start = group["arrival_date"].values.astype("datetime64[D]")
        end = start + group["nights"].to_numpy().astype("timedelta64[D]")    # check-out day, not occupied
        first, last = start.min(), end.max()
        days = np.arange(first, last, dtype="datetime64[D]")
        # +1 at arrival, -1 at check-out, running total = rooms occupied that night
        change = np.zeros(len(days) + 1)
        np.add.at(change, (start - first).astype(int), 1)
        np.add.at(change, (end - first).astype(int), -1)
        occupied = np.cumsum(change)[:-1]
        rows.append(pd.DataFrame({"hotel": hotel, "night": pd.to_datetime(days), "occupied": occupied}))
    return pd.concat(rows, ignore_index=True)


def main():
    df = data_loader.load_bookings()
    occ = nightly_occupancy(df)
    occ = occ[(occ["night"] >= FIRST_RELIABLE_NIGHT) & (occ["night"] <= df["arrival_date"].max())]

    capacity = occ.groupby("hotel")["occupied"].quantile(CAPACITY_PERCENTILE / 100)
    occ["capacity_proxy"] = occ["hotel"].map(capacity)
    occ["near_full"] = occ["occupied"] >= NEAR_FULL * occ["capacity_proxy"]

    def period(night):
        if night < pd.Timestamp(contract.TRAIN_END):
            return "train"
        return "choose" if night < pd.Timestamp(contract.PROOF_START) else "proof"

    occ["period"] = occ["night"].map(period)

    by_period = occ.groupby(["hotel", "period"]).agg(nights=("near_full", "size"),
                                                     near_full_nights=("near_full", "sum"),
                                                     share_near_full=("near_full", "mean")).reset_index()
    overall = occ.groupby("hotel").agg(nights=("near_full", "size"), near_full_nights=("near_full", "sum"),
                                       share_near_full=("near_full", "mean")).reset_index().assign(period="all")
    table = pd.concat([by_period, overall], ignore_index=True)
    table["capacity_proxy_rooms"] = table["hotel"].map(capacity).round(0).astype(int)
    table["share_near_full"] = table["share_near_full"].round(3)
    table = table[["hotel", "period", "nights", "near_full_nights", "share_near_full", "capacity_proxy_rooms"]]

    print(f"Near-full = occupancy >= {NEAR_FULL:.0%} of the {CAPACITY_PERCENTILE}th-percentile occupancy (capacity proxy)")
    print(table.to_string(index=False))
    EVIDENCE.mkdir(exist_ok=True)
    table.to_csv(EVIDENCE / "full_night_share.csv", index=False)
    print("Saved to evidence/full_night_share.csv")


if __name__ == "__main__":
    main()
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"