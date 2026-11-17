# Plan: cancellation-aware overbooking for the two hotels (for approval, no code yet)

_Saved word for word from the AI's plan-mode answer, before approval._

Sources I read: `BRIEF.md`, `docs/EVALUATION_CONTRACT.md`, `src/data.py`, `src/contract.py`, and only the header row of `data/hotels.csv` (119,390 rows, 32 columns, which matches `EXPECTED_ROWS`). I have not explored the data. Every row count below gets measured at build time and logged in `docs/DECISIONS.md`.

---

## 1. What we will predict

- **Unit of prediction:** one booking.
- **Target:** `is_canceled`, which is 1 for a cancellation or no-show. The output is a calibrated probability **p** that the booking cancels.
- **What the business number is built from:** the bookings are not scored one at a time. The p values are summed per hotel and arrival night by `nightly_table`, which gives `expected` (the sum of p) and `spread` (√Σp(1−p)). The oversell count *k* is built from those two numbers.
- **Consequence for how we judge the model:** we care about calibration, meaning the sum of p for a night should land close to the real number of cancellations. We do not care about accuracy or ranking.
  - This is why the other vendor's "95% accuracy" (brief item 3) did not help in practice.
  - It is also why we are not offering a list of the bookings most likely to cancel (brief item 2). The desk cannot act on a list. It can act on a nightly count.

## 2. Columns we will use, and why

Rule: a column is used only if its value is known **when the booking is made** (or while it sits on the book). It must not be filled in by the cancellation or by the guest arriving.

**Will use**

| Column(s) | Why |
|---|---|
| `hotel` | City and Resort behave differently. It also lets the model interact with the other columns. |
| `lead_time` | Strongest known signal: bookings made far ahead cancel more. |
| Arrival month and week (`arrival_date_month`, `arrival_date_week_number`), plus day of week derived from `data.arrival_date` | Seasonality. The year is **not** a feature, because it would not carry over to 2017. |
| `stays_in_weekend_nights`, `stays_in_week_nights` | Length of stay. |
| `adults`, `children`, `babies` | Party makeup. |
| `meal`, `reserved_room_type` | Product chosen at booking. |
| `market_segment`, `distribution_channel`, `customer_type` | Channel. Groups and OTA bookings behave very differently. |
| `deposit_type` | Kept, but flagged (see below). |
| `is_repeated_guest`, `previous_cancellations`, `previous_bookings_not_canceled` | Guest history at booking time. |
| `agent`, `company` | IDs, with rare values grouped into "other" using train data only. `NULL` is treated as its own category. |
| `adr` | Price paid. Known at booking. |
| `required_car_parking_spaces`, `total_of_special_requests` | Kept, but flagged as possible leakage (see below). |

**Excluded, because they leak the outcome**

- `reservation_status`: it *is* the outcome (Canceled / No-Show / Check-Out).
- `reservation_status_date`: it is the date of cancellation or check-out.
- `assigned_room_type`: assigned at check-in. A mismatch with the reserved room mostly means the guest arrived.
- `booking_changes` and `days_in_waiting_list`: their final values build up until arrival or cancellation, and the export gives no timestamp for them.
- `country`: in this dataset it is widely reported to be filled in or corrected at check-in. Cancelled bookings fall back to PRT far more often, so the column carries the outcome.

**Flagged, with a test before we keep them**

- `required_car_parking_spaces` and `total_of_special_requests` may also be recorded at arrival. Parking is almost never non-zero on cancelled bookings.
  - Test: on the choose period, compare the model with and without these two columns.
  - Decision rule: if the gain looks too good to be true, we drop them and say so.
- `deposit_type = Non Refund` (brief item 1, Finance's claim):
  - We will measure the cancellation rate for Non Refund bookings, by hotel and by segment, and report what we find rather than argue it.
  - This does not contradict "prepaid means guaranteed". The money is guaranteed, but the room is still empty. The contract values an empty room at *V* whatever the deposit.
  - These bookings are concentrated in a few agents and groups. That suggests block bookings released in bulk.
  - We keep the column, because it is known at booking. We will check that the model is not just learning one agent's behaviour and failing to carry it over.

**Not modelled:** `arrival_date_year`. `adr` and `nights` are also needed in their raw form by `nightly_table`, which computes *V* from them.

## 3. Which bookings we will score

The same scored set is used for our rule and for the flat rule, in every period. Each exclusion is logged with its reason and row count.

- **Keep exact duplicate rows.** They look like several identical rooms in one group booking. Each one is a room that can cancel.
- **Exclude stays of 0 nights.** These are day-use bookings that never take a room-night, and *V* would count them at 0.
- **Exclude the single negative `adr`** and the extreme `adr` outlier (a value in the thousands). Either one would distort a night's *V*.
- **Keep bookings with `adr` = 0** (complimentary rooms). They are real rooms.
- **Exclude bookings with 0 adults, 0 children and 0 babies.** They appear to be data errors.
- **No other filtering.** Including no-shows is required, since `is_canceled` already counts them.

If the client wants to score *every* row, we will run that as a sensitivity check and report it.

## 4. How we will split the data

We use the contract's periods unchanged, through `contract.split_periods` on `data.arrival_date`:

| Period | Arrival dates | What we do with it |
|---|---|---|
| Train | before 1 Jul 2016 | Fit the models, the flat rate, and the category groupings. Tune model hyperparameters with time-ordered folds **inside** train (for example, fit on Jul 2015–Mar 2016 and validate on Apr–Jun 2016). |
| Choose | 1 Jul–31 Dec 2016 | Pick the model, the feature set (including the leakage tests above) and the buffer for both rules. Check the walk ceiling here. |
| Proof | 1 Jan–31 Aug 2017 | One run, at the end. |

- Before the proof run, we refit the chosen model and the flat rate on train and choose together, with every setting frozen. That brings the training data closer to the proof months.
- If anything changes after we see the proof results, we report both runs (slide 5).
- **Known risk:** the choose period (Jul–Dec) does not cover Jan–Jun seasonality, and proof spans Jan–Aug. We will report each rule's walks per 1,000 by month on proof so that drift is visible.

## 5. What we will compare against

1. **The client's flat rule (the official baseline).** For each night, k = max(0, ⌊r_h × book⌋ − m), where:
   - r_h is the hotel's cancellation rate on train (on train and choose for the proof refit);
   - m is a whole-number safety margin chosen on choose, as the cost-minimising value that meets the ceiling. That is the same procedure we use for our own buffer.

   Every saving we report is measured against this rule.
2. **Oversell nothing (k = 0).** Shown for context only, never as the saving.
3. **Segment-rate rule.** Cancellation rates by hotel × deposit_type × market_segment, using the same k-rule as ours. This shows how much of any gain needs a model at all.
4. **Model candidates.** Regularised logistic regression first, because it is simple, well calibrated and explainable. Then gradient-boosted trees, with isotonic or Platt calibration fitted inside train.
   - Model-level metrics: log loss, Brier score, a calibration curve, and the night-level error between the summed p and the actual cancellations (mean error and MAE per night).
   - We do not report accuracy.
5. **Perfect foresight (k = A).** Used only as a ceiling on what is achievable, labelled as unattainable.

## 6. Turning probabilities into rooms to oversell each night

For each hotel h and night n:

> **k = max(0, ⌊expected − z_h × spread⌋)**

- `expected` and `spread` come from `contract.nightly_table`.
- **The buffer z_h** is chosen on the choose period over a grid, for example 0 to 4 in steps of 0.05. Two candidate structures:
  - one shared z;
  - one z per hotel, searched jointly so that the **combined** ceiling holds.

  We pick the cost-minimising setting with walks per 1,000 ≤ 10 according to `night_cost`. Fewer free parameters is the tiebreak.
- **Why z is fitted rather than set at 2.33:** `spread` assumes bookings cancel independently. Group bookings cancel together, so the real spread is wider, and a fitted z absorbs that.
- **Optional refinement, only if it beats the plain rule on choose:** add an extra spread term per night that grows with the share of group or block bookings.
- **Safety margin under the ceiling (needs your approval):** because the period shifts from choose to proof, we propose choosing z under a tighter internal target of **8 per 1,000 on choose**. If you prefer, we use the contract's 10 exactly. The flat rule's m gets the same target, so the comparison stays fair.
- **Rounding:** floor for both rules. Whole numbers and k ≥ 0 match what `night_cost` requires.
- **Fixed before the proof run:** the model, the features, the scored set, the z values and the flat rule's m.

## 7. What we will report

**Proof period (run once).** Our rule beside the flat rule, broken out by City, Resort and total:
- cost in EUR;
- empty rooms;
- walked guests;
- walks per 1,000 and whether the ceiling was met;
- number of nights.

We also show the saving in euros and in rooms against the flat rule, plus walks per 1,000 by month. A euro figure always appears with its rooms and walks.

**Choose period.** The same table, plus the buffer search curve (cost against walks per 1,000) for both rules, showing where each setting was picked.

**Model diagnostics.** Log loss, Brier, calibration plot, and night-level error between expected and actual cancellations, by hotel. Also the with/without results for the flagged leakage columns.

**Findings on the brief's three notes:**
1. The measured Non Refund cancellation rate, and what drives it.
2. Why a ranked list of cancellers is the wrong tool, and a nightly count the right one.
3. Why accuracy is misleading at a base rate of about 25–37%, with calibration shown instead.

**Morning table.** One row per hotel and night for the next 14 nights, with these columns:
- hotel, night, bookings on the book, expected cancellations, buffer (z × spread, in rooms) and oversell k;
- optionally stay value *V* and the flat rule's k for comparison.

For the demo this is built from the last 14 arrival nights in the data (18–31 Aug 2017), using the final book as the contract says. It carries a stated caveat: 14 days out, only about half of the final book exists. Scoring with only the bookings known on the morning of the run is the first roadmap item.

**`docs/DECISIONS.md`.** Every exclusion with its row count, every dropped column with its reason, every setting chosen, and the dataset citation (Antonio, de Almeida & Nunes, 2019, CC BY 4.0).

**Out of scope for this build:** marketing's "hidden guest types" (clustering). It is noted as a possible follow-on, because it does not affect the nightly oversell number.

---

## Decisions we need you to approve before we build

1. The leakage exclusions: `country`, `booking_changes`, `days_in_waiting_list`, `assigned_room_type` and the reservation status fields. Plus the with/without test for parking and special requests.
2. The scored set: drop 0-night stays, the negative and extreme `adr` rows, and bookings with no guests. Keep duplicate rows.
3. The buffer: one per hotel (searched jointly) or one shared z.
4. The ceiling target on choose: an internal 8 per 1,000 for both rules, or the contract's 10 exactly.

We will wait for your approval before writing any code.
