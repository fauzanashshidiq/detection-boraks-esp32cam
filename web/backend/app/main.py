import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.model_service import BoraxModelService
from app.schemas import CameraPredictRequest, PredictionResponse
from app.supabase_service import SupabaseHistoryService


settings = get_settings()
model_service = BoraxModelService(settings.model_path, settings.model_class_names)
history_service = SupabaseHistoryService(settings)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_path": str(settings.model_path),
        "model_class_names": settings.model_class_names,
        "esp32_camera_url": settings.esp32_camera_url,
        "supabase_enabled": history_service.enabled,
    }


@app.post("/api/predict/upload", response_model=PredictionResponse)
async def predict_upload(file: UploadFile = File(...)):
    image_bytes = await file.read()
    return _predict_and_store(image_bytes, source="upload")


@app.post("/api/predict/camera", response_model=PredictionResponse)
def predict_camera(payload: CameraPredictRequest | None = None):
    camera_url = str(payload.camera_url) if payload and payload.camera_url else settings.esp32_camera_url
    if not camera_url:
        raise HTTPException(
            status_code=400,
            detail="Camera URL is missing. Set ESP32_CAMERA_URL in .env or send camera_url in request body.",
        )

    try:
        response = requests.get(camera_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to capture ESP32-CAM image: {exc}") from exc

    return _predict_and_store(response.content, source=camera_url)


@app.get("/api/history")
def get_history(limit: int = 50):
    return history_service.list_history(limit=limit)


def _predict_and_store(image_bytes: bytes, source: str):
    try:
        prediction = model_service.predict_jpeg_bytes(image_bytes)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored = history_service.save_detection(image_bytes, prediction, source=source)
    return {
        **prediction,
        "image_url": stored["image_url"],
        "history_id": stored["history_id"],
    }
