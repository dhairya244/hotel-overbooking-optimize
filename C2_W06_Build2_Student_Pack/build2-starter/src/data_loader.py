# data_loader.py
# Loads the bookings, splits them by time, and hands back data that is ready for the models.

import pathlib
import sys

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"    # data.py and features.py live in src/
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import data              # the starter's data.py
import contract          # the starter's scoring file (we do not change it)
import features


def load_bookings():
    raw = data.read_raw()
    df = features.clean_bookings(raw)
    return df


def split_by_time(df):
    """Cut the bookings into three periods by arrival date.
       train  = before 1 July 2016   (the models learn from this)
       choose = July to December 2016 (we pick the safety buffer on this)
       proof  = 2017                  (the final test, used once)"""
    train, choose, proof = contract.split_periods(df)
    return train, choose, proof


def get_ready_data():
    df = load_bookings()
    train, choose, proof = split_by_time(df)

    # nothing is learned here; encoders and scalers are fitted on TRAIN only, inside the models
    train = features.add_features(train)
    choose = features.add_features(choose)
    proof = features.add_features(proof)

    return train, choose, proof


def get_bookings_between(df, start_date, end_date):
    starts_ok = df["arrival_date"] >= start_date
    ends_ok = df["arrival_date"] < end_date
    return df[starts_ok & ends_ok]
