import os
from ml.pipelines.data_pipeline import load_traffic_data, load_behavior_data
from ml.features.feature_engineering import behavior_features
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import numpy as np

def create_sequences(data, seq_length=24):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

def retrain_traffic():
    print("\n--- Retraining Traffic Model ---")
    df_t = load_traffic_data()
    df_t = df_t.dropna().sort_values('timestamp')

    df_t['hour'] = df_t['timestamp'].dt.hour / 23.0
    df_t['dayofweek'] = df_t['timestamp'].dt.dayofweek / 6.0

    features = df_t[['visitors', 'hour', 'dayofweek']].values
    scaler = MinMaxScaler()
    features = scaler.fit_transform(features)

    X_t, y_t = create_sequences(features)
    y_t = y_t[:,0]  # next visitors

    split = int(len(X_t) * 0.8)
    X_train, X_val = X_t[:split], X_t[split:]
    y_train, y_val = y_t[:split], y_t[split:]

    # --- Load old model or create new if input shape changed ---
    create_new_model = True
    if os.path.exists("models/traffic/v1_lstm.h5"):
        old_model = keras.models.load_model("models/traffic/v1_lstm.h5", compile=False)
        if old_model.input_shape[-1] == X_train.shape[2]:
            traffic_model = old_model
            create_new_model = False
            print("✅ Loaded existing traffic model v1")
        else:
            print("⚠️ Input shape changed. Creating new traffic model.")

    if create_new_model:
        traffic_model = keras.Sequential([
            keras.layers.LSTM(64, input_shape=(X_train.shape[1], X_train.shape[2])),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(1)
        ])

    traffic_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    traffic_model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=20, callbacks=[early_stop])

    val_loss, val_mae = traffic_model.evaluate(X_val, y_val)
    print(f"📊 Traffic Validation MAE: {val_mae:.4f}")

    traffic_model.save("models/traffic/v2_lstm.h5")
    print("✅ Traffic retraining complete")

def retrain_behavior():
    print("\n--- Retraining Behavior Model ---")
    df_b = behavior_features(load_behavior_data())
    feature_cols = ['total_spent', 'visits', 'avg_basket', 'spend_per_visit']
    X = df_b[feature_cols].values
    y = df_b['label'].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    create_new_model = True
    if os.path.exists("models/behavior/v1.h5"):
        old_model = keras.models.load_model("models/behavior/v1.h5", compile=False)
        if old_model.input_shape[-1] == X_train.shape[1]:
            behavior_model = old_model
            create_new_model = False
            print("✅ Loaded existing behavior model v1")
        else:
            print("⚠️ Input shape changed. Creating new behavior model.")

    if create_new_model:
        behavior_model = keras.Sequential([
            keras.layers.Dense(32, activation='relu', input_shape=(X_train.shape[1],)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])

    behavior_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    behavior_model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=20, batch_size=32, callbacks=[early_stop])

    val_loss, val_acc = behavior_model.evaluate(X_val, y_val)
    print(f"📊 Behavior Validation Accuracy: {val_acc:.4f}")

    behavior_model.save("models/behavior/v2.h5")
    print("✅ Behavior retraining complete")

if __name__ == "__main__":
    retrain_traffic()
    retrain_behavior()