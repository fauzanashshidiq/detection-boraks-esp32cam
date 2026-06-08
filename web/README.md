# Web App Deteksi Boraks

Folder ini berisi:

- `backend`: FastAPI untuk inference model, capture ESP32-CAM, dan Supabase history.
- `frontend`: React untuk dashboard capture, hasil prediksi, dan history.

## Tahapan Pengerjaan

### 1. Jalankan backend tanpa Supabase

```powershell
cd web/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Cek:

```text
http://localhost:8000/health
```

Di tahap ini `ENABLE_SUPABASE=false`, jadi prediksi jalan tapi history belum disimpan.

Jika ingin melatih ulang model dari backend:

```powershell
python tools/train_range_model.py
```

Lalu ubah `web/backend/.env`:

```env
MODEL_PATH=../../borax_range_model.keras
MODEL_CLASS_NAMES=0ppm,100-250ppm,500-1000ppm,1250-1500ppm,1750-2000ppm
```

Restart backend setelah itu.

### 2. Test prediksi upload

Buka Swagger:

```text
http://localhost:8000/docs
```

Pakai endpoint:

```text
POST /api/predict/upload
```

Upload salah satu gambar dari dataset. Output harus berupa:

- `label`: rentang kadar, misalnya `500-1000ppm`
- `confidence`: angka 0 sampai 1
- `confidence_percent`: persentase
- `probabilities`: peluang tiap kelas

Catatan: model dari notebook terbaru dilatih dengan 5 kelas rentang:

```text
0ppm
100-250ppm
500-1000ppm
1250-1500ppm
1750-2000ppm
```

Kalau response error mengatakan jumlah output model tidak sama dengan `MODEL_CLASS_NAMES`, berarti file `.h5` yang dipakai bukan model dengan label tersebut. Cek `MODEL_PATH` dan daftar label di `web/backend/.env`.

### 3. Test ESP32-CAM

Pastikan ESP32-CAM sudah menyala dan satu WiFi dengan laptop. Dari browser coba:

```text
http://IP-ESP32CAM/capture
```

Kalau gambar muncul, test endpoint:

```text
POST /api/predict/camera
```

Body:

```json
{
  "camera_url": "http://IP-ESP32CAM/capture"
}
```

### 4. Setup Supabase

Di Supabase SQL Editor, jalankan:

```sql
create table if not exists detections (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  confidence numeric not null,
  probabilities jsonb,
  image_url text,
  source text,
  created_at timestamptz default now()
);

create index if not exists detections_created_at_idx
on detections (created_at desc);
```

Buat Storage bucket:

```text
borax-detection-images
```

Untuk demo paling mudah, bucket dibuat public agar gambar bisa tampil di frontend.

Edit `web/backend/.env`:

```env
ENABLE_SUPABASE=true
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_SERVICE_ROLE_KEY=ISI_SERVICE_ROLE_KEY
SUPABASE_BUCKET=borax-detection-images
```

Restart backend setelah `.env` diubah.

### 5. Jalankan frontend

```powershell
cd web/frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Buka:

```text
http://localhost:5173
```

Isi URL ESP32-CAM, lalu klik `Capture & Test`.

## Endpoint Backend

- `GET /health`
- `POST /api/predict/upload`
- `POST /api/predict/camera`
- `GET /api/history`

## Catatan Deployment

Untuk demo lokal, backend dan frontend jalan di laptop, ESP32-CAM satu WiFi, Supabase di cloud. Kalau backend dipindah ke cloud, ESP32-CAM lokal biasanya tidak bisa dicapture langsung dari cloud kecuali pakai tunneling/VPN atau ESP32-CAM dibuat push upload ke backend.
