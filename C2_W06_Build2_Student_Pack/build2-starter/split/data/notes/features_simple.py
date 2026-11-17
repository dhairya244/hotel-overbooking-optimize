from random import Random
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

bin1_features = [
    'hotel',
    'lead_time',
    'adults',
    'children',
    'babies',
    'country',
    'market_segment',
    'distribution_channel',
    'is_repeated_guest',
    'previous_cancellations',
    'previous_bookings_not_canceled',
    'deposit_type',
    'agent',
    'company',
    'customer_type',
    'adr',
]

bin2_features = [
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
    'adr'
]

bin1_categorical_cols = [
    'hotel',
    'country',
    'market_segment',
    'distribution_channel',
    'is_repeated_guest',
    'deposit_type',
    'agent',
    'company',
    'customer_type'
]

run_b_features = bin1_features + bin2_features + bin3_features


def extract_bin1_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract strictly Bin 1 features known on the day of booking."""
    num_cols = [
        "lead_time", "adr", "adults", "children", "stays_in_weekend_nights",
        "stays_in_week_nights", "is_repeated_guest", "previous_cancellations",
        "previous_bookings_not_canceled"
    ]
    cat_cols = [
        "hotel", "market_segment", "distribution_channel", "deposit_type", "customer_type"
    ]
    encoded = pd.get_dummies(df[cat_cols], drop_first=True)
    return pd.concat([df[num_cols], encoded], axis=1)


def load_data():
    data_path = Path(__file__).resolve().parent.parent / 'data' / 'hotels.csv'
    df = pd.read_csv(data_path)
    df['arrival_date'] = pd.to_datetime(
        df['arrival_date_year'].astype(str)
        + '-'
        + df['arrival_date_month']
        + '-'
        + df['arrival_date_day_of_month'].astype(str),
        format='%Y-%B-%d',
    )
    df['total_nights']=df['stays_in_weekend_nights']+df['stays_in_week_nights']
    return df

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


def random_time_split(df: pd.DataFrame, random_state: int = 42):
    """Split rows at seeded, randomized date boundaries without mixing time periods."""
    if "arrival_date" not in df.columns:
        raise ValueError("df must contain an arrival_date column")
    if df["arrival_date"].isna().any():
        raise ValueError("arrival_date cannot contain missing values")

    dates = pd.Index(df["arrival_date"].unique()).sort_values()
    if len(dates) < 3:
        raise ValueError("at least three unique arrival dates are required")

    jitter = max(1, int(len(dates) * 0.05))
    rng = Random(random_state)
    train_cut = rng.randint(
        max(1, int(len(dates) * 0.70) - jitter),
        min(len(dates) - 2, int(len(dates) * 0.70) + jitter),
    )
    validation_cut = rng.randint(
        max(train_cut + 1, int(len(dates) * 0.85) - jitter),
        min(len(dates) - 1, int(len(dates) * 0.85) + jitter),
    )

    train_end = dates[train_cut]
    validation_end = dates[validation_cut]
    train_df = df[df["arrival_date"] < train_end]
    validation_df = df[
        (df["arrival_date"] >= train_end)
        & (df["arrival_date"] < validation_end)
    ]
    test_df = df[df["arrival_date"] >= validation_end]
    return train_df, validation_df, test_df


def evaluate_logistic_regression(model, eval_df, features, run_name):
    X_eval = eval_df[features]
    y_eval = eval_df["is_canceled"]
    predictions = model.predict_proba(X_eval)[:, 1]
    auc = roc_auc_score(y_eval, predictions)

    print(f"{run_name} ROC-AUC:", round(auc, 4))
    return auc


def run_logistic_regression(train_df, val_df, features, run_name):
    X_train = train_df[features]
    y_train = train_df['is_canceled']

# Explicit classification for Bin 1
    categorical_cols = [
    col for col in features
    if col in bin1_categorical_cols
]

    numerical_cols = [
    col for col in features
    if col in bin1_numeric_cols
]

# Automatic classification for additional Bin 2 / Bin 3 features
    for col in features:

        if col not in categorical_cols and col not in numerical_cols:

            if (
            pd.api.types.is_object_dtype(X_train[col])
            or isinstance(X_train[col].dtype, pd.CategoricalDtype)
            or pd.api.types.is_string_dtype(X_train[col])
        ):
                categorical_cols.append(col)
            else:
                numerical_cols.append(col)

# Validation checks
    assert set(numerical_cols + categorical_cols) == set(features)
    assert not set(numerical_cols).intersection(categorical_cols)

    # print("Numerical columns to scale:", numerical_cols)
    # print("Categorical columns to encode:", categorical_cols)

    numerical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(
        drop='first',
        handle_unknown='infrequent_if_exist',
        min_frequency=10
    )),
])

    preprocessor = ColumnTransformer([
        ('num', numerical_pipeline, numerical_cols),
        ('cat', categorical_pipeline, categorical_cols),
    ])

    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(max_iter=2000)),
    ])

    model.fit(X_train, y_train)
    auc = evaluate_logistic_regression(model, val_df, features, run_name)
    return model, auc

# =====================================================================
# PART 4. Building the clue columns
# =====================================================================
def add_features(df):
    """Add the clue columns and make the text columns real text. Returns one DataFrame.
       Works after clean_bookings() (agent / company are 0, country is 'Unknown').
       Rare countries are not collapsed here: the models' OneHotEncoder(min_frequency=...)
       groups them, and it learns that from TRAIN only."""
    df = df.copy()

    # month and weekday of arrival, as text
    df["arrival_month"] = df["arrival_date"].dt.month.astype(str)
    df["arrival_weekday"] = df["arrival_date"].dt.dayofweek.astype(str)

    # 1 if the booking has an agent / company. An empty cell and a 0 both mean "none".
    df["is_agent"] = (df["agent"].fillna(0) != 0).astype(int)
    df["is_company"] = (df["company"].fillna(0) != 0).astype(int)

    # an empty country gets its own label, because those bookings behave differently
    df["country"] = df["country"].fillna("Unknown")

    # make all text columns real text
    for column in bin1_categorical_cols:
        df[column] = df[column].astype(str)

    return df

if __name__ == '__main__':
    df = load_data()
    # print(df.shape)
    data = clean_bookings(df)
    # print(data.isna().sum())
    print(data.shape)
    train_df = data[data['arrival_date'] < '2016-07-01']
    choose_df = data[(data['arrival_date'] >= '2016-07-01') & (data['arrival_date'] < '2017-01-01')]
    proof_df = data[data['arrival_date'] >= '2017-01-01']

    model_A, auc_A = run_logistic_regression(
        train_df,
        choose_df,
        bin1_features,
        'Run A - Bin 1 Validation',
    )
    evaluate_logistic_regression(model_A, proof_df, bin1_features, 'Run A - Bin 1 Proof Test')

    model_B, auc_B = run_logistic_regression(
        train_df,
        choose_df,
        run_b_features,
        'Run B - Bin 1+2+3 (Bin 3 leaks the answer)',
    )
    evaluate_logistic_regression(model_B, proof_df, run_b_features, 'Run B - Bin 1+2+3 Proof Test (leaky)')

    development_data = data[data['arrival_date'] < '2017-01-01']
    random_train_df, random_choose_df, random_test_df = random_time_split(development_data)
    random_model, random_auc = run_logistic_regression(
        random_train_df,
        random_choose_df,
        bin1_features,
        'Random Time Split - Validation',
    )
    evaluate_logistic_regression(
        random_model,
        random_test_df,
        bin1_features,
        'Random Time Split - Test',
    )

    deposit_audit = (
        data.groupby('deposit_type')['is_canceled']
        .agg(
            total_bookings='count',
            cancellations='sum',
            cancellation_rate='mean'
        )
    )

    deposit_audit['cancellation_rate'] *= 100

    print(deposit_audit)