import base64
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import requests


IMG_SIZE = (128, 128)


class BoraxModelService:
    def __init__(
        self,
        model_path: Path,
        class_names: list[str],
        hf_space_id: str = "",
        hf_api_url: str = "",
        hf_api_name: str = "/predict",
        hf_api_timeout: int = 60,
    ):
        self.model_path = model_path
        self.class_names = class_names
        self.hf_space_id = hf_space_id.strip()
        self.hf_api_url = hf_api_url.strip()
        self.hf_api_name = hf_api_name.strip() or "/predict"
        self.hf_api_timeout = hf_api_timeout
        self.model = None

    @property
    def uses_hugging_face(self) -> bool:
        return bool(self.hf_space_id or self.hf_api_url)

    def load(self) -> None:
        if self.uses_hugging_face:
            return

        if self.model is None:
            try:
                import tensorflow as tf
            except ImportError as exc:
                raise RuntimeError(
                    "TensorFlow is not installed. Set HF_SPACE_ID or HF_API_URL "
                    "to use the Hugging Face Space model, or install local requirements."
                ) from exc

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
        if self.uses_hugging_face:
            return self._predict_hugging_face(image_bytes)

        self.load()
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "OpenCV and NumPy are required for local prediction. "
                "Install requirements-local.txt or use HF_SPACE_ID/HF_API_URL."
            ) from exc

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

        return make_prediction_response(
            self.class_names[predicted_index],
            confidence,
            probability_map,
        )

    def _predict_hugging_face(self, image_bytes: bytes) -> dict:
        if self.hf_space_id and not self.hf_api_url:
            client_payload = self._predict_with_gradio_client(image_bytes)
            if client_payload is not None:
                return normalize_hugging_face_output(client_payload)

        data_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
        payload = {"data": [data_url]}

        if self.hf_api_url:
            response_payload = self._post_gradio(self._resolved_hf_api_url(), payload)
        else:
            base_url = f"https://{self.hf_space_id.replace('/', '-')}.hf.space"
            response_payload = self._post_gradio(f"{base_url}/run/predict", payload)

        return normalize_hugging_face_output(response_payload)

    def _predict_with_gradio_client(self, image_bytes: bytes) -> Any | None:
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            return None

        import os
        import tempfile

        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(image_bytes)
            
            client = Client(self.hf_space_id)
            try:
                return client.predict(handle_file(temp_path), api_name=self.hf_api_name)
            except Exception:
                return client.predict(handle_file(temp_path))
        except Exception as e:
            print("Gradio Client error:", e)
            return None
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def _resolved_hf_api_url(self) -> str:
        api_url = self.hf_api_url.rstrip("/")
        if api_url.endswith(".hf.space"):
            return f"{api_url}/run/predict"
        return api_url

    def _post_gradio(self, url: str, payload: dict[str, Any]) -> Any:
        try:
            response = requests.post(url, json=payload, timeout=self.hf_api_timeout)
            if response.status_code == 404 and "/run/predict" in url:
                return self._post_gradio_call(url.replace("/run/predict", "/call/predict"), payload)
            response.raise_for_status()
            response_payload = response.json()
            if isinstance(response_payload, dict) and "event_id" in response_payload:
                return self._read_gradio_event(url, response_payload["event_id"])
            return response_payload
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to call Hugging Face Space: {exc}") from exc

    def _post_gradio_call(self, url: str, payload: dict[str, Any]) -> Any:
        response = requests.post(url, json=payload, timeout=self.hf_api_timeout)
        response.raise_for_status()
        response_payload = response.json()
        event_id = response_payload.get("event_id")
        if not event_id:
            return response_payload
        return self._read_gradio_event(url, event_id)

    def _read_gradio_event(self, url: str, event_id: str) -> Any:
        response = requests.get(f"{url}/{event_id}", timeout=self.hf_api_timeout)
        response.raise_for_status()

        for line in reversed(response.text.splitlines()):
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ").strip()
            if data and data != "null":
                return json.loads(data)

        raise RuntimeError("Hugging Face Space returned an empty prediction event")


def normalize_hugging_face_output(payload: Any) -> dict:
    prediction = unwrap_gradio_payload(payload)
    if not isinstance(prediction, dict):
        raise ValueError(f"Unexpected Hugging Face response format: {prediction!r}")

    label = str(prediction.get("label") or "")
    confidences = prediction.get("confidences") or []

    probability_map = {}
    for item in confidences:
        if not isinstance(item, dict) or "label" not in item:
            continue
        probability_map[str(item["label"])] = float(item.get("confidence") or 0)

    if not label and probability_map:
        label = max(probability_map, key=probability_map.get)

    if not label:
        raise ValueError(f"Hugging Face response did not include a label: {prediction!r}")

    confidence = probability_map.get(label)
    if confidence is None:
        confidence = float(confidences[0].get("confidence") or 0) if confidences else 0.0

    return make_prediction_response(label, float(confidence), probability_map)


def unwrap_gradio_payload(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return unwrap_gradio_payload(payload["data"])
    if isinstance(payload, list) and payload:
        return unwrap_gradio_payload(payload[0])
    return payload


def make_prediction_response(label: str, confidence: float, probabilities: dict[str, float]) -> dict:
    return {
        "label": label,
        "confidence": confidence,
        "confidence_percent": f"{confidence * 100:.2f}%",
        "probabilities": probabilities,
    }


def segment_curcumin_paper(image_bgr, output_size=IMG_SIZE):
    import cv2
    import numpy as np

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
