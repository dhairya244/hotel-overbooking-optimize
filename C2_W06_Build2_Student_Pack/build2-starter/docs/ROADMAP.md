# What happens after this week?

**Owner:** Build Lead (Data Lead in the team of three). **When:** Friday.

The next three weeks, one line each, with the role that owns the work and an hour estimate. Then the production additions from the build plan.

| Week | What we would build next | Why it matters to the client, with a number | Owner | Hours |
|---|---|---|---|---|
| 7 | Run on the bookings known that morning: rebuild the nightly table from the bookings that exist N days before arrival, without needing `is_canceled`, and re-choose the buffer on that book. | Fourteen days out only about half of a night's final book exists, so the table the revenue manager reads today is built on more bookings than a real morning would have. | Model Lead | 12 |
| 8 | Retraining and drift check: refit on train and choose together, re-choose the buffer, and compare cancel rate and deposit mix against the training period before the model replaces `chosen.joblib`. | Cancel rate moved from 35.8% in train to 38.7% in proof, and the non-refundable share from 15.3% to 10.2%. The walk ceiling is 10 per 1,000, so a drifting model puts it at risk. | Data Lead | 8 |
| 9 | Capacity feed and live monitoring: replace our occupancy proxy with the hotels' real room counts, show the running walk rate, and let the manager overrule a night and record why. | By our proxy 65% of City Hotel and 62% of Resort Hotel proof nights were near full, so the euro saving is only fully earned on those nights. | Client Lead and Build Lead | 16 |

## Which production additions come with it?

| Addition | Owner | Hours |
|---|---|---|
| Run on the bookings known that morning | Model Lead | 12 |
| Scheduled retraining and drift check | Data Lead | 8 |
| Capacity feed in place of our proxy | Client Lead | 6 |
| Overrides and live walk monitoring | Build Lead | 10 |

_Hours are first estimates, not measurements. Replace them with the team's own. The week 9 line combines the last two additions, which is why it adds up to 16._
