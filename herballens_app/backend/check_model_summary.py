import tensorflow as tf
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "herbal_model.keras")

try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    model.summary()
except Exception as e:
    print(f"FAILED: {str(e)}")
