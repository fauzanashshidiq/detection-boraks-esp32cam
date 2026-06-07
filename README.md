# Deteksi Boraks Dataset Capture

Web kecil ini dipakai untuk mengumpulkan gambar dari ESP32-CAM dan menyimpan dataset berdasarkan 10 variasi label kadar ppm.

## Menjalankan web

```powershell
python .\dataset_web\server.py
```

Buka:

```text
http://127.0.0.1:8000
```

Isi URL snapshot ESP32-CAM, pilih label kadar ppm, lalu tekan **Ambil & Simpan Gambar**.
Jika hasil capture kurang bagus, tekan tombol **Hapus** pada riwayat sesi untuk menghapus file dari folder dataset.

Default URL di web hanya contoh. Karena ESP32-CAM memakai DHCP dari WiFi/router, lihat IP dari Serial Monitor Arduino IDE setelah upload sketch, lalu isi URL dengan format:

```text
http://IP_DHCP_ESP32/capture
```

Contoh:

```text
http://192.168.1.27/capture
```

## Struktur hasil gambar

Gambar akan disimpan otomatis ke folder:

```text
dataset\<label_ppm>\<label_ppm>_<tanggal>_<jam>.jpg
```

Contoh:

```text
dataset\20ppm\20ppm_20260606_143012_125.jpg
```

## Label ppm

- 0ppm
- 10ppm
- 20ppm
- 30ppm
- 40ppm
- 50ppm
- 60ppm
- 70ppm
- 80ppm
- 90ppm

## Ekstraksi RGB

Ekstrak rata-rata RGB semua gambar dataset ke CSV:

```powershell
python .\extract_rgb.py
```

Hasilnya tersimpan di:

```text
rgb_features.csv
```

Jika ingin hanya mengambil area tengah gambar, gunakan opsi crop. Contoh crop 40% area tengah:

```powershell
python .\extract_rgb.py --crop 0.4
```

Ekstraksi khusus kertas kurkumin, dengan background dan kuning dasar diabaikan:

```powershell
python .\extract_curcumin_rgb.py
```

Hasilnya tersimpan di:

```text
curcumin_rgb_features.csv
```

Untuk mengecek area mana yang terdeteksi, jalankan:

```powershell
python .\extract_curcumin_rgb.py --debug-masks
```

Mask warna:

- Merah: area reaksi yang dipakai sebagai RGB utama
- Kuning: warna dasar kertas kurkumin yang diabaikan
- Abu-abu: area kertas kurkumin lain
