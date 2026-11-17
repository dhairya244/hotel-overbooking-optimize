# backtest.py
# 1. Train Logistic Regression, Decision Tree and Random Forest on the train bookings.
# 2. Check how good their predictions are, and find the safety buffer, on the choose period.
# 3. Test once on the proof period (the "test data") and print one table.
# 4. Save the winner for nightly.py.

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # sibling modules

import joblib
import pandas as pd

import contract
import data_loader
import k_calculator
import all_models

# The proof period is the FINAL exam. While you are still experimenting, set this to False.
RUN_PROOF = True

HERE = pathlib.Path(__file__).resolve().parent
MODELS_FOLDER = HERE.parent / "models"


def nightly_error(nights):
    """Average gap, in rooms, between expected and real cancellations per night."""
    return (nights["expected"] - nights["cancelled"]).abs().mean()


def show_scores(title, scores):
    print(title)
    print(f"   accuracy  {scores['accuracy']:.3f} ")
    print(f"   AUC       {scores['auc']:.3f}")
    print(f"   precision {scores['precision']:.3f}   recall {scores['recall']:.3f}   f1 {scores['f1']:.3f}")
    print(f"   stays guessed right {scores['true_stays']:,} | cancels guessed right {scores['true_cancels']:,}"
          f" | wrongly said cancel {scores['false_cancels']:,} | missed cancels {scores['missed_cancels']:,}")
    print("==============================================================================================")


def main():
    # STEP 1. Load the data and split it by time
    train, choose, proof = data_loader.get_ready_data()
    print(f"bookings: train {len(train):,} | choose {len(choose):,} | proof {len(proof):,}")

    trainers = {
        "lookup table": all_models.train_lookup,     # the simple baseline every model must beat
        "logistic regression": all_models.train_logistic,
        "decision tree": all_models.train_tree,
        "random forest": all_models.train_forest,
    }

    # STEP 2. For each model: train, predict the choose period, find the buffer
    models = {}
    buffers = {}
    choose_costs = {}

    for name, train_function in trainers.items():
        print("\n" + "=" * 70)
        print(name.upper())
        print("=" * 70)

        print("settings from the notebook:", all_models.load_hyperparams(name) or "none saved, using defaults")
        model = train_function(train)                                    # learn from train only
        chances = all_models.predict_chances(model, choose)           # a chance for every booking
        show_scores("Predictions on the CHOOSE period:", all_models.get_scores(choose, chances))

        nights = contract.nightly_table(choose, chances)                 # add the chances up per night
        buffer, result = k_calculator.find_best_buffer(nights)           # the cheapest safe buffer
        print(f"Best buffer on the choose period: z = {buffer} std devs = "
              f"{k_calculator.avg_rooms_held_back(nights, buffer):.1f} rooms per night on average  (cost EUR {result['cost_eur']:,.0f}, "
              f"walks per 1,000 {result['walks_per_1000']})")

        models[name] = model
        buffers[name] = buffer
        choose_costs[name] = result["cost_eur"]

    # The client's flat rule, only as a yardstick (it is not one of our models).
    # Every saving is measured against it.
    hotel_rate = train.groupby("hotel")["is_canceled"].mean()

    def flat_rule_nights(df):
        chances = df["hotel"].map(hotel_rate).to_numpy()    # every booking gets its hotel's average rate
        return contract.nightly_table(df, chances)

    flat_margin, _ = k_calculator.find_best_buffer(flat_rule_nights(choose), kind="margin")
    print(f"\nClient's flat rule: best safety margin on the choose period = {flat_margin} rooms")

    # STEP 3. The winner is the model with the lowest cost on the CHOOSE period
    winner = min(choose_costs, key=choose_costs.get)
    print(f"Winner on the choose period: {winner}")

    # STEP 4. Save the winner for nightly.py
    MODELS_FOLDER.mkdir(exist_ok=True)
    joblib.dump({
        "method_name": winner,
        "model": models[winner],
        "buffer": buffers[winner],
        "buffer_kind": "z",
    }, MODELS_FOLDER / "chosen.joblib")
    print("Saved to models/chosen.joblib")

    if not RUN_PROOF:
        print("\nRUN_PROOF is False, so the proof period was not used.")
        return

    # STEP 5. The final test on the PROOF period (run it once, then change nothing)
    print("\n" + "=" * 70)
    print("FINAL TEST on the PROOF period (2017)")
    print("=" * 70)

    flat_nights = flat_rule_nights(proof)
    flat_k = k_calculator.calculate_k(flat_nights, flat_margin, kind="margin")
    flat_result = k_calculator.score_k(flat_nights, flat_k)

    rows = [{
        "method": "flat rule (client)", "accuracy": None, "AUC": None,
        "nightly error": nightly_error(flat_nights), "buffer": f"{flat_margin:.1f} rooms", "z used (std devs)": None,
        "cost EUR": flat_result["cost_eur"], "empty rooms": flat_result["empty_rooms"],
        "walked": flat_result["walked_guests"], "walks per 1,000": flat_result["walks_per_1000"],
        "ceiling met": flat_result["ceiling_met"], "saving vs flat EUR": 0.0,
    }]

    for name, model in models.items():
        chances = all_models.predict_chances(model, proof)
        scores = all_models.get_scores(proof, chances)
        show_scores(f"{name}: predictions on the PROOF period", scores)

        nights = contract.nightly_table(proof, chances)
        k = k_calculator.calculate_k(nights, buffers[name])               # the buffer chosen earlier, unchanged
        result = k_calculator.score_k(nights, k)

        rows.append({
            "method": name, "accuracy": scores["accuracy"], "AUC": scores["auc"],
            "nightly error": nightly_error(nights), "buffer": f"{k_calculator.avg_rooms_held_back(nights, buffers[name]):.1f} rooms",
            "z used (std devs)": buffers[name],
            "cost EUR": result["cost_eur"], "empty rooms": result["empty_rooms"],
            "walked": result["walked_guests"], "walks per 1,000": result["walks_per_1000"],
            "ceiling met": result["ceiling_met"],
            "saving vs flat EUR": flat_result["cost_eur"] - result["cost_eur"],
        })

    table = pd.DataFrame(rows).set_index("method")
    print("\nRESULT TABLE (proof period)")
    print(table.round(3).to_string())


if __name__ == "__main__":
    main()
