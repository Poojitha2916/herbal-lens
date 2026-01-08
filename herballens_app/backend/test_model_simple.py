import tensorflow as tf
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "herbal_model.keras")

try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print("RESULT: SUCCESS")
except Exception as e:
    print(f"RESULT: FAILED - {str(e)}")
