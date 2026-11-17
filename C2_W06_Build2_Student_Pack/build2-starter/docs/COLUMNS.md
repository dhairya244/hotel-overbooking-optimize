# Which columns did the hotel know on the day of booking?

**Owner:** Data Lead. **Closes:** part of ladder stage 1. **Used by:** `src/features.py`, the PRD and slide 4.

Put every column in exactly one bin, by when the hotel learns its value:

1. **Fixed at booking**: known on the day the booking is made, and it does not change.
2. **Amendable**: known at booking but it can change before arrival, or it is only partly known at booking.
3. **After the fact**: written at check-in, during the stay, or when the outcome is already known.

Only the first bin feeds the MVP. A second-bin column may be tried with its caveat written beside it. A third-bin column never feeds a method. The dataset article (Antonio, de Almeida and Nunes, 2019) says how several columns were recorded; cite it where it settles a bin.

The evidence column holds the number or the source that settled the bin, for example a rate you computed, or a sentence from the dataset article.

| Column | Bin (1, 2 or 3) | Why | Evidence |
|---|---|---|---|
| `hotel` | | | |
| `is_canceled` | | | |
| `lead_time` | | | |
| `arrival_date_year` | | | |
| `arrival_date_month` | | | |
| `arrival_date_week_number` | | | |
| `arrival_date_day_of_month` | | | |
| `stays_in_weekend_nights` | | | |
| `stays_in_week_nights` | | | |
| `adults` | 1, with caveat | The party size is stated when the booking is made, but it can be amended before arrival. | Kept in the model: removing `adults`, `children` and `babies` raised the forest's choose-period cost by EUR 22k (`docs/DECISIONS.md`). |
| `children` | 1, with caveat | As `adults`. | 4 missing values filled with 0. |
| `babies` | 1, with caveat | As `adults`. | As `adults`. |
| `meal` | | | |
| `country` | 2 | Entered at booking, but the data suggests it is corrected at check-in, so cancelled bookings keep a default value. The dataset definition ("Country of origin") does not say when it is recorded. | Inside Offline TA/TO, 97.4% of cancelled bookings are PRT against 26.8% of stays; inside Groups, 95.1% against 30.9%. A tour group's nationality should not depend on whether it cancels. |
| `market_segment` | | | |
| `distribution_channel` | | | |
| `is_repeated_guest` | | | |
| `previous_cancellations` | | | |
| `previous_bookings_not_canceled` | | | |
| `reserved_room_type` | | | |
| `assigned_room_type` | | | |
| `booking_changes` | | | |
| `deposit_type` | | | |
| `agent` | | | |
| `company` | | | |
| `days_in_waiting_list` | | | |
| `customer_type` | | | |
| `adr` | 2 | The booked rate exists at booking, but the value is built from transactions during the stay, so it can change. Still used by `src/contract.py` for the stay value, which is the client's scoring, not a model input. | Dataset definition: "dividing the sum of all lodging transactions by the total number of staying nights". Stays have `adr` = 0 five times as often as cancellations (2.5% against 0.5%). |
| `required_car_parking_spaces` | | | |
| `total_of_special_requests` | | | |
| `reservation_status` | | | |
| `reservation_status_date` | | | |

## What happens to a method when the late columns go in?

_Train the same method twice on the same split, once with first-bin columns only and once with the second and third bins added. Then run the first version once more on a random split. Record the three AUCs here and say which one the client should believe._

| Run | Columns | Split | AUC on the proof period |
|---|---|---|---|
| A | First bin only | Time | 0.798 |
| B | All three bins | Time | 1.000 |
| C | First bin only | Random | 0.829 |

Same method in all three runs: logistic regression with the settings in `models/hyperparams.json`, fitted on train and choose together. Reproduce with `python src/late_columns.py`, which writes `evidence/late_columns_auc.csv`.

The client should believe Run A. Run B is perfect because `reservation_status` records the outcome itself, which is how a vendor's demo reaches 95% accuracy and then fails in the lobby. Run C is 0.03 higher than Run A because a random split puts test bookings next to training bookings in time, which never happens when the model is used.

Before `country` and `adr` moved to bin 2, Run A was 0.835. The 0.037 difference is what those two columns were adding.
