import numpy as np
from PIL import Image
import requests
import os

# Create dummy image
img = Image.new('RGB', (224, 224), (255, 0, 0))
img.save('test_dummy.jpg')

print("Sending prediction request to http://localhost:5000/predict...")
try:
    with open('test_dummy.jpg', 'rb') as f:
        r = requests.post('http://localhost:5000/predict', files={'image': f})
    
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error connecting to server: {e}")
finally:
    if os.path.exists('test_dummy.jpg'):
        os.remove('test_dummy.jpg')
