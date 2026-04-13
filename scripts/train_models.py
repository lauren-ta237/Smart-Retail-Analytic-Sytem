# run it like this python scripts/train_models.py
# This script is responsible for training machine learning models
import sys
import os

# Ensure the ml folder is in the Python path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ml.training.train_traffic_model import train_traffic_model
    from ml.training.train_behavior_model import train_behavior_model
except ImportError as e:
    print("Error importing training modules:", e)
    sys.exit(1)

def main():
    print("Training traffic prediction model...")
    # Call with dataset path if required
    train_traffic_model()

    print("Training customer behavior model...")
    train_behavior_model()

    print("All models trained successfully!")

if __name__ == "__main__":
    main()