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
| `hotel` | 1 | Which hotel the booking is for. Fixed when the booking is made. | Dataset definition: "Hotel (H1 = Resort Hotel or H2 = City Hotel)". |
| `is_canceled` | 3 | This is the outcome we predict, so it can never be an input. | Dataset definition: "Value indicating if the booking was canceled (1) or not (0)". Includes no-shows. |
| `lead_time` | 1 | Days from making the booking to arrival. Fixed on the day of booking. | Dataset definition: "days that elapsed between the entering date of the booking into the PMS and the arrival date". |
| `arrival_date_year` | 2 | Known at booking, but guests can change their dates. | `booking_changes` counts date changes among other amendments. Arrival month and weekday also made the forest EUR 305k worse on the choose period. |
| `arrival_date_month` | 2 | Same as `arrival_date_year`. | Same as `arrival_date_year`. |
| `arrival_date_week_number` | 2 | Same as `arrival_date_year`. | Same as `arrival_date_year`. |
| `arrival_date_day_of_month` | 2 | Same as `arrival_date_year`. | Same as `arrival_date_year`. |
| `stays_in_weekend_nights` | 2 | Booked at the start, but the stay can be made longer or shorter. | Dataset definition: nights "the guest stayed or booked to stay", so for stays it is what actually happened. |
| `stays_in_week_nights` | 2 | Same as `stays_in_weekend_nights`. | Same as `stays_in_weekend_nights`. |
| `adults` | 1, with caveat | Given when booking, but guests can change it before arrival. | Kept: dropping `adults`, `children` and `babies` made the forest EUR 22k worse on the choose period. |
| `children` | 1, with caveat | Same as `adults`. | 4 missing values set to 0. |
| `babies` | 1, with caveat | Same as `adults`. | Same as `adults`. |
| `meal` | 2 | Chosen at booking but can be changed before arrival. | Dataset definition: "Type of meal booked". |
| `country` | 2 | Entered at booking, but it looks like it gets corrected at check-in. Bookings that cancel never get corrected. The dataset only says "Country of origin", not when it is filled in. | For Offline TA/TO bookings, 97.4% of cancellations are PRT but only 26.8% of stays. For Groups, 95.1% against 30.9%. A tour group's nationality shouldn't depend on whether it cancels. |
| `market_segment` | 1 | Who the customer is (group, online agent and so on). Set when the booking comes in. | Dataset definition: "Market segment designation". |
| `distribution_channel` | 1 | How the booking arrived. Set when the booking comes in. | Dataset definition: "Booking distribution channel". |
| `is_repeated_guest` | 1 | Whether this guest has stayed before. Known when the booking is made. | Dataset definition: "if the booking name was from a repeated guest". |
| `previous_cancellations` | 1 | Counts earlier bookings only, so it is known at booking. | Dataset definition: "previous bookings that were cancelled by the customer prior to the current booking". Its link to cancelling drifts a lot over time (one-column AUC 0.657 on train, 0.510 on choose). |
| `previous_bookings_not_canceled` | 1 | Same as `previous_cancellations`. | Dataset definition: "previous bookings not cancelled by the customer prior to the current booking". |
| `reserved_room_type` | 2 | Chosen at booking but can be changed. | Dataset definition: "Code of room type reserved". |
| `assigned_room_type` | 3 | Decided by the hotel at check-in, so it doesn't exist for bookings that cancel. | Dataset definition: "Sometimes the assigned room type differs from the reserved room type due to hotel operation reasons (e.g. overbooking)". |
| `booking_changes` | 2 | Counts changes until check-in or cancellation, so the final number is only known at the end. A strict reading would put it in bin 3. | Dataset definition: "from the moment the booking was entered on the PMS until the moment of check-in or cancellation". |
| `deposit_type` | 1 | The deposit is made to guarantee the booking, so it is known at booking. | Dataset definition: "if the customer made a deposit to guarantee the booking". Non Refund bookings cancel 99.4% of the time, which is odd but not a timing problem. |
| `agent` | 1 | The travel agency that made the booking. Fixed at booking. Empty means no agent (set to 0). | Dataset definition: "ID of the travel agency that made the booking". 16,340 empty. |
| `company` | 1 | The company that made or pays for the booking. Fixed at booking. Empty means no company (set to 0). | Dataset definition: "ID of the company/entity that made the booking or responsible for paying". 112,593 empty. |
| `days_in_waiting_list` | 2 | Only known once the booking is confirmed, which can be after it was made. | Dataset definition: "days the booking was in the waiting list before it was confirmed". |
| `customer_type` | 1 | Transient, group, contract and so on. Set when the booking is made. | Dataset definition: "Type of booking": Contract, Group, Transient or Transient-party. |
| `adr` | 2 | There is a booked rate at booking, but the value is worked out from what the guest pays during the stay, so it can change. `src/contract.py` still uses it for the stay value; it just isn't a model input. | Dataset: "dividing the sum of all lodging transactions by the total number of staying nights". Stays have `adr` = 0 five times more often than cancellations (2.5% against 0.5%). |
| `required_car_parking_spaces` | 2 | Guests can ask for parking any time before or during the stay. | Dataset definition: "Number of car parking spaces required by the customer". |
| `total_of_special_requests` | 2 | Guests can add requests any time before arrival. | Dataset definition: "Number of special requests made by the customer". |
| `reservation_status` | 3 | The final status (cancelled, checked out or no-show), so it is the answer itself. | Dataset definition: "Reservation last status". Adding bin 3 columns pushes AUC to 1.000 (Run B below). |
| `reservation_status_date` | 3 | The date the final status was set, so it is only known at the end. | Dataset definition: "Date at which the last status was set". |

## What happens to a method when the late columns go in?

_Train the same method twice on the same split, once with first-bin columns only and once with the second and third bins added. Then run the first version once more on a random split. Record the three AUCs here and say which one the client should believe._

| Run | Columns | Split | AUC on the proof period |
|---|---|---|---|
| A | First bin only | Time | 0.798 |
| B | All three bins | Time | 1.000 |
| C | First bin only | Random | 0.829 |

All three runs use logistic regression with the settings in `models/hyperparams.json`, trained on train and choose together. Run `python src/late_columns.py` to get these numbers (saved to `evidence/late_columns_auc.csv`).

The client should believe Run A.

- Run B is perfect because `reservation_status` is basically the answer. That's how a vendor demo hits 95% accuracy and then fails in the lobby.
- Run C is 0.03 higher than Run A because a random split mixes up dates, so the model gets tested on bookings right next to ones it learned from. That never happens in real use.

Before we moved `country` and `adr` to bin 2, Run A was 0.835. The 0.037 gap is what those two columns were adding.
