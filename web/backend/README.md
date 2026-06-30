# Borax Detection Backend

FastAPI backend untuk mengambil gambar dari upload atau ESP32-CAM, menjalankan prediksi boraks, dan menyimpan riwayat deteksi ke Supabase. Untuk deployment Vercel, prediksi dipanggil ke Hugging Face Space agar package serverless tetap ringan.

## Setup

```powershell
cd web/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Isi `.env` sesuai kebutuhan. Supabase boleh dikosongkan dulu saat testing lokal.

## Mode Hugging Face Space

Gunakan mode ini untuk Vercel:

```env
HF_SPACE_ID=Hara25/detection-boraks-esp32cam
MODEL_CLASS_NAMES=0ppm,100ppm,250ppm,500ppm,750ppm,1000ppm,1250ppm,1500ppm,1750ppm,2000ppm
```

Jika Space menggunakan URL endpoint khusus, isi `HF_API_URL` langsung, misalnya URL `/run/predict`. Output Space `{"label":"0ppm","confidences":[...]}` akan dinormalisasi menjadi response backend lama: `label`, `confidence`, `confidence_percent`, dan `probabilities`.

## Mode model lokal

Untuk menjalankan model Keras `.h5` secara lokal, install dependency lengkap:

```powershell
pip install -r requirements-local.txt
```

Kosongkan `HF_SPACE_ID` dan `HF_API_URL`, lalu isi `MODEL_PATH`.

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
