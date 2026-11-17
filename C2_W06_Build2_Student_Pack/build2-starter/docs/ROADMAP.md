# What happens after this week?

**Owner:** Build Lead (Data Lead in the team of three). **When:** Friday.

The next three weeks, one line each, with the role that owns the work and an hour estimate. Then the production additions from the build plan.

| Week | What we would build next | Why it matters to the client, with a number | Owner | Hours |
|---|---|---|---|---|
| 7 | Build the table from only the bookings known N days before arrival, without needing `is_canceled`, and pick the buffer again for that. | Fourteen days out, only about half of a night's bookings exist. Today's table uses all of them, so it has more to go on than a real morning would. | Model Lead | 12 |
| 8 | Retrain on train and choose together, pick the buffer again, and compare the cancel rate and deposit mix with the training period before replacing `chosen.joblib`. | The cancel rate went from 35.8% in train to 38.7% in proof, and non-refundable bookings fell from 15.3% to 10.2%. If the model drifts, the 10 per 1,000 walk limit is at risk. | Data Lead | 8 |
| 9 | Use the hotels' real room counts instead of our estimate, show the walk rate so far, and let the manager change a night and record why. | By our estimate, 65% of City Hotel and 62% of Resort Hotel proof nights were nearly full, so the euro saving only fully holds on those nights. | Client Lead and Build Lead | 16 |

## Which production additions come with it?

| Addition | Owner | Hours |
|---|---|---|
| Use only the bookings known that morning | Model Lead | 12 |
| Regular retraining and drift check | Data Lead | 8 |
| Real room counts instead of our estimate | Client Lead | 6 |
| Overrides and live walk tracking | Build Lead | 10 |

_The hours are rough guesses. Replace them with the team's own. Week 9 covers the last two additions, which is why it's 16 hours._
