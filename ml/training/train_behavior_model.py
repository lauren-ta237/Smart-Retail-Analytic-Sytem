# ml/training/train_behavior_model.py

import tensorflow as tf
from ml.pipelines.data_pipeline import load_behavior_data
from ml.features.feature_engineering import behavior_features
from sklearn.model_selection import train_test_split
import os

def train_behavior_model(epochs=20, batch_size=16, save_path="models/behavior/v1_behavior.keras"):
    """
    Trains a customer behavior model on combined datasets and saves it.

    Args:
        epochs (int): Number of training epochs.
        batch_size (int): Batch size for training.
        save_path (str): Path to save the trained model (.keras format recommended)
    
    Returns:
        model: Trained Keras model
    """
    # Ensure save directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Load and preprocess data
    df = load_behavior_data()
    df = behavior_features(df)

    # Features and target
    X = df[['total_spent', 'visits', 'avg_basket', 'spend_per_visit']].values
    y = df['label'].values

    # Optional: split for validation
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Build model
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(X.shape[1],)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Train model
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val))

    # Save model in native Keras format
    model.save(save_path)

    print(f"✅ Behavior model trained and saved to {save_path}")
    return model

# Allow script to be run directly
if __name__ == "__main__":
    train_behavior_model()