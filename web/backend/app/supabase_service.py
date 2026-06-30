import base64
from datetime import datetime, timezone
from uuid import uuid4

from supabase import Client, create_client

from app.config import Settings


class SupabaseHistoryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client | None = None
        self.memory_history: list[dict] = []
        if settings.enable_supabase:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise ValueError("Supabase is enabled but credentials are missing")
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def save_detection(self, image_bytes: bytes, prediction: dict, source: str) -> dict:
        if not self.enabled:
            return self._save_memory_detection(image_bytes, prediction, source)

        image_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4()}.jpg"
        try:
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
            return {
                "history_id": row.get("id"),
                "image_url": image_url,
                "created_at": row.get("created_at"),
                "source": source,
            }
        except Exception:
            return self._save_memory_detection(image_bytes, prediction, source)

    def list_history(self, limit: int = 50) -> list[dict]:
        if not self.enabled:
            return self.memory_history[:limit]
        result = (
            self.client.table("detections")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def _save_memory_detection(self, image_bytes: bytes, prediction: dict, source: str) -> dict:
        if not self.settings.enable_memory_history:
            return {"history_id": None, "image_url": None, "created_at": None, "source": source}

        history_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        image_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
        row = {
            "id": history_id,
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "probabilities": prediction.get("probabilities"),
            "image_url": image_url,
            "source": source,
            "created_at": created_at,
        }
        self.memory_history.insert(0, row)
        del self.memory_history[self.settings.memory_history_limit :]
        return {
            "history_id": history_id,
            "image_url": image_url,
            "created_at": created_at,
            "source": source,
        }
