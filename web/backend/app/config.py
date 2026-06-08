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
            "0ppm,100-250ppm,500-1000ppm,1250-2000ppm",
        ).split(",")
        if name.strip()
    ]
    esp32_camera_url: str = os.getenv("ESP32_CAMERA_URL", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_bucket: str = os.getenv("SUPABASE_BUCKET", "borax-detection-images")
    enable_supabase: bool = os.getenv("ENABLE_SUPABASE", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
