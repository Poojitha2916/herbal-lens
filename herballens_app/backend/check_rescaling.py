import tensorflow as tf
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "herbal_model.keras")

try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    has_rescaling = any("rescaling" in layer.name.lower() for layer in model.layers)
    print(f"Has rescaling layer: {has_rescaling}")
    for layer in model.layers[:10]:
        print(f"Layer: {layer.name}, Type: {type(layer)}")
except Exception as e:
    print(f"FAILED: {str(e)}")
