# Borax Detection Frontend

React frontend untuk capture gambar ESP32-CAM, upload gambar manual, menampilkan hasil prediksi, membaca riwayat, dan mengekspor laporan CSV.

## Setup

```powershell
cd web/frontend
npm install
Copy-Item .env.example .env
```

## Run

```powershell
npm run dev
```

Pastikan backend berjalan di `http://localhost:8000`.

## Deploy Vercel

Set `VITE_API_BASE_URL` ke URL backend FastAPI yang sudah dideploy, lalu deploy folder `web/frontend` sebagai project Vercel terpisah.
