# How do we get from a first test to something the client can run?

**Owner:** Build Lead. **Closes:** ladder stages 4 and 6. **Length:** one page.

Three stages, each with an owner, an hour budget, a line that says when it is done, and the file that proves it. Fill the table on Wednesday morning and update the hours as you go.

| Stage | What is built | Owner | Hours planned | Hours used | Done when | Evidence file |
|---|---|---|---|---|---|---|
| POC | The client's flat rule, a lookup table and three learned models (logistic regression, decision tree, random forest). Each one gives every booking a chance of cancelling; we add these up per night and turn them into rooms with a buffer picked on the choose period. | Model Lead | _fill in_ | _fill in_ | Every method you tried prints from `python src/backtest.py` on the proof period, scored by `src/contract.py`, with the ceiling checked | `src/backtest.py`, `evidence/backtest_output.txt` |
| MVP | `src/nightly.py` reads the bookings and `models/chosen.joblib`, keeps the 14 nights asked for, and writes one row per hotel and night: bookings, expected cancellations, buffer and rooms to oversell. | Build Lead | _fill in_ | _fill in_ | `python src/nightly.py --from 2017-08-18 --nights 14` writes the nightly table from a bookings file, reading only first-bin columns, signed by the challenger | `outputs/oversell_2017-08-18_14n.csv`, `docs/architecture.png` |
| Final | The proof table puts our buffer (rooms held back based on how uncertain each night is) next to the flat rule's fixed number of rooms. `src/full_night.py` works out the full-night caveat. The roadmap is written. | Client Lead (caveat), Build Lead (roadmap) | _fill in_ | _fill in_ | The uncertainty buffer is compared with the rooms buffer, the full-night caveat is computed, and the roadmap is written | `evidence/full_night_share.csv`, `docs/ROADMAP.md` |

In the team of three, the final stage is the full-night caveat and the roadmap, because the uncertainty buffer is excused.

> **Worked example (one row, home collection).** POC: a lookup table and a learned model, each summed per route and scored on the held-back months. Owner: Model Lead. Planned 9 hours, used 11. Done when one command prints both against today's rule. Evidence: `src/backtest.py` and `evidence/poc_table.png`.

## What would production add that the MVP leaves out?

_One line each, with the role that would own it and an hour estimate. These become the roadmap._

| Addition | Why it matters | Owner | Hours |
|---|---|---|---|
| Use only the bookings known that morning | Right now we count every booking a night will ever get. Fourteen days out, only about half are in (`docs/EVALUATION_CONTRACT.md`), so real mornings have less to go on than our test did. | Model Lead | 12 |
| Regular retraining and drift check | Between train and proof, the cancel rate went from 35.8% to 38.7% and non-refundable bookings fell from 15.3% to 10.2%. A model trained once gets worse. | Data Lead | 8 |
| Real room counts instead of our estimate | By our estimate, only 65% of City Hotel and 62% of Resort Hotel proof nights were nearly full (`evidence/full_night_share.csv`). On the other nights, a cancelled room may not get resold. | Client Lead | 6 |
| Overrides and live walk tracking | The limit is 10 walks per 1,000. The manager needs to change a night, say why, and see the walk rate so far. | Build Lead | 10 |

_The hours are rough guesses. Replace them with the team's own._

## What did we cut, and why?

_Anything you planned and dropped, with the reason. A cut you explain is not a gap._

- **Using only the bookings known that morning.** The contract scores each night's full book, and `nightly_table` needs the `is_canceled` column. It's first on the roadmap.
- **Retraining on train and choose together before the proof run.** The contract allows it, but we kept the model trained on train only, so the buffer picked on the choose period still matches the model it was picked for.
- **Clustering for the wish-list item.** See `docs/PRD.md`, section 3. We didn't build it this week.
- **Arrival month and weekday as inputs.** They made the forest EUR 305k worse on the choose period, because train only has one year of each month.
