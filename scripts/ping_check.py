import json
import time
import platform
import subprocess
import requests
import os
from pathlib import Path
try:
    import routeros_api
    ROUTEROS_AVAILABLE = True
except Exception:
    ROUTEROS_AVAILABLE = False
    print("⚠️  Warning: 'routeros_api' module not installed — MikroTik features will be disabled.")

MIKROTIK_IP = '202.169.224.15'
MIKROTIK_PORT = 1500
MIKROTIK_USER = 'cleon'
MIKROTIK_PASS = 'cleon'

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
STATUS_CACHE_PATH = BASE_DIR / 'status_cache.json'

FLASK_SERVER_URL = 'http://127.0.0.1:8000'
PING_INTERVAL = 30
MIKROTIK_INTERVAL = 300

def ping(ip):
    """
    Ping function yang kompatibel dengan Windows dan Linux.
    """
    try:
        if platform.system().lower() == "windows":
            command = f"ping -n 1 -w 1000 {ip}"
        else:
            command = f"ping -c 1 -W 1 {ip}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        if platform.system().lower() == "windows":
            return "Reply from" in result.stdout or "bytes=" in result.stdout
        else:
            return result.returncode == 0
    except Exception as e:
        print(f"Error saat ping {ip}: {e}")
        return False

# FUNGSI LAMA (TETAP ADA)
def get_mikrotik_hotspot_active_count():
    """Menghubungkan ke MikroTik via API dan menghitung user aktif."""
    if not ROUTEROS_AVAILABLE:
        print("routeros_api not available; skipping MikroTik hotspot count")
        return None
    try:
        connection = routeros_api.RouterOsApiPool(
            MIKROTIK_IP,
            username=MIKROTIK_USER,
            password=MIKROTIK_PASS,
            port=MIKROTIK_PORT,
            plaintext_login=True
        )
        api = connection.get_api()
        active_users_list = api.get_resource('/ip/hotspot/active').get(server='hs-bridge-csr-sleman')
        user_count = len(active_users_list)
        connection.disconnect()
        return user_count
    except Exception as e:
        print(f"GAGAL (get_mikrotik_hotspot_active_count): {e}")
        return None

# FUNGSI BARU (TAMBAHAN)
def get_mikrotik_active_users_detail():
    """Menghubungkan ke MikroTik dan mengambil data detail semua user aktif."""
    try:
        if not ROUTEROS_AVAILABLE:
            print("routeros_api not available; skipping MikroTik active users detail")
            return None
        print(f"Mengambil detail user dari MikroTik di {MIKROTIK_IP}:{MIKROTIK_PORT}...")
        connection = routeros_api.RouterOsApiPool(
            MIKROTIK_IP,
            username=MIKROTIK_USER,
            password=MIKROTIK_PASS,
            port=MIKROTIK_PORT,
            plaintext_login=True
        )
        api = connection.get_api()
        
        # Mengambil seluruh daftar user aktif beserta detailnya
        active_users_list = api.get_resource('/ip/hotspot/active').get(server='hs-bridge-csr-sleman')
        connection.disconnect()
        
        # Membersihkan data, hanya mengambil yang penting untuk log
        cleaned_users = []
        for user in active_users_list:
            cleaned_users.append({
                'ip': user.get('address', '-'),
                'mac': user.get('mac-address', '-'),
                'uptime': user.get('uptime', '0s'),
                'bytes_in': user.get('bytes-in', 0),
                'bytes_out': user.get('bytes-out', 0)
            })
        print(f"BERHASIL: Ditemukan detail untuk {len(cleaned_users)} user.")
        return cleaned_users

    except Exception as e:
        print(f"GAGAL (get_mikrotik_active_users_detail): {e}")
        return None

# FUNGSI LAMA (TETAP ADA)
def update_ont_statuses():
    """Melakukan ping ke semua ONT dan mengupdate statusnya.

    Untuk monitoring, ambil data sumber dari `onts.json` (read-only).
    Perubahan status tidak disimpan kembali ke file sumber untuk menghindari
    menimpa data master; jika diperlukan, perubahan tetap bisa ditulis ke
    `onts.json` atau file lain secara eksplisit.
    """
    try:
        # Baca dari data/wifi_sleman.json sebagai sumber IP untuk pengecekan
        with open(DATA_DIR / "wifi_sleman.json", "r", encoding='utf-8') as f:
            onts = json.load(f)

        print(f"Memulai ping ke {len(onts)} ONT...")
        updated = []
        for ont in onts:
            ip = ont.get('ip', '').strip()
            if not ip:
                updated.append({**ont, 'status': 'UNKNOWN'})
                continue
            if ping(ip):
                updated.append({**ont, 'status': 'ON'})
            else:
                updated.append({**ont, 'status': 'OFF'})

        # Hanya laporkan hasil (tidak menimpa file master `onts.json`)
        print("Hasil pengecekan (sample 5):", updated[:5])

        # Tulis cache status agar web app dapat menggabungkan status terbaru
        try:
            status_cache = []
            for item in updated:
                status_cache.append({
                    'id': item.get('id'),
                    'ip': item.get('ip'),
                    'status': item.get('status')
                })
            # atomic write
            tmp = STATUS_CACHE_PATH.with_name('.tmp-status_cache.json')
            with open(tmp, 'w', encoding='utf-8') as tf:
                json.dump(status_cache, tf, indent=2, ensure_ascii=False)
                tf.flush()
                try:
                    os.fsync(tf.fileno())
                except Exception:
                    pass
            os.replace(tmp, STATUS_CACHE_PATH)
            print(f"Status cache written ({len(status_cache)} entries) to {STATUS_CACHE_PATH.name}")
        except Exception as e:
            print(f"Gagal menulis status_cache.json: {e}")
    except Exception as e:
        print(f"Error saat memperbarui status ONT: {e}")

def main():
    print("🚀 Memulai Layanan Monitoring (Ping ONT & User MikroTik)...")
    last_ping_check = 0
    last_mikrotik_check = 0
    while True:
        try:
            current_time = time.time()

            if current_time - last_ping_check >= PING_INTERVAL:
                print(f"\n--- Menjalankan Pengecekan Ping ONT ({time.ctime()}) ---")
                update_ont_statuses()
                last_ping_check = current_time

            if current_time - last_mikrotik_check >= MIKROTIK_INTERVAL:
                print(f"\n--- Menjalankan Pengecekan User MikroTik ({time.ctime()}) ---")
                
                # CUKUP PANGGIL FUNGSI DETAIL SATU KALI
                users_detail = get_mikrotik_active_users_detail()
                
                if users_detail is not None:
                    # Hitung jumlah user dari data detail yang sudah didapat
                    user_count = len(users_detail)
                    
                    # 1. Kirim JUMLAH user untuk grafik di dashboard
                    try:
                        payload_count = {'users': user_count}
                        requests.post(f"{FLASK_SERVER_URL}/api/record-history", json=payload_count, timeout=10)
                        print(f"Berhasil mengirim jumlah user ({user_count}) ke web server.")
                    except Exception as e:
                        print(f"ERROR: Gagal mengirim jumlah user. Alasan: {e}")
                    
                    # 2. Kirim DETAIL user untuk halaman analitik
                    try:
                        # Data detail sudah bersih dari fungsi sebelumnya, langsung kirim
                        requests.post(f"{FLASK_SERVER_URL}/api/log-active-users", json=users_detail, timeout=10)
                        print(f"Berhasil mengirim detail {len(users_detail)} user ke web server.")
                    except Exception as e:
                        print(f"ERROR: Gagal mengirim detail user. Alasan: {e}")

                last_mikrotik_check = current_time

            time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Layanan monitoring dihentikan.")
            break
        except Exception as e:
            print(f"\nTerjadi error pada loop utama: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
