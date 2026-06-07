import argparse
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf


CLASS_NAMES = [
    "0ppm",
    "100ppm",
    "250ppm",
    "500ppm",
    "750ppm",
    "1000ppm",
    "1250ppm",
    "1500ppm",
    "1750ppm",
    "2000ppm",
]

IMG_SIZE = (128, 128)
DEFAULT_MODEL_PATH = "borax_cnn_model.h5"


def segment_curcumin_paper(image_bgr, output_size=IMG_SIZE):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([8, 35, 35], dtype=np.uint8)
    upper = np.array([70, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 100:
            x, y, w, h = cv2.boundingRect(largest)
            crop = image_bgr[y : y + h, x : x + w]
            crop_mask = mask[y : y + h, x : x + w]
            neutral = np.full_like(crop, 255)
            crop = np.where(crop_mask[..., None] > 0, crop, neutral)
        else:
            crop = center_crop(image_bgr)
    else:
        crop = center_crop(image_bgr)

    return cv2.resize(crop, output_size, interpolation=cv2.INTER_AREA)


def center_crop(image_bgr, ratio=0.6):
    height, width = image_bgr.shape[:2]
    crop_w = int(width * ratio)
    crop_h = int(height * ratio)
    x1 = max((width - crop_w) // 2, 0)
    y1 = max((height - crop_h) // 2, 0)
    return image_bgr[y1 : y1 + crop_h, x1 : x1 + crop_w]


def load_model(model_path=DEFAULT_MODEL_PATH):
    return tf.keras.models.load_model(model_path)


def predict_image(image_path, model_path=DEFAULT_MODEL_PATH, model=None):
    if model is None:
        model = load_model(model_path)

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise FileNotFoundError(f"Image not found or unreadable: {image_path}")

    crop_bgr = segment_curcumin_paper(image_bgr)
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    image_array = crop_rgb.astype("float32") / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    probabilities = model.predict(image_array, verbose=0)[0]
    predicted_index = int(np.argmax(probabilities))
    label = CLASS_NAMES[predicted_index]
    confidence = float(probabilities[predicted_index])
    return label, confidence


def main():
    parser = argparse.ArgumentParser(description="Predict borax concentration from one image.")
    parser.add_argument("image_path", help="Path to image file")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, help="Path to .h5 model")
    args = parser.parse_args()

    label, confidence = predict_image(Path(args.image_path), model_path=args.model)
    print(f"Prediction: {label}")
    print(f"Confidence: {confidence:.4f}")


if __name__ == "__main__":
    main()
