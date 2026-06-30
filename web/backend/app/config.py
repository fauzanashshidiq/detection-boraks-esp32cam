from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Borax Detection API")
    model_path: Path = Path(os.getenv("MODEL_PATH", "../../borax_cnn_model.h5"))
    model_class_names: list[str] = [
        name.strip()
        for name in os.getenv(
            "MODEL_CLASS_NAMES",
            "0ppm,100ppm,250ppm,500ppm,750ppm,1000ppm,1250ppm,1500ppm,1750ppm,2000ppm",
        ).split(",")
        if name.strip()
    ]
    esp32_camera_url: str = os.getenv("ESP32_CAMERA_URL", "")
    hf_space_id: str = os.getenv("HF_SPACE_ID", "")
    hf_api_url: str = os.getenv("HF_API_URL", "")
    hf_api_name: str = os.getenv("HF_API_NAME", "/predict_borax")
    hf_api_timeout: int = int(os.getenv("HF_API_TIMEOUT", "60"))
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_bucket: str = os.getenv("SUPABASE_BUCKET", "borax-detection-images")
    enable_supabase: bool = os.getenv("ENABLE_SUPABASE", "false").lower() == "true"
    enable_memory_history: bool = os.getenv("ENABLE_MEMORY_HISTORY", "true").lower() == "true"
    memory_history_limit: int = int(os.getenv("MEMORY_HISTORY_LIMIT", "100"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
