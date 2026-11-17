# slide_numbers.py
# Prints the numbers for slides 3 and 6, plus a few the panel may ask about.
# It reads the data and the saved model in models/. It trains nothing and chooses nothing.
#
#   python src/slide_numbers.py > evidence/slide_numbers_output.txt

import pathlib

import joblib
import pandas as pd

import data
import contract
import features
import data_loader
import all_models
import k_calculator

HERE = pathlib.Path(__file__).resolve().parent
MODEL_FILE = HERE.parent / "models" / "chosen.joblib"
pd.set_option("display.width", 200)


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


raw = data.read_raw()
clean = features.clean_bookings(raw)

# ---------------------------------------------------------------- slide 3
section("SLIDE 3: checking the brief's numbers")
print(f"rows {len(raw):,} | columns {raw.shape[1]} | after cleaning {len(clean):,} (dropped {len(raw) - len(clean):,})")
print(f"cancel rate overall {raw.is_canceled.mean():.3f}   (the brief says about 1 in 4 = 0.25)")
print(raw.groupby("hotel").is_canceled.agg(bookings="size", cancel_rate="mean").round(3))
print("arrivals from", clean.arrival_date.min().date(), "to", clean.arrival_date.max().date())

section("SLIDE 3: observation 1, do non-refundable bookings stay?")
print(raw.groupby("deposit_type").is_canceled.agg(bookings="size", cancel_rate="mean").round(3))
nr = raw[raw.deposit_type == "Non Refund"]
print(f"\nNon Refund: {len(nr):,} bookings, {nr.is_canceled.sum():,} cancelled")
print("\nNon Refund by market segment:")
print(nr.groupby("market_segment").is_canceled.agg(bookings="size", cancel_rate="mean")
        .round(3).sort_values("bookings", ascending=False).head(5))
print(f"\nshare from Portugal: cancelled {(nr[nr.is_canceled == 1].country == 'PRT').mean():.3f}"
      f" | stayed {(nr[nr.is_canceled == 0].country == 'PRT').mean():.3f}")

section("SLIDE 3: travel-partner view, rate against volume")
stays = raw[raw.is_canceled == 0]
seg = raw.groupby("market_segment").agg(bookings=("is_canceled", "size"), cancel_rate=("is_canceled", "mean"))
seg["share_of_bookings"] = seg.bookings / seg.bookings.sum()
seg["avg_rate_of_stays_eur"] = stays.groupby("market_segment").adr.mean()
print(seg.sort_values("bookings", ascending=False)[["bookings", "share_of_bookings", "cancel_rate", "avg_rate_of_stays_eur"]].round(3).to_string())

# ---------------------------------------------------------------- observation 3
train, choose, proof = data_loader.get_ready_data()
section("OBSERVATION 3: what accuracy does guessing 'nobody cancels' get?")
print(f"accuracy on the proof period: {1 - proof.is_canceled.mean():.3f}")

# ---------------------------------------------------------------- slide 6
saved = joblib.load(MODEL_FILE)
section(f"SLIDE 6: buffer against walks on the CHOOSE period ({saved['method_name']}, chosen z = {saved['buffer']})")
nights = contract.nightly_table(choose, all_models.predict_chances(saved["model"], choose))
rows = []
for z in [0, 0.3, 0.6, 0.9, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0]:
    r = contract.night_cost(nights, k_calculator.calculate_k(nights, z))
    rows.append(dict(z=z, rooms_held_back=round(k_calculator.avg_rooms_held_back(nights, z), 1),
                     cost_eur=r["cost_eur"], empty_rooms=r["empty_rooms"], walked=r["walked_guests"],
                     walks_per_1000=r["walks_per_1000"], ceiling_met=r["ceiling_met"]))
print(pd.DataFrame(rows).to_string(index=False))

section("SLIDE 6: one changed condition (z picked again on the CHOOSE period)")
# contract.py is not edited; the two constants are changed in memory for this what-if only
for label, walk_cost, ceiling in [("as in the brief", 300, 10), ("a walk costs EUR 1,000", 1000, 10), ("ceiling 5 per 1,000", 300, 5)]:
    contract.WALK_COST, contract.WALK_CEILING = float(walk_cost), float(ceiling)
    z, r = k_calculator.find_best_buffer(nights)
    print(f"{label:24s} -> z {z} | rooms held back {k_calculator.avg_rooms_held_back(nights, z):.1f}"
          f" | cost EUR {r['cost_eur']:,.0f} | walks per 1,000 {r['walks_per_1000']}")
contract.WALK_COST, contract.WALK_CEILING = 300.0, 10.0

# ---------------------------------------------------------------- panel question: January
section(f"PANEL Q, January: the proof run by month (z fixed at {saved['buffer']}, nothing re-chosen)")
pn = contract.nightly_table(proof, all_models.predict_chances(saved["model"], proof))
pn["k"] = k_calculator.calculate_k(pn, saved["buffer"])
pn = pn.reset_index()
pn["month"] = pd.to_datetime(pn.arrival_date).dt.strftime("%Y-%m")
out = []
for month, g in pn.groupby("month"):
    r = contract.night_cost(g.set_index(["hotel", "arrival_date"]), g.k.values)
    out.append(dict(month=month, avg_bookings_per_night=round(g.book.mean(), 1),
                    cancel_rate=round(g.cancelled.sum() / g.book.sum(), 3),
                    oversell_per_night=round(g.k.mean(), 1),
                    walks_per_1000=r["walks_per_1000"], cost_eur=round(r["cost_eur"])))
print(pd.DataFrame(out).to_string(index=False))
