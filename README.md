# Deteksi Boraks ESP32-CAM Berbasis Kolorimetri Kurkumin dan Analisis RGB _Deep Learning_

**BoraxSense IoT - Portable Food Safety Screening**

Proyek ini merupakan sistem deteksi boraks portabel berbasis *Internet of Things (IoT)* dan *Deep Learning* yang dirancang untuk membantu proses skrining keamanan pangan secara cepat, praktis, dan objektif.

Sistem menggunakan *ESP32-CAM* untuk mengambil citra kertas indikator kurkumin yang telah bereaksi dengan sampel makanan. Perubahan warna yang terjadi dianalisis menggunakan teknik *Computer Vision* dan diklasifikasikan oleh model *Convolutional Neural Network (CNN)* untuk memperkirakan rentang kadar boraks pada sampel.

Repositori ini mencakup keseluruhan _pipeline_ dari awal hingga akhir, meliputi: akuisisi dataset gambar, preprocessing (ekstraksi fitur RGB dan segmentasi area aktif menggunakan HSV), pelatihan model _Deep Learning_, hingga implementasi antarmuka pengguna berupa _Dashboard Web_ yang modern. Dashboard tersebut memungkinkan teknisi untuk memonitor hasil uji, melihat riwayat deteksi di _cloud_, dan menghasilkan laporan resmi (PDF) secara otomatis.

## Latar Belakang

Keamanan pangan merupakan isu kesehatan masyarakat yang sangat krusial, terutama dengan maraknya penyalahgunaan bahan kimia industri seperti boraks sebagai pengawet makanan. Meskipun metode laboratorium konvensional sangat akurat, sayangnya metode tersebut mahal, rumit, dan tidak bisa digunakan untuk pengujian cepat di lapangan. Untuk mengatasi masalah tersebut, proyek ini memanfaatkan ekstrak kurkumin (kunyit) alami yang bereaksi menjadi kemerahan saat terpapar boraks, yang kemudian digabungkan dengan teknologi kamera dan Kecerdasan Buatan untuk menciptakan alat skrining portabel yang murah, cepat, dan sepenuhnya objektif tanpa bias penglihatan manusia.

## Teknologi Utama

- **Hardware**: ESP32-CAM (OV2640)
- **Machine Learning**: TensorFlow/Keras untuk model CNN
- **Computer Vision**: OpenCV untuk manipulasi citra dan segmentasi warna
- **Backend (API)**: FastAPI (Python) terintegrasi dengan Hugging Face & Supabase (Database)
- **Frontend (UI)**: React.js (Vite) lengkap dengan TailwindCSS dan fitur ekspor PDF (jsPDF)

## Instalasi

```powershell
pip install -r requirements.txt
```

## 1. Akuisisi Dataset

### Menjalankan Web Interface

Web interface terbaru untuk akuisisi dataset dan dashboard lengkap sekarang berada di dalam folder `web/`.
Silakan baca panduan lengkapnya di `web/README.md`.

(Script lama `dataset_web/server.py` sudah usang dan digantikan oleh arsitektur Frontend-Backend yang baru).

Langkah-langkah:

1. Isi URL snapshot ESP32-CAM
2. Pilih label kadar ppm (0-2000ppm)
3. Tekan **Ambil & Simpan Gambar**
4. Jika hasil kurang bagus, tekan **Hapus** untuk menghapus file

**Setup ESP32-CAM:**

- Upload sketch: `esp32cam_capture_server.ino`
- Lihat IP DHCP dari Serial Monitor Arduino IDE
- Gunakan URL format: `http://<IP_DHCP_ESP32>/capture`

Contoh: `http://192.168.1.27/capture`

### Struktur Dataset

```
dataset\<label_ppm>\<label_ppm>_<tanggal>_<jam>.jpg
```

Contoh:

```
dataset\20ppm\20ppm_20260606_143012_125.jpg
```

### Label PPM (Kadar Boraks - Dataset Range)

Dataset terbaru dikelompokkan berdasarkan rentang (range) kadar:

- 0ppm
- 100-250ppm
- 500-1000ppm
- 1250-1500ppm
- 1750-2000ppm

## 2. Ekstraksi Fitur RGB

### Ekstraksi RGB Standar

Ekstrak rata-rata RGB semua gambar:

```powershell
python .\rgb_extract.py
```

Hasil disimpan ke: `rgb_features.csv`

**Opsi crop** (ambil area tengah):

```powershell
python .\rgb_extract.py --crop 0.4
```

### Ekstraksi Fitur Kertas Kurkumin

Ekstraksi khusus untuk kertas kurkumin dengan background diabaikan:

```powershell
python .\extract_curcumin_rgb.py
```

Hasil: `curcumin_rgb_features.csv`

**Mode debug** (lihat visualisasi mask):

```powershell
python .\extract_curcumin_rgb.py --debug-masks
```

**Mask warna:**

- 🔴 **Merah**: area reaksi boraks (RGB utama)
- 🟡 **Kuning**: warna dasar kertas kurkumin (diabaikan)
- ⚫ **Abu-abu**: area kertas kurkumin lainnya

## 3. Pelatihan Model

### Pelatihan CNN

Jalankan training dengan dataset yang sudah disiapkan:

```powershell
python .\train.py
```

**Fitur:**

- Preprocessing gambar (segmentasi HSV, crop center 60%)
- Data augmentation (rotasi, flip, brightness)
- Model CNN dengan batch normalization
- Validasi split 80:20
- Menyimpan best model ke `best_borax_model.h5`
- Logging training ke `training_log.csv`

**Parameter training:**

```python
CLASS_NAMES = ["0ppm", "100-250ppm", "500-1000ppm", "1250-1500ppm", "1750-2000ppm"]
IMG_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 200
```

### Training Log

Log tersimpan di `training_log.csv` dengan metrik:

- accuracy, loss
- val_accuracy, val_loss

## 4. Prediksi & Inference

### Prediksi Single Image

```powershell
python .\predict.py --image <path_to_image> --model borax_cnn_model.h5
```

**Opsi model:**

- `borax_cnn_model.h5` (model utama)
- `best_borax_model.h5` (best checkpoint)

**Output:**

- Klasifikasi kadar boraks
- Confidence score
- Visualisasi gambar hasil segmentasi

## Struktur File

```
.
├── train.py                      # Training CNN model
├── predict.py                    # Inference & prediction
├── rgb_extract.py                # Ekstraksi fitur RGB
├── extract_curcumin_rgb.py       # Ekstraksi RGB kertas kurkumin
├── esp32cam_capture_server.ino   # Sketch ESP32-CAM
├── web/
│   ├── frontend/                 # React Web Dashboard & Capture
│   └── backend/                  # FastAPI & ML Inference API
├── dataset/                      # Dataset folder lama
├── dataset_range/                # Dataset terbaru dengan range ppm
├── curcumin_masks/               # Debugging masks dari ekstraksi
├── borax_cnn_model.h5            # Trained CNN model
├── best_borax_model.h5           # Best checkpoint model
├── rgb_features.csv              # Ekstraksi RGB hasil
├── training_log.csv              # Log pelatihan
├── borax_model_training.ipynb    # Jupyter notebook training
└── requirements.txt              # Dependencies

```

## Dependencies

Lihat `requirements.txt`:

```
tensorflow>=2.10,<3
opencv-python>=4.8
numpy>=1.23
pandas>=1.5
matplotlib>=3.7
seaborn>=0.12
scikit-learn>=1.2
```

## Workflow Lengkap

1. **Dataset Collection** → Gunakan web interface untuk capture dari ESP32-CAM
2. **Feature Extraction** → Ekstraksi RGB menggunakan `rgb_extract.py` atau `extract_curcumin_rgb.py`
3. **Training** → Jalankan `train.py` untuk pelatihan model CNN
4. **Inference** → Gunakan `predict.py` untuk prediksi pada gambar baru

## Notes

- Model menggunakan segmentasi HSV untuk mengisolasi kertas kurkumin
- CNN di-train dengan data augmentation untuk robustness
- Setiap prediksi melakukan preprocessing otomatis (segmentasi + normalisasi)
- Best model disimpan berdasarkan validation accuracy

## Tim Pengembang

| Nama                      | NIM        |
| ------------------------- | ---------- |
| NANDA ZACKY FIRMANSYAH    | 1237050059 |
| MUHAMMAD FAUZAN ASHSHIDIQ | 1237050051 |
| NISRINA ALIYA THARIFAH    | 1237050044 |
