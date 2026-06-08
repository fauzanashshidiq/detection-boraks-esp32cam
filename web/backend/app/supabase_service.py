from datetime import datetime, timezone
from uuid import uuid4

from supabase import Client, create_client

from app.config import Settings


class SupabaseHistoryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client | None = None
        if settings.enable_supabase:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise ValueError("Supabase is enabled but credentials are missing")
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def save_detection(self, image_bytes: bytes, prediction: dict, source: str) -> dict:
        if not self.enabled:
            return {"history_id": None, "image_url": None}

        image_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4()}.jpg"
        self.client.storage.from_(self.settings.supabase_bucket).upload(
            image_name,
            image_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "false"},
        )
        image_url = self.client.storage.from_(self.settings.supabase_bucket).get_public_url(image_name)

        payload = {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "image_url": image_url,
            "source": source,
        }
        result = self.client.table("detections").insert(payload).execute()
        row = result.data[0] if result.data else {}
        return {"history_id": row.get("id"), "image_url": image_url}

    def list_history(self, limit: int = 50) -> list[dict]:
        if not self.enabled:
            return []
        result = (
            self.client.table("detections")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
