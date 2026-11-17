# What exactly are we building, and why this way?

**Owner:** Build Lead. **Closes:** ladder stages 3 and 5. **Length:** two pages and one diagram.

Write the options section on Wednesday, before the method table exists, and update it once the table is in. The architecture goes in on Thursday.

### 1. Who uses it, when, and what do they do with it?

> **Worked example.** The city operations lead opens the route table every evening, before routes are fixed, and adds the extra visits route by route. They overrule a route when a camp is cancelled at short notice.

**Our answer:** The revenue manager opens the table every morning. It shows the next 14 nights for both hotels. For each night, they read how many extra rooms to sell and enter that number in the booking system. If they know something the model can't, like a big group that just cancelled, they change the number by hand. The table does not record these changes yet.

### 2. Which two ways could we decide, what does each cost, which do we choose, and what would flip it?

> **Worked example.** (a) A lookup table: the failure rate by booking channel and lead-time band, summed per route. Half a day to build, nothing to retrain. (b) A learned model of each booking's chance of failing, summed per route. Two days to build, retrained monthly. We choose (b) because it cuts idle slots by a further 9% with the guardrail met; we would flip to (a) if the gap fell under 3% on the next quarter's data.

**Our answer:**

- **(a) Lookup table.** For each hotel, deposit type and lead-time band, take the share of past bookings that cancelled. Add these up for each night. Cheap to build, easy to read, nothing to tune.
- **(b) Learned model.** Logistic regression, decision tree or random forest gives each booking a chance of cancelling, and we add them up for each night. Takes longer to build and tune (notebooks 03 to 05) and needs retraining when bookings change.

Both turn the nightly total into rooms the same way, with the buffer in `src/k_calculator.py`.

We picked the one that costs least on the choose period without going over 10 walks per 1,000. The random forest won. It cost EUR 1,193,673 on the choose period, against EUR 1,880,287 for the lookup table, so it saved EUR 686,614 (37%). We would go back to the lookup table if, after retraining, the forest saved less than 10% over it. Below that, the extra work of building and explaining it isn't worth it.

### 3. What is our answer to the wish-list item?

_One paragraph with a number. Say which method the item would need and whether its output would change any number the client acts on._

**Our answer:** Finding "hidden guest types" would need clustering, which means grouping bookings without looking at whether they cancelled. The data already shows that guest types behave very differently: Groups cancel 61% of the time, Direct bookings 15% (`notebooks/01_baseline.ipynb`). `market_segment` and `customer_type` are already model inputs. Clusters would only change the oversell number if adding them made the model cheaper on the choose period, and we haven't tested that. So for now this helps marketing, not the nightly table.

### 4. What exactly is in the table the client reads?

> **Worked example.** One row per route and morning: route, date, slots booked, expected failures, buffer, extra visits to book, and a one-line reason.

**Our answer:** `src/nightly.py` writes one row per hotel and night to `outputs/oversell_<date>_<nights>n.csv`. The columns are:

- `hotel`
- `night`
- `bookings`: bookings due that night
- `expected_cancellations`
- `buffer_rooms`: rooms held back for safety
- `oversell`: extra rooms to sell

There is no one-line reason per row yet.

### 5. Which inputs do we use, by bin?

_Point to `docs/COLUMNS.md` and list here only the columns the method reads, each with its bin._

**Our answer:** The model reads 14 columns, all bin 1 (`features.bin1_features`; bins are in `docs/COLUMNS.md`): `hotel`, `lead_time`, `adults`, `children`, `babies`, `market_segment`, `distribution_channel`, `is_repeated_guest`, `previous_cancellations`, `previous_bookings_not_canceled`, `deposit_type`, `agent`, `company` and `customer_type`. The lookup table uses only `hotel`, `deposit_type` and `lead_time`.

On 17 November we moved `country` and `adr` to bin 2. `country` looks like it gets corrected at check-in, and `adr` is built from what the guest spends during the stay. We kept `adults`, `children` and `babies` in bin 1, but note that guests can change them before arrival.

### 6. Where do the numbers come from, and how is the buffer set and frozen?

> **Worked example.** Each booking gets a probability of failing; the probabilities are summed per route; the buffer is the number of slots subtracted from that sum, chosen on the choose period as the cheapest buffer that keeps the guardrail, then frozen for the proof period.

**Our answer:**

1. A model trained on the train period gives each booking a chance of cancelling.
2. `contract.nightly_table` adds these up for each hotel and night (`expected`). It also gives `spread`, how much that total could vary.
3. Rooms to oversell = `floor(expected - z x spread)`, never below 0 (`k_calculator.calculate_k`). z is the buffer.
4. `find_best_buffer` tries z from 0.0 to 4.0 in steps of 0.1 on the choose period. It keeps the cheapest z with no more than 10 walks per 1,000.
5. `backtest.py` saves the model and its z to `models/chosen.joblib`. After that nothing changes, and `nightly.py` only reads the file.

The client's flat rule is tuned the same way, with a fixed number of rooms (0 to 60) instead of z.

### 7. What is the error bill on the proof period?

_Euros, rooms and walks per 1,000 for the chosen rule and for the client's flat rule, from `python src/backtest.py`._

| Rule | Empty rooms | Walked guests | Walks per 1,000 | Cost (EUR) | Saving a month against the flat rule (EUR) |
|---|---|---|---|---|---|
| Client's flat rule | 8,179 | 151 | 6.07 | 3,934,243 | 0 |
| Our chosen rule (random forest, 14 columns, z = 0.9) | 4,084 | 62 | 2.49 | 2,040,111 | 236,766 |

The proof period is 1 January to 31 August 2017: eight months, 486 hotel-nights. The monthly saving is the total saving (EUR 1,894,131) divided by 8. Run `python src/backtest.py` to get these numbers; the full output is in `evidence/backtest_output.txt`.

**We ran the proof twice, so we report both.** The first run used 16 columns, including `country` and `adr`. It cost EUR 1,936,178, with 3,708 empty rooms, 134 walked guests and 5.38 walks per 1,000, saving EUR 249,758 a month (`evidence/backtest_before_feature_change.txt`). We then moved those two columns to bin 2 (see `docs/DECISIONS.md`). The new rule costs EUR 103,933 more over the eight months and leaves 376 more rooms empty, but walks 72 fewer guests.

These euro numbers assume every cancelled room could have been sold again. By our estimate, only 65% of City Hotel nights and 62% of Resort Hotel nights in the proof period were nearly full (`evidence/full_night_share.csv`).

### 8. What does the system look like, first as a black box and then inside?

_Two drawings. The black box: what goes in, what comes out, who reads it. The white box: every step from the bookings file to the table, with the file or function that does it. Then list what production would add._

**Our diagram:** `docs/architecture.png`

![Architecture: the black box, then every step of backtest.py and nightly.py, then what production would add](architecture.png)

Lane A (`python src/backtest.py`) runs once, offline. It trains the models, picks the buffer on the choose period, saves the winner to `models/chosen.joblib`, then scores the proof period once. Lane B (`python src/nightly.py --from DATE --nights 14`) loads that saved model and never retrains. Both lanes use the same 14 bin 1 columns.

**What production would add:**

- **Use only the bookings known that morning.** Right now the table counts every booking a night will ever get. Fourteen days before arrival, only about half have come in. This needs a version of `nightly_table` that works without `is_canceled`.
- **Regular retraining.** Retrain on train and choose together, pick the buffer again, and check walks per 1,000 before replacing `chosen.joblib`.
- **Real room counts.** Our euro numbers assume a cancelled room gets sold again, which only happens when the hotel is full. With real room counts, the table could show when that isn't true.
- **Monitoring and overrides.** Track walks per 1,000 on real nights, and let the revenue manager change a night and record why.

### 9. What are the limits?

> **Worked example.** Runs in under five minutes on a laptop; every number has a one-line reason; no patient name leaves the lab's systems.

**Our answer:**

- `python src/nightly.py --from 2017-08-18 --nights 14` takes about a second on a laptop (0.94 s measured).
- It only reads the bookings file and `models/chosen.joblib`, and the model only uses bin 1 columns.
- The data covers two hotels from July 2015 to August 2017.
- The table counts every booking a night will ever get, not only the ones known that morning.
- It gives no reason per row, and we haven't tested it on any other hotel.

### 10. What could go wrong?

> **Worked example.** Camps cancelled at short notice cluster on the same routes; the failure rate drifts after a price change; route leads stop trusting the table after one bad morning.

**Our answer:**

- **Groups cancel together.** The spread assumes bookings cancel independently, so it underestimates the risk. Groups cancel 61% of the time in our data. The buffer z is chosen from real results, which covers some of this, but one big group cancelling can still cause walks.
- **Bookings change over time.** Between train and proof, the cancel rate went from 35.8% to 38.7%, and the share of non-refundable bookings fell from 15.3% to 10.2%. A model trained once will get worse.
- **Not every night is full.** The euro savings assume cancelled rooms get resold. By our estimate, only 62% to 65% of proof nights were nearly full (`evidence/full_night_share.csv`).

### 11. What is out of scope?

**Our answer:** Room prices, any hotel other than these two, a per-booking list for the front desk, a version that uses only the bookings known that morning (roadmap week 7), hidden guest types (section 3), and the real number of rooms in each hotel.
