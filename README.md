# Deteksi Boraks ESP32-CAM

Sistem deteksi kadar boraks menggunakan ESP32-CAM dengan Deep Learning (CNN). Proyek ini mencakup akuisisi dataset, preprocessing gambar, pelatihan model CNN, dan prediksi real-time.

## Status Proyek

✅ **Selesai:**
- Sistem akuisisi dataset dari ESP32-CAM via web interface
- Ekstraksi fitur RGB dan HSV dari gambar
- Segmentasi kertas kurkumin otomatis menggunakan HSV
- Pelatihan model CNN dengan dataset berlabel
- Model trained: `borax_cnn_model.h5` dan `best_borax_model.h5`
- Prediksi dan klasifikasi kadar boraks

## Teknologi

- **Hardware**: ESP32-CAM untuk capture gambar
- **Deep Learning**: TensorFlow/Keras untuk CNN
- **Image Processing**: OpenCV untuk segmentasi HSV
- **ML**: Scikit-learn untuk feature extraction & classification
- **Web**: Python server untuk dataset collection

## Instalasi

```powershell
pip install -r requirements.txt
```

## 1. Akuisisi Dataset

### Menjalankan Web Interface

```powershell
python .\dataset_web\server.py
```

Buka browser: `http://127.0.0.1:8000`

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

### Label PPM (Kadar Boraks)

- 0ppm
- 100ppm
- 250ppm
- 500ppm
- 750ppm
- 1000ppm
- 1250ppm
- 1500ppm
- 1750ppm
- 2000ppm

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
CLASS_NAMES = ["0ppm", "100ppm", "250ppm", "500ppm", "750ppm", 
               "1000ppm", "1250ppm", "1500ppm", "1750ppm", "2000ppm"]
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
├── dataset_web/
│   └── server.py                 # Web interface untuk capture dataset
├── dataset/                      # Dataset folder (struktur: <ppm>/<images>)
├── dataset_range/                # Dataset dengan range ppm
├── dataset_web/                  # Web capture history
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
