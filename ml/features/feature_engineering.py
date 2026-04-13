def traffic_features(df):
    # Extract time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['dayofweek'] >= 5

    # Add rolling average (captures trend)
    df['rolling_mean'] = df['visitors'].rolling(window=3).mean()

    # Fill missing values from rolling
    df = df.fillna(method='bfill')

    return df


def behavior_features(df):
    # Normalize values (important for DL)
    df['spend_per_visit'] = df['total_spent'] / (df['visits'] + 1)

    return df