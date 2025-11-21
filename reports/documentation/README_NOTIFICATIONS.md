# Fitur Notifikasi dengan Histori

## Overview
Sistem notifikasi dengan histori yang tersimpan dan tidak terhapus telah ditambahkan ke aplikasi monitoring ONT. Fitur ini memungkinkan pengguna untuk melacak semua aktivitas dan perubahan status ONT.

## Fitur Utama

### 1. Histori Notifikasi Permanen
- Semua notifikasi disimpan dalam file `notifications.json`
- Notifikasi tidak akan terhapus dan dapat diakses kembali
- Data tersimpan dengan timestamp lengkap

### 2. Halaman Histori Notifikasi
- URL: `/notifications`
- Menampilkan semua notifikasi dengan urutan terbaru
- Filter berdasarkan tipe notifikasi (Info, Sukses, Peringatan, Error)
- Filter notifikasi yang belum dibaca
- Tombol "Tandai Dibaca" untuk setiap notifikasi

### 3. Tipe Notifikasi
- **Info**: Perubahan status ONT, update data
- **Success**: Penambahan ONT baru
- **Warning**: Penghapusan ONT, status OFF
- **Error**: RTO (Request Timeout) berulang

### 4. Integrasi dengan Halaman Existing
- **Halaman Admin**: Tombol notifikasi dengan badge jumlah notifikasi belum dibaca
- **Halaman Peta**: Tombol "Lihat Semua" di dropdown notifikasi
- **Auto-refresh**: Update jumlah notifikasi setiap 30 detik

## API Endpoints

### GET `/api/notifications`
Mengambil semua notifikasi (diurutkan berdasarkan timestamp terbaru)

### POST `/api/notifications`
Menambah notifikasi baru dari client

### POST `/api/notifications/mark-read/<id>`
Menandai notifikasi sebagai sudah dibaca

### POST `/api/ont-status/<id>`
Update status ONT dan generate notifikasi otomatis

## Struktur Data Notifikasi

```json
{
  "id": 1,
  "message": "ONT baru ditambahkan: ONT 1 (XM000465)",
  "type": "success",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "ont_id": 1,
  "ont_name": "ONT 1",
  "read": false
}
```

## Notifikasi Otomatis

### Penambahan ONT
- Tipe: `success`
- Pesan: "ONT baru ditambahkan: [nama] ([id_pelanggan])"

### Update ONT
- Tipe: `info`
- Pesan: "ONT diperbarui: [nama_lama] ([id_lama]) → [nama_baru] ([id_baru])"

### Penghapusan ONT
- Tipe: `warning`
- Pesan: "ONT dihapus: [nama] ([id_pelanggan])"

### Perubahan Status
- Tipe: `info` (ON) atau `warning` (OFF)
- Pesan: "Status ONT [nama] berubah: [status_lama] → [status_baru]"

### RTO (Request Timeout)
- Tipe: `warning` (1-2 kali) atau `error` (3+ kali)
- Pesan: "ONT [nama] mengalami RTO sebanyak [jumlah] kali"

## Cara Penggunaan

1. **Melihat Histori Notifikasi**:
   - Klik tombol "Notifikasi" di halaman admin
   - Atau klik "Lihat Semua" di dropdown notifikasi di peta

2. **Filter Notifikasi**:
   - Gunakan tombol filter di halaman notifikasi
   - Pilih "Belum Dibaca" untuk melihat notifikasi baru

3. **Menandai Dibaca**:
   - Klik tombol "Tandai Dibaca" pada notifikasi
   - Badge jumlah notifikasi akan berkurang otomatis

4. **Monitoring Real-time**:
   - Notifikasi akan muncul otomatis saat ada perubahan status
   - Jumlah notifikasi belum dibaca ditampilkan di badge

## File yang Ditambahkan/Dimodifikasi

### File Baru
- `notifications.json` - Database notifikasi
- `templates/notifications.html` - Halaman histori notifikasi

### File Dimodifikasi
- `app.py` - Menambah sistem notifikasi dan API endpoints
- `templates/list.html` - Menambah tombol notifikasi dengan badge
- `templates/map.html` - Menambah tombol "Lihat Semua" di dropdown

## Keamanan Data
- Notifikasi disimpan dalam file JSON terpisah
- Backup otomatis saat ada perubahan data ONT
- Data notifikasi tidak terpengaruh oleh operasi backup data ONT

## Performa
- Auto-refresh setiap 30 detik untuk update jumlah notifikasi
- Lazy loading untuk notifikasi lama
- Filter client-side untuk responsivitas 