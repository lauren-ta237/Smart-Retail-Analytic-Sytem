import tensorflow as tf
import numpy as np

model = tf.keras.models.load_model("models/traffic/v1_lstm.h5")

def predict(sequence):
    sequence = np.array(sequence).reshape(1, len(sequence), 1)
    return model.predict(sequence)[0][0]

# Example: last 5 time steps
print(predict([100, 120, 130, 125, 140]))