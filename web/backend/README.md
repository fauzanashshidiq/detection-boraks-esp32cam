# Borax Detection Backend

FastAPI backend untuk mengambil gambar dari upload atau ESP32-CAM, menjalankan prediksi model Keras `.h5`, dan menyimpan riwayat deteksi ke Supabase.

## Setup

```powershell
cd web/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Isi `.env` sesuai kebutuhan. Supabase boleh dikosongkan dulu saat testing lokal.

## Train/export model

Jika ingin melatih ulang model dari backend:

```powershell
python tools/train_range_model.py
```

Setelah selesai, ubah `.env`:

```env
MODEL_PATH=../../borax_range_model.keras
MODEL_CLASS_NAMES=0ppm,100-250ppm,500-1000ppm,1250-1500ppm,1750-2000ppm
```

Restart backend setelah `.env` diubah.

## Run

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoint

- `GET /health`
- `POST /api/predict/upload`
- `POST /api/predict/camera`
- `GET /api/history`

`/api/predict/camera` menerima JSON:

```json
{
  "camera_url": "http://192.168.1.20/capture"
}
```
