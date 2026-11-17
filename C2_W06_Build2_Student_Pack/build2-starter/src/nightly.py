# nightly.py
# Writes the how many extra rooms to sell table for the next nights.

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # sibling modules

import joblib
import pandas as pd

import contract
import data_loader
import features
import k_calculator
import all_models

HERE = pathlib.Path(__file__).resolve().parent
MODEL_FILE = HERE.parent / "models" / "chosen.joblib"
OUTPUT_FOLDER = HERE.parent / "outputs"


def main():
    # STEP 1. Read what was typed:  --from 2017-08-18 --nights 14
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start", required=True, help="first night, like 2017-08-18")
    parser.add_argument("--nights", type=int, default=14, help="how many nights to cover")
    args = parser.parse_args()

    start_date = pd.Timestamp(args.start)
    end_date = start_date + pd.Timedelta(days=args.nights)     # the day AFTER the last night

    # STEP 2. Load the winner that backtest.py saved
    saved = joblib.load(MODEL_FILE)
    model = saved["model"]
    buffer = saved["buffer"]

    # STEP 3. Load the bookings and keep the ones arriving on those nights
    all_bookings = data_loader.load_bookings()
    bookings = data_loader.get_bookings_between(all_bookings, start_date, end_date)
    if len(bookings) == 0:
        raise SystemExit("No bookings arrive between " + str(start_date.date()) + " and " + str(end_date.date()))

    # STEP 4. Build the clue columns (rare countries are grouped inside the saved model's encoder)
    bookings = features.add_features(bookings)

    # STEP 5. A chance of cancelling for every booking, then add them up per night
    chances = all_models.predict_chances(model, bookings)
    nights = contract.nightly_table(bookings, chances)
    # (nightly_table needs the is_canceled column to build its table,
    #  but the number of rooms to sell below never uses it)

    # STEP 6. k = expected cancellations - buffer x spread
    nights["oversell"] = k_calculator.calculate_k(nights, buffer)

    # STEP 7. Keep the columns the revenue manager needs, and save them
    # buffer = the rooms we hold back from the expected cancellations (what the revenue manager can see)
    nights["buffer"] = nights["expected"] - nights["oversell"]

    table = nights.reset_index()
    table = table[["hotel", "arrival_date", "book", "expected", "buffer", "oversell"]]
    table.columns = ["hotel", "night", "bookings", "expected_cancellations", "buffer_rooms", "oversell"]
    table["expected_cancellations"] = table["expected_cancellations"].round(1)
    table["buffer_rooms"] = table["buffer_rooms"].round(1)

    OUTPUT_FOLDER.mkdir(exist_ok=True)
    file_path = OUTPUT_FOLDER / ("oversell_" + str(start_date.date()) + "_" + str(args.nights) + "n.csv")
    table.to_csv(file_path, index=False)

    print("Method used:", saved["method_name"], "| buffer z =", buffer)
    print("Saved", len(table), "rows to", file_path)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
