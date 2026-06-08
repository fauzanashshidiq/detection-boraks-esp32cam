from pydantic import BaseModel, HttpUrl


class CameraPredictRequest(BaseModel):
    camera_url: HttpUrl | None = None


class PredictionResponse(BaseModel):
    label: str
    confidence: float
    confidence_percent: str
    probabilities: dict[str, float]
    image_url: str | None = None
    history_id: str | None = None


class HistoryItem(BaseModel):
    id: str
    label: str
    confidence: float
    probabilities: dict[str, float] | None = None
    image_url: str | None = None
    source: str | None = None
    created_at: str | None = None
