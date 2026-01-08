import tensorflow as tf
import numpy as np
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "herbal_model.keras")

print(f"Loading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
print("Model loaded successfully.")

# Create dummy input
dummy_input = np.random.rand(1, 224, 224, 3).astype(np.float32) * 255

print("Running prediction...")
try:
    preds = model(dummy_input, training=False)
    print("Prediction SUCCESS!")
    print(f"Output shape: {preds.shape}")
except Exception as e:
    print(f"Prediction FAILED: {e}")
