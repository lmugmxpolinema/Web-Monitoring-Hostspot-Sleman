# Laporan Penggabungan Data ONT

## Ringkasan Proses

**Tanggal:** 30 Juli 2025  
**Waktu:** 09:52:43  
**Script:** `merge_onts.py`

## Data Sumber

### Data Existing (onts.json)
- **Jumlah data:** 104 item
- **Format:** JSON dengan struktur yang sudah ada
- **Field:** id, id_pelanggan, name, lokasi, ip, latitude, longitude, status, rto_count

### Data CSV (csvjson.json)
- **Jumlah data:** 285 item
- **Format:** JSON hasil konversi dari CSV
- **Field asli:** no, ID, Nama, Lokasi, Latitude, Longitude, IP, Status

## Konversi Format

### Mapping Field
- `no` → `id` (nomor urut)
- `ID` → `id_pelanggan` (ID pelanggan)
- `Nama` → `name` (nama ONT)
- `Lokasi` → `lokasi` (lokasi ONT)
- `IP` → `ip` (alamat IP)
- `Latitude` → `latitude` (koordinat latitude)
- `Longitude` → `longitude` (koordinat longitude)
- `Status` → `status` (default: "ON")
- Tambahan: `rto_count` (default: 0)

## Hasil Penggabungan

### Statistik
- **Data existing:** 104 item
- **Data baru ditambahkan:** 199 item
- **Data diperbarui:** 86 item
- **Total data akhir:** 303 item

### Detail Perubahan

#### Data yang Diperbarui (86 item)
Data yang sudah ada dengan `id_pelanggan` yang sama diperbarui dengan informasi terbaru dari CSV:

- Baciro RW 10-1 (LM000896)
- Baciro RW 11-1 (XM000362)
- Baciro RW 20-1 (JP001855)
- Bausasran RW 2-1 (XM000406)
- Bausasran RW 3-2 (XM000407)
- Bausasran RW 5-1 (XM000409)
- Bausasran RW 8-1 (XM000412)
- Bausasran RW 9-1 (XM000413)
- Bausasran RW 10-1 (XM000414)
- Bausasran RW 11-1 (XM000415)
- Dan 76 item lainnya...

#### Data Baru yang Ditambahkan (199 item)
Data yang belum ada sebelumnya:

- Baciro (JP000816)
- Baciro RW 1-1 (LM000893)
- Baciro RW 1-2 (LM002054)
- Baciro RW 11 (JP003250)
- Baciro RW 12-1 (XM001239)
- Baciro RW 12-1 (JP000007)
- Baciro RW 13 (XM000463)
- Baciro RW 14-1 (JP000009)
- Baciro RW 15-1 (JP000010)
- Baciro RW 15-1 (JP002293)
- Dan 189 item lainnya...

## File Output

### File Utama
- **onts.json** - Data yang sudah digabung (303 item)

### Backup
- **onts-backup-20250730-095243.json** - Backup data lama sebelum penggabungan

## Validasi Data

### Konversi Koordinat
- Latitude dan longitude dikonversi ke format float
- Data kosong atau invalid diset ke 0
- Format koordinat dipastikan konsisten

### Duplikasi
- Tidak ada data duplikat berdasarkan `id_pelanggan`
- Data yang sama ditimpa dengan informasi terbaru
- ID baru diberikan secara berurutan untuk data baru

### Integritas Data
- Semua field wajib terisi (id_pelanggan, name)
- Data dengan field kosong di-skip
- Format JSON valid dan konsisten

## Rekomendasi

1. **Verifikasi Data:** Periksa beberapa data hasil penggabungan untuk memastikan akurasi
2. **Testing:** Jalankan aplikasi untuk memastikan semua fitur berfungsi dengan data baru
3. **Monitoring:** Perhatikan notifikasi yang muncul saat aplikasi pertama kali dijalankan dengan data baru
4. **Backup:** Simpan backup file dengan aman untuk keperluan rollback jika diperlukan

## Catatan Teknis

- Script menggunakan Python dengan library `json` dan `datetime`
- Encoding UTF-8 digunakan untuk mendukung karakter khusus
- Backup otomatis dibuat sebelum penggabungan
- Log detail tersedia di output console
- Error handling untuk file tidak ditemukan dan format JSON invalid 