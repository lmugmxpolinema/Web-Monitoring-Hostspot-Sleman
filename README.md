<div align="center">

# Web Monitoring Hotspot Sleman

Sistem monitoring terpadu untuk memantau status ONT dan pengguna hotspot MikroTik di wilayah Sleman.

</div>

## Ringkasan

Aplikasi ini dibangun dengan Flask untuk membantu tim operasional memonitor perangkat ONT, riwayat pengguna hotspot, dan notifikasi gangguan secara real-time. Layanan web dapat dijalankan berdampingan dengan skrip monitoring yang melakukan ping berkala ke setiap ONT serta menarik data aktif dari MikroTik melalui RouterOS API.

## Fitur Utama

- **Peta interaktif**: Pemetaan ONT pada halaman `map.html` dengan status yang diperbarui dari cache monitoring.
- **Dashboard & analitik**: Statistik ONT online/offline, jumlah user aktif, grafik histori, dan halaman analitik berbasis data `runtime/user_log.json`.
- **Manajemen ONT**: CRUD perangkat melalui halaman admin yang dilindungi login `flask-login`.
- **Manajemen notifikasi**: CRUD notifikasi, backup otomatis, serta pemulihan dari folder `runtime/backups`.
- **Rekap gangguan**: Deteksi perubahan status ONT untuk mencatat outage start/end dan merangkum frekuensi gangguan.
- **Integrasi MikroTik**: Endpoint dan skrip untuk mengambil daftar user aktif via `routeros_api`.

## Arsitektur Singkat

- `app.py` menjalankan aplikasi Flask, API publik, halaman HTML (Jinja2), autentikasi admin, dan logika penyimpanan JSON.
- Direktori `templates/` dan `static/` menyajikan UI dashboard, peta, formulir admin, dan halaman analitik.
- Direktori `data/` berisi data sumber (mis. `wifi_sleman.json`, `onts.json`, `notifications.json`). Direktori `runtime/` menyimpan cache, log historis, serta backup.
- Skrip di `scripts/` (mis. `ping_check.py`) dijalankan terpisah untuk memutakhirkan cache status ONT dan log user MikroTik.

## Prasyarat

- Python 3.10+ (dikembangkan dan diuji pada Windows 10/11 dengan PowerShell).
- Git terpasang untuk melakukan clone repository.
- Akses ke router MikroTik dan kredensial API valid (untuk fitur monitoring hotspot).
- Pip dan virtual environment (disarankan) untuk isolasi dependensi.

## Setup di Lingkungan Baru

1. **Clone repository**

   ```powershell
   git clone https://github.com/lmugmxpolinema/Web-Monitoring-Hostspot-Sleman.git
   cd Web-Monitoring-Hostspot-Sleman
   ```

   > Bila bekerja di folder khusus, sesuaikan path tujuan sebelum menjalankan `git clone`.

2. **Buat dan aktifkan virtual environment (disarankan)**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Untuk Linux/macOS:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instal dependensi Python**

   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Konfigurasi awal**

   - Salin data contoh: pastikan berkas di `data/` (`wifi_sleman.json`, `onts.json`, dsb.) tersedia. Jika mengambil dari lingkungan lain, copy ke folder yang sama.
   - Ubah kredensial MikroTik di `app.py` dan `scripts/ping_check.py` (`MIKROTIK_IP`, `MIKROTIK_USER`, dll.).
   - Ganti `app.secret_key` dan hash admin default (`ADMIN_PASSWORD_HASH`) sebelum deploy ke produksi.
   - Simpan konfigurasi sensitif di variabel lingkungan bila memungkinkan.

5. **Jalankan aplikasi web**

   ```powershell
   python app.py
   ```

   Aplikasi akan aktif di `http://127.0.0.1:8000`. Login admin standar: username `admin`, password `admin2025` (ubah segera).

6. **Jalankan layanan monitoring ping & MikroTik**
   Gunakan terminal terpisah setelah server Flask aktif:

   ```powershell
   python scripts\ping_check.py
   ```

   Skrip ini memperbarui `runtime/status_cache.json`, `runtime/history.json`, dan `runtime/user_log.json` secara periodik.

7. **Verifikasi dengan pengujian otomatis**

   ```powershell
   python -m pytest
   ```

   Tambahkan paket `pytest` secara manual (`pip install pytest`) bila belum terpasang.

8. **Men-deploy atau menjalankan ulang**
   - Simpan environment variables (mis. `FLASK_ENV`, `SECRET_KEY`, kredensial MikroTik) di task runner atau service manager.
   - Untuk menjalankan ulang setelah reboot, aktifkan virtual environment dan ulangi langkah 5-6.

## Struktur Folder

```
hotspot_sleman/
├── app.py
├── data/
│   ├── wifi_sleman.json         # Data ONT utama untuk monitoring
│   ├── onts.json                # Data master (hasil sinkronisasi CSV)
│   └── notifications.json       # Notifikasi aktif
├── runtime/
│   ├── status_cache.json        # Cache status ONT dari skrip ping
│   ├── history.json             # Riwayat jumlah user hotspot
│   └── backups/                 # Backup notifikasi & ONT
├── scripts/
│   ├── ping_check.py            # Ping ONT + log user MikroTik
│   └── convert_csv_to_main.py   # Konversi CSV -> onts.json
├── templates/                   # Halaman dashboard, map, admin, dsb.
└── tests/                       # Pytest untuk logika notifikasi & realtime
```

## Konfigurasi Penting

- **Kredensial MikroTik**: Ubah `MIKROTIK_*` di `app.py` dan `scripts/ping_check.py` sesuai lingkungan Anda.
- **Secret Flask**: Ganti `app.secret_key` dengan nilai unik melalui variabel lingkungan sebelum deployment.
- **Admin default**: Perbarui hash password admin di `app.py` (`ADMIN_PASSWORD_HASH`) bila kata sandi diubah.
- **Interval monitoring**: Atur `PING_INTERVAL` dan `MIKROTIK_INTERVAL` di `scripts/ping_check.py`.

## Endpoint API (Ringkas)

- `GET /api/onts` – Daftar ONT lengkap beserta status saat ini.
- `GET /api/history` – Riwayat jumlah user hotspot (untuk grafik).
- `POST /api/record-history` – Mencatat jumlah user aktif terbaru (dipanggil skrip monitoring).
- `POST /api/log-active-users` – Menyimpan detail user MikroTik per batch.
- `GET /api/analytics-data` – Ringkasan data log untuk halaman analitik.
- `GET/POST /api/notifications` – Ambil atau tambahkan notifikasi baru.
- `POST /api/notifications/mark-read/<id>` – Menandai notifikasi sebagai dibaca.
- `POST /api/notifications/clear-all` – Mengosongkan notifikasi (dengan backup otomatis).
- `GET /api/outages` – Daftar outage ONT; `GET /api/outages/summary` untuk rekap.

## Data & Backup

- Data sumber disimpan dalam format JSON untuk memudahkan sinkronisasi dengan sistem eksternal.
- Setiap penambahan/penyuntingan ONT memicu backup otomatis ke `runtime/backups/onts-*.json`.
- Notifikasi akan disalin ke backup setiap ada perubahan, menjaga pemulihan bila file utama korup.
- Skrip `convert_csv_to_main.py` menyediakan workflow konversi `data/csvjson.json` menjadi `onts.json` sekaligus backup lama.

## Pengembangan & Testing

- Jalankan pengujian otomatis dengan `python -m pytest` (butuh `pytest` dalam environment).
- Gunakan `scripts/check_duplicates.py` untuk memvalidasi data pelanggan sebelum sinkronisasi.
- Dokumentasi historis dan analisis pembaruan tersedia di `runtime/reports/`.

## Troubleshooting

- Pastikan layanan Flask aktif sebelum menjalankan `scripts/ping_check.py`, karena skrip akan memanggil API lokal.
- Jika koneksi MikroTik gagal, periksa port, firewall, dan kredensial; skrip akan tetap melakukan ping ONT walau API MikroTik tidak tersedia.
- File JSON yang korup biasanya otomatis dipulihkan dari backup; cek folder `runtime/backups/` bila data hilang.

## Roadmap Ide Lanjutan

- Migrasi kredensial dan konfigurasi sensitif ke variabel lingkungan atau file `.env`.
- Tambahkan sistem role-based access dan audit trail untuk multi-user.
- Implementasi notifikasi otomatis (email/Telegram) ketika ONT mengalami outage berulang.

---

Untuk catatan warna, implementasi, dan laporan testing terperinci, lihat direktori `COLOR_*`, `runtime/reports/`, serta dokumen troubleshooting lainnya di repo.
