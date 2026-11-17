"""features.py: everything that turns the raw bookings into model-ready columns.

1. Bins        which columns are known when (Bin 1 = on the day of booking, Bin 2 = later, Bin 3 = leaks)
2. Cleaning    clean_bookings(): drop bad rows, fill missing values, build arrival_date and nights
3. Clue columns add_features(): text columns as text
4. Encoding    make_preparer(): scaling and one-hot encoding

notes/features_simple.py is kept untouched as a reference copy (it also has the Run A / Run B experiments).
"""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# =====================================================================
# 1. Bins
# =====================================================================
# adults, children and babies are stated at booking but can be amended before arrival.
# We keep them in Bin 1 with that caveat (docs/COLUMNS.md): dropping them cost EUR 22k on the choose period.
bin1_features = [
    'hotel',
    'lead_time',
    'adults',
    'children',
    'babies',
    'market_segment',
    'distribution_channel',
    'is_repeated_guest',
    'previous_cancellations',
    'previous_bookings_not_canceled',
    'deposit_type',
    'agent',
    'company',
    'customer_type',
]

# country and adr moved here from Bin 1 (docs/DECISIONS.md):
#   country - inside Groups and Offline TA/TO, 95-97% of cancelled bookings are PRT against 27-31% of stays,
#             which fits a default value corrected at check-in.
#   adr     - defined as lodging transactions / staying nights, so it can change after booking.
# adr is still used by src/contract.py for the stay value; it is just not a model input.
bin2_features = [
    'country',
    'adr',
    'arrival_date_year',
    'arrival_date_month',
    'arrival_date_week_number',
    'arrival_date_day_of_month',
    'stays_in_weekend_nights',
    'stays_in_week_nights',
    'meal',
    'reserved_room_type',
    'booking_changes',
    'days_in_waiting_list',
    'required_car_parking_spaces',
    'total_of_special_requests',
]

bin3_features = [
    'assigned_room_type',
    'reservation_status',
    'reservation_status_date',
]

bin1_numeric_cols = [
    'lead_time',
    'adults',
    'children',
    'babies',
    'previous_cancellations',
    'previous_bookings_not_canceled',
]

bin1_categorical_cols = [
    'hotel',
    'market_segment',
    'distribution_channel',
    'is_repeated_guest',
    'deposit_type',
    'agent',
    'company',
    'customer_type'
]

# Short names used by the notebooks (`from features import CATEGORICAL, NUMERIC, FEATURES`)
CATEGORICAL = bin1_categorical_cols
NUMERIC = bin1_numeric_cols
FEATURES = bin1_features


# =====================================================================
# 2. Cleaning
# =====================================================================
def clean_bookings(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans the raw hotel bookings dataframe based on documented decisions.

    1. Drops 180 ghost bookings where adults + children + babies == 0.
    2. Drops 1 billing error row where adr < 0.
    3. Imputes missing children with 0 (4 rows).
    4. Imputes missing country with 'Unknown' (488 rows).
    5. Imputes missing agent (16,340) and company (112,593) with 0 (direct booking).
    6. Creates 'nights' column as stays_in_weekend_nights + stays_in_week_nights.
    """

    data = df.copy()

    # one real date column, built from this frame's own year / month / day columns
    data["arrival_date"] = pd.to_datetime(
        data["arrival_date_year"].astype(str) + "-"
        + data["arrival_date_month"] + "-"
        + data["arrival_date_day_of_month"].astype(str),
        format="%Y-%B-%d",
    )

    # 1. Drop ghost bookings (180 rows)
    has_guests = (data["adults"] + data["children"].fillna(0) + data["babies"]) > 0
    data = data[has_guests].copy()

    # 2. Drop negative ADR (1 row)
    data = data[data["adr"] >= 0].copy()

    # 3. Impute missing children with 0
    data["children"] = data["children"].fillna(0).astype(int)

    # 4. Impute missing country with 'Unknown'
    data["country"] = data["country"].fillna("Unknown")

    # 5. Impute agent and company with 0
    data["agent"] = data["agent"].fillna(0).astype(int)
    data["company"] = data["company"].fillna(0).astype(int)

    # 6. Total length of stay (nights)
    data["nights"] = data["stays_in_weekend_nights"] + data["stays_in_week_nights"]

    return data


clean = clean_bookings   # name used by the notebooks


# =====================================================================
# 3. Building the clue columns
# =====================================================================
def add_features(df):
    """Make the Bin 1 text columns real text. Returns one DataFrame.
       Works after clean_bookings() (agent / company are 0, country is 'Unknown').
       Rare agents and companies are not collapsed here: the models' OneHotEncoder(min_frequency=...)
       groups them, and it learns that from TRAIN only.
       (Arrival month / weekday and is_agent / is_company used to be built here but no model read them.
       Arrival month and weekday also made the forest EUR 305k worse on the choose period, because
       train holds only one year of each month.)"""
    df = df.copy()

    # an empty country gets its own label (country is Bin 2 now, but late_columns.py still reads it)
    df["country"] = df["country"].fillna("Unknown")

    # make all text columns real text
    for column in bin1_categorical_cols:
        df[column] = df[column].astype(str)

    return df


# =====================================================================
# 4. Encoding
# =====================================================================
def make_preparer(scale_numbers):
    """The encoding: the Bin 1 columns only (used by the four models in src/all_models.py).
         categories -> OneHotEncoder(handle_unknown='ignore', min_frequency=20)
         numbers    -> StandardScaler, or untouched when scale_numbers is False (trees do not need scaling)"""
    text_step = OneHotEncoder(handle_unknown="ignore", min_frequency=20)
    if scale_numbers:
        number_step = StandardScaler()
    else:
        number_step = "passthrough"

    return ColumnTransformer([
        ("text", text_step, bin1_categorical_cols),
        ("numbers", number_step, bin1_numeric_cols),
    ])
