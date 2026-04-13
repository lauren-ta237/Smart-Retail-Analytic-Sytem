# ml/training/train_traffic_model.py

import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split

from ml.pipelines.data_pipeline import load_traffic_data
from ml.features.feature_engineering import traffic_features

def train_traffic_model(seq_length=5, epochs=20, batch_size=16, save_path="models/traffic/v1_lstm.keras"):
    """
    Trains an LSTM model on traffic visitor data and saves it.

    Args:
        seq_length (int): Number of time steps for LSTM sequences.
        epochs (int): Number of training epochs.
        batch_size (int): Batch size for training.
        save_path (str): File path to save the trained model (.keras recommended).
    
    Returns:
        model: Trained Keras LSTM model.
    """
    # Load and prepare data
    df = load_traffic_data()
    df = traffic_features(df)

    data = df['visitors'].values

    # Create sequences for LSTM
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    
    X = np.array(X)
    y = np.array(y)

    # Reshape for LSTM [samples, time_steps, features]
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Build model
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, activation='relu', input_shape=(X.shape[1], 1)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1)
    ])

    # Compile
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Train
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)

    # Save model
    model.save(save_path)

    print(f"✅ LSTM traffic model trained and saved to {save_path}")

    return model

# This allows script to run directly
if __name__ == "__main__":
    train_traffic_model()