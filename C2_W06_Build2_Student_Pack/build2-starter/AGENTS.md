# Which rules must a coding agent follow in this repository?

## Which rules has our team set?

1. Models may only use the columns in `features.bin1_features`. Bin 2 and bin 3 columns can change or are filled in after booking. Adding them pushes AUC from 0.798 to a fake 1.000 (`python src/late_columns.py`). Don't move `country` or `adr` back to bin 1 without a new row in `docs/DECISIONS.md`.
2. Never split the data at random. Split by arrival date with `contract.split_periods`: train is before 1 July 2016, choose is July to December 2016, proof is 2017.
3. Never edit `src/contract.py`. It is the client's scoring rule.
4. Pick the buffer on the choose period only. Never change a setting after seeing a proof number. The proof period is run once, at the end, with `python src/backtest.py`.
5. We decide per hotel per night. Add up each booking's chance of cancelling for each night with `contract.nightly_table`. Never hand over a list of individual bookings.
6. Never report euros on their own. Always show euros, empty rooms, walked guests and walks per 1,000 together. A rule with more than 10 walks per 1,000 is rejected, however much it saves.
7. `nightly.py` only loads `models/chosen.joblib` and never retrains. To change the model or buffer, rerun `backtest.py` and commit the new file.
8. Log every cleaning step in `docs/DECISIONS.md` with the reason and the number of rows it affects.
9. Every number on a slide must come from a command in this repo. Don't type results into a document by hand without saying which command made them.
10. Never commit `data/hotels.csv` or `.venv/`. Download the data with `python src/data.py`.

## Which general coding guidelines apply?

<!-- Append Andrej Karpathy's guidelines below this line with the commands in docs/AI_WORKFLOW.md. -->
