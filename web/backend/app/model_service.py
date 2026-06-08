from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf


IMG_SIZE = (128, 128)


class BoraxModelService:
    def __init__(self, model_path: Path, class_names: list[str]):
        self.model_path = model_path
        self.class_names = class_names
        self.model = None

    def load(self) -> None:
        if self.model is None:
            resolved_path = self.model_path.resolve()
            if not resolved_path.exists():
                raise FileNotFoundError(f"Model file not found: {resolved_path}")
            self.model = tf.keras.models.load_model(resolved_path)
            output_count = int(self.model.output_shape[-1])
            if output_count != len(self.class_names):
                raise ValueError(
                    "Model output count does not match MODEL_CLASS_NAMES: "
                    f"model has {output_count} outputs, labels has {len(self.class_names)}. "
                    "Use the correct model file or update MODEL_CLASS_NAMES in .env."
                )

    def predict_jpeg_bytes(self, image_bytes: bytes) -> dict:
        self.load()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("Image is not readable")

        crop_bgr = segment_curcumin_paper(image_bgr)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        input_array = crop_rgb.astype("float32") / 255.0
        input_array = np.expand_dims(input_array, axis=0)

        probabilities = self.model.predict(input_array, verbose=0)[0]
        predicted_index = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_index])
        probability_map = {
            label: float(probabilities[index])
            for index, label in enumerate(self.class_names)
        }

        return {
            "label": self.class_names[predicted_index],
            "confidence": confidence,
            "confidence_percent": f"{confidence * 100:.2f}%",
            "probabilities": probability_map,
        }


def segment_curcumin_paper(image_bgr, output_size=IMG_SIZE):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    _, mask = cv2.threshold(saturation, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        crop = center_crop(image_bgr, ratio=0.7)
    else:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 500:
            crop = center_crop(image_bgr, ratio=0.7)
        else:
            x, y, width, height = cv2.boundingRect(largest)
            padding = int(0.05 * max(width, height))
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image_bgr.shape[1], x + width + padding)
            y2 = min(image_bgr.shape[0], y + height + padding)
            crop = image_bgr[y1:y2, x1:x2]

    return cv2.resize(crop, output_size, interpolation=cv2.INTER_AREA)


def center_crop(image_bgr, ratio=0.6):
    height, width = image_bgr.shape[:2]
    crop_width = int(width * ratio)
    crop_height = int(height * ratio)
    x1 = max((width - crop_width) // 2, 0)
    y1 = max((height - crop_height) // 2, 0)
    return image_bgr[y1 : y1 + crop_height, x1 : x1 + crop_width]
