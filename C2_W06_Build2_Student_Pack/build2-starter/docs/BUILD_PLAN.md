# How do we get from a first test to something the client can run?

**Owner:** Build Lead. **Closes:** ladder stages 4 and 6. **Length:** one page.

Three stages, each with an owner, an hour budget, a line that says when it is done, and the file that proves it. Fill the table on Wednesday morning and update the hours as you go.

| Stage | What is built | Owner | Hours planned | Hours used | Done when | Evidence file |
|---|---|---|---|---|---|---|
| POC | The client's flat rule, a lookup table (hotel, deposit type, lead-time band) and three learned models (logistic regression, decision tree, random forest). Each gives every booking a cancel chance, the chances are added up per night, and a buffer chosen on the choose period turns them into rooms to oversell. | Model Lead | _fill in_ | _fill in_ | Every method you tried prints from `python src/backtest.py` on the proof period, scored by `src/contract.py`, with the ceiling checked | `src/backtest.py`, `evidence/poc_table.png` (screenshot still to take) |
| MVP | `src/nightly.py`: reads a bookings file and `models/chosen.joblib`, keeps the 14 nights asked for, and writes one row per hotel and night: bookings, expected cancellations, buffer in rooms, rooms to oversell. | Build Lead | _fill in_ | _fill in_ | `python src/nightly.py --from 2017-08-18 --nights 14` writes the nightly table from a bookings file, reading only first-bin columns, signed by the challenger | `outputs/oversell_2017-08-18_14n.csv`, `docs/architecture.png` |
| Final | The z-buffer (rooms held back in proportion to the spread of the night's cancellations) is compared with the flat rule's fixed rooms margin in the proof table. The full-night caveat is computed by `src/full_night.py`. The roadmap is written. | Client Lead (caveat), Build Lead (roadmap) | _fill in_ | _fill in_ | The uncertainty buffer is compared with the rooms buffer, the full-night caveat is computed, and the roadmap is written | `evidence/full_night_share.csv`, `docs/ROADMAP.md` |

In the team of three, the final stage is the full-night caveat and the roadmap, because the uncertainty buffer is excused.

> **Worked example (one row, home collection).** POC: a lookup table and a learned model, each summed per route and scored on the held-back months. Owner: Model Lead. Planned 9 hours, used 11. Done when one command prints both against today's rule. Evidence: `src/backtest.py` and `evidence/poc_table.png`.

## What would production add that the MVP leaves out?

_One line each, with the role that would own it and an hour estimate. These become the roadmap._

| Addition | Why it matters | Owner | Hours |
|---|---|---|---|
| Run on the bookings known that morning | Today a run scores each night's final book. Fourteen days before arrival only about half of it exists (`docs/EVALUATION_CONTRACT.md`), so the table the manager gets in real life is built on less than we tested. | Model Lead | 12 |
| Scheduled retraining and drift check | Between train and proof the cancel rate rose from 35.8% to 38.7% and the non-refundable share fell from 15.3% to 10.2%. A model fitted once will age. | Data Lead | 8 |
| Capacity feed in place of our proxy | By our proxy only 65% of City Hotel proof nights and 62% of Resort Hotel proof nights were near full (`evidence/full_night_share.csv`). On the rest, a cancelled room is not necessarily resold. | Client Lead | 6 |
| Overrides and live walk monitoring | The ceiling is 10 walks per 1,000. The manager needs to overrule a night, record why, and see the running walk rate. | Build Lead | 10 |

_Hours are first estimates, not measurements. Replace them with the team's own._

## What did we cut, and why?

_Anything you planned and dropped, with the reason. A cut you explain is not a gap._

- **A run on the bookings known that morning.** The contract scores each night's final book, and `nightly_table` needs the `is_canceled` column. Building an as-of-date version is the first thing on the roadmap.
- **Refitting on train and choose together before the proof run.** The contract allows it. We kept the model fitted on train only so the buffer chosen on the choose period matches the model it was chosen for.
- **Answering the wish-list item with a clustering model.** The reasoning is in `docs/PRD.md`, section 3. We did not build it this week.
