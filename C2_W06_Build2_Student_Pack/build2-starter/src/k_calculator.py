# k_calculator.py
# k = how many EXTRA rooms to sell on a night.
#
#   z-buffer  (our models):   k = floor( expected - z * spread )
#   margin    (client rule):  k = floor( expected ) - margin
#
# "expected" = sum of the cancel chances of that night's bookings (the average number of cancels).
# "spread"   = standard deviation of that sum. So z is a Z-SCORE: how many standard deviations
#              below the average we hold back. z = 0 sells exactly the expected cancels,
#              z > 0 is cautious (fewer walks). The buffer is never negative (0 to 4).
# The flat rule has no spread, so its buffer is a plain number of rooms.

import numpy as np

import contract    # the starter's scoring file (we do not change it)

Z_GRID = [round(i * 0.1, 1) for i in range(0, 41)]   # 0.0 ... 4.0 (a buffer only holds rooms back)
MARGIN_GRID = list(range(0, 61))                       # 0 ... 60 rooms


def calculate_k(nights, buffer, kind="z"):
    """Work out k for every night.
       kind="z"      -> hold back (buffer x spread) rooms. Used for the models.
       kind="margin" -> hold back a fixed number of rooms. Used for the client's flat rule."""
    if kind == "margin":
        k = np.floor(nights["expected"]) - buffer
    else:
        k = np.floor(nights["expected"] - buffer * nights["spread"])

    k = np.clip(k, 0, None)        # k is never below 0
    return k.astype(int)           # whole rooms only


def buffer_label(buffer, kind="z"):
    """Readable text for the result table, so the unit is never a mystery."""
    if kind == "margin":
        return f"{buffer} rooms"
    return f"{buffer} std devs"


def avg_rooms_held_back(nights, buffer, kind="z"):
    """The buffer expressed in rooms per night, so z and margin can be compared."""
    if kind == "margin":
        return float(buffer)
    return float(buffer * nights["spread"].mean())


def find_best_buffer(nights, kind="z"):
    """Try many buffers and keep the CHEAPEST one that stays inside the walk limit.
       Run this on the CHOOSE period only. Returns the buffer and its score.
       If the best buffer sits on the edge of the grid, a warning is printed."""
    buffers_to_try = MARGIN_GRID if kind == "margin" else Z_GRID

    best_buffer = None
    best_result = None

    for buffer in buffers_to_try:
        k = calculate_k(nights, buffer, kind)
        result = contract.night_cost(nights, k)     # the starter scores it for us

        if result["ceiling_met"]:                   # only buffers inside the walk limit count
            if best_result is None or result["cost_eur"] < best_result["cost_eur"]:
                best_buffer = buffer
                best_result = result

    if best_result is None:
        raise ValueError("No buffer stayed inside the walk limit. Try a bigger range of buffers.")

    if best_buffer in (buffers_to_try[0], buffers_to_try[-1]):
        print(f"   WARNING: best buffer {best_buffer} is at the edge of the grid; widen the grid.")

    return best_buffer, best_result


def score_k(nights, k):
    """Score a k: euros, empty rooms, walked guests, walks per 1,000, ceiling met."""
    return contract.night_cost(nights, k)
