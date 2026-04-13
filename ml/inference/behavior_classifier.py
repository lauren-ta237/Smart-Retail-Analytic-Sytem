import tensorflow as tf
import numpy as np
import os

model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'behavior', 'v1.h5')
model = tf.keras.models.load_model(model_path)

def predict_behavior(time_spent, zone_visits, interactions):
    # Note: Ensure the input features match the 4 inputs expected by the trained model
    prediction = model.predict(np.array([[time_spent, zone_visits, interactions]]))
    return int(prediction[0][0] > 0.5)