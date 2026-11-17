# AI review log for the PRD and build

**Owner:** Build Lead. **Date:** 17 November 2026.

**Record type:** Retrospective summary of the AI code review and the follow-up discussion. This is not a verbatim `grill-me` transcript. Question wording below is summarized, and team responses are based on the decisions and files visible in the repository. The review summary is in `ai_logs/20261117_build-lead_claude-code_review-and-fixes.md`.

| Q | Review question (summary, not verbatim) | AI recommendation | Team response | Decision | What changed, and where |
|---|---|---|---|---|---|
| 1 | Can we defend every model input as information fixed when the booking is made? | Exclude `country` and `adr` from the model inputs until their booking-time availability is supported. Test the impact of late columns and keep the proof-period result transparent. | We removed both from `features.bin1_features`, reran the model comparison, and reported both proof runs. The audit still needs correction: `country` and `adr` are currently labelled Bin 2, while the definitions and evidence suggest they may belong in Bin 3. `adults`, `children`, `babies`, and `deposit_type` are also labelled Bin 1 despite caveats about later changes or payment timing. | Accepted, with bin labels still open for Data Lead review. | `src/features.py`, `docs/COLUMNS.md`, `docs/DECISIONS.md`, `docs/PRD.md`; both proof results are recorded in `docs/PRD.md` and `evidence/`. |
| 2 | Does the comparison include the simple baseline the client can understand, and is every method scored the same way? | Add a lookup-table baseline and compare it with the flat rule and at least two learned models using the same temporal split, buffer selection period, and scoring contract. | We added a lookup method using hotel, deposit type, and lead-time bands. On the choose period, the random forest cost EUR 1,193,673 and the lookup cost EUR 1,880,287; both met the walk ceiling. The random forest was selected. | Accepted. | `src/all_models.py`, `src/backtest.py`, `docs/PRD.md`, `docs/BUILD_PLAN.md`, and `evidence/backtest_output.txt`. |
| 3 | Does the nightly table show enough information to understand the recommendation, and can this MVP be used with a truly future booking file? | Show the rooms held back in the output. State that this replay uses the final book and that a live version needs to work without the cancellation outcome column. | We added `buffer_rooms` to the CSV. We documented that the current historical replay counts the final book and depends on `is_canceled` for the contract aggregation; a production version needs an as-of-date booking table. | Accepted. | `src/nightly.py`, `docs/PRD.md`, `docs/BUILD_PLAN.md`, `docs/ROADMAP.md`, and `docs/architecture.png`. |

## What we learned

The prediction is per booking, but the hotel acts per hotel-night: booking probabilities are added up, then a buffer turns the expected cancellations into whole rooms to oversell. A high AUC can be misleading when late columns reveal information recorded after booking, so the column timing audit has to match the model inputs. The MVP runs on the historical final book; the production tool needs the bookings actually known that morning and cannot depend on `is_canceled`.

## Questions still open

- Complete and evidence every bin in `docs/COLUMNS.md`; the current Bin 1 list still needs a strict timing check.
- Make the architecture diagram and PRD table agree exactly with the final feature list and nightly output schema.
- Run a genuine interactive grill if the course requires a verbatim grilling session; this retrospective summary does not claim one occurred.
