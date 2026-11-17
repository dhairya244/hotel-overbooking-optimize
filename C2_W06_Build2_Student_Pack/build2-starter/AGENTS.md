# Which rules must a coding agent follow in this repository?

## Which rules has our team set?

1. Never feed a method any column outside `features.bin1_features`. Bin 2 and bin 3 columns can change or are filled in after booking, and adding them lifts AUC from 0.798 to 1.000 (`python src/late_columns.py`). `country` and `adr` are bin 2: do not move them back without a new row in `docs/DECISIONS.md`.
2. Never split the bookings at random. Split by arrival date with `contract.split_periods`: train before 1 July 2016, choose from then to 31 December 2016, proof from 1 January 2017.
3. Never edit `src/contract.py`. It is the client's scoring rule, and every method is scored by it on the same nights.
4. Choose the buffer on the choose period only, and never change any setting after reading a proof-period number. The proof period is run once, at the end, by `python src/backtest.py`.
5. The unit of decision is one hotel on one night. Add each booking's cancel probability up per night with `contract.nightly_table`, and never ship a per-booking list.
6. Never report euros alone. Every result shows euros, empty rooms, walked guests and walks per 1,000 together, and a rule above 10 walks per 1,000 is rejected whatever it saves.
7. `nightly.py` loads `models/chosen.joblib` and never retrains. If the model or its buffer must change, rerun `backtest.py` and commit the new file.
8. Log every cleaning or filtering choice in `docs/DECISIONS.md` with the reason and the number of rows it touched, before the code that does it.
9. Every number that goes on a slide must come from a command in this repository. Do not type a result into a document by hand without saying which command made it.
10. Never commit `data/hotels.csv` or `.venv/`. The data is downloaded by `python src/data.py`.

## Which general coding guidelines apply?

<!-- Append Andrej Karpathy's guidelines below this line with the commands in docs/AI_WORKFLOW.md. -->
