from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
from collections import Counter
from pathlib import Path
import routeros_api

app = Flask(__name__)
app = Flask(__name__)
app.secret_key = 's0t0kudus_secret_key_monitoringwebjss_2025'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Silakan login untuk mengakses halaman ini."
login_manager.login_message_category = "warning"

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin2025')

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = ADMIN_USERNAME
        
@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

_env_root = os.environ.get("HOTSPOT_ROOT")
if _env_root:
    PROJECT_ROOT = Path(_env_root).expanduser().resolve()
else:
    PROJECT_ROOT = Path(app.root_path).resolve()

DATA_DIR = PROJECT_ROOT / 'data'
RUNTIME_DIR = PROJECT_ROOT / 'runtime'
DATA_FILE = DATA_DIR / 'onts.json'
NOTIFICATIONS_FILE = DATA_DIR / 'notifications.json'
NOTIFICATIONS_BAK_FILE = NOTIFICATIONS_FILE.with_name(NOTIFICATIONS_FILE.name + '.bak')
WIFI_DATA_FILE = DATA_DIR / 'wifi_sleman.json'
OUTAGES_FILE = DATA_DIR / 'outages.json'
BACKUP_DIR = RUNTIME_DIR / 'backups'
HISTORY_FILE = RUNTIME_DIR / 'history.json'
MIKROTIK_IP = '111.92.166.184'
MIKROTIK_PORT = 8728
MIKROTIK_USER = 'monitor'
MIKROTIK_PASS = 's0t0kudus'
USER_LOG_FILE = RUNTIME_DIR / 'user_log.json'
STATUS_CACHE_FILE = RUNTIME_DIR / 'status_cache.json'


def load_data():
    # Membaca data ONT dari `wifi_sleman.json` sebagai sumber utama untuk monitoring.
    # Jika file tersebut tidak ada atau corrupt, fallback ke DATA_FILE (onts.json).
    try:
        with open(WIFI_DATA_FILE, 'r', encoding='utf-8') as f:
            base = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        try:
            with open(DATA_FILE, 'r') as f:
                base = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            base = []

    # Jika ada cache status yang dibuat oleh skrip monitoring, gabungkan ke data
    try:
        with open(STATUS_CACHE_FILE, 'r', encoding='utf-8') as sf:
            status_cache = json.load(sf)
            # status_cache diharapkan berupa list atau dict; normalisasi ke dict by id/ip
            status_map = {}
            if isinstance(status_cache, list):
                for item in status_cache:
                    key = item.get('id') or item.get('ip')
                    if key is not None:
                        status_map[str(key)] = item.get('status')
            elif isinstance(status_cache, dict):
                # langsung mapping id/ip -> status
                for k, v in status_cache.items():
                    status_map[str(k)] = v

            # terapkan status ke base
            for ont in base:
                # coba mencocokkan berdasarkan id terlebih dulu, lalu ip
                ont_id = ont.get('id')
                ont_ip = ont.get('ip')
                if ont_id is not None and str(ont_id) in status_map:
                    ont['status'] = status_map[str(ont_id)]
                elif ont_ip and str(ont_ip) in status_map:
                    ont['status'] = status_map[str(ont_ip)]
                else:
                    # pastikan ada field status default
                    ont.setdefault('status', 'UNKNOWN')
    except (FileNotFoundError, json.JSONDecodeError):
        # tidak ada cache status, pastikan setiap entri memiliki field status
        for ont in base:
            ont.setdefault('status', 'UNKNOWN')

    # Normalisasi koordinat: pastikan latitude/longitude adalah float atau None
    for ont in base:
        lat = ont.get('latitude')
        lon = ont.get('longitude')
        try:
            if lat is None or lat == "":
                ont['latitude'] = None
            else:
                ont['latitude'] = float(str(lat).strip())
        except Exception:
            ont['latitude'] = None
        try:
            if lon is None or lon == "":
                ont['longitude'] = None
            else:
                ont['longitude'] = float(str(lon).strip())
        except Exception:
            ont['longitude'] = None

    # Filter out entries without valid coordinates when needed by the UI
    return base


# --- SEMUA FUNGSI LAMA ANDA TETAP DI SINI (TIDAK ADA YANG DIHAPUS) ---

def load_notifications():
    """Load notifications from primary file; fall back to backup on decode error."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as f:
            notifications = json.load(f)
        if not isinstance(notifications, list):
            raise ValueError("Notifications file does not contain a list")
        for notif in notifications:
            if not isinstance(notif, dict):
                raise ValueError("Invalid notification format")
            if 'id' not in notif or 'message' not in notif or 'timestamp' not in notif:
                raise ValueError("Notification missing required fields")
        return notifications
    except FileNotFoundError:
        print("Notifications file not found, trying to recover from backup...")
        return _recover_notifications_from_backup()
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Notifications file corrupted: {e}, trying to recover from backup...")
        return _recover_notifications_from_backup()

def _recover_notifications_from_backup():
    """Mencoba memulihkan notifikasi dari backup terbaru"""
    try:
        import glob
        backup_pattern = os.path.join(BACKUP_DIR, 'notifications-*.json')
        backup_files = glob.glob(backup_pattern)
        if not backup_files:
            print("No notification backups found, starting fresh")
            return []
        backup_files.sort(key=os.path.getmtime, reverse=True)
        latest_backup = backup_files[0]
        print(f"Recovering notifications from: {latest_backup}")
        with open(latest_backup, 'r') as f:
            notifications = json.load(f)
        save_notifications(notifications)
        print(f"Successfully recovered {len(notifications)} notifications")
        return notifications
    except Exception as e:
        print(f"Failed to recover notifications from backup: {e}")
        return []

def _atomic_write_json(file_path, data):
    dir_name = os.path.dirname(file_path) or '.'
    os.makedirs(dir_name, exist_ok=True)
    temp_path = os.path.join(dir_name, f".tmp-{os.path.basename(file_path)}")
    with open(temp_path, 'w') as tf:
        json.dump(data, tf, indent=2)
        tf.flush()
        try:
            os.fsync(tf.fileno())
        except Exception:
            pass
    try:
        with open(f"{file_path}.bak", 'w') as bf:
            json.dump(data, bf, indent=2)
    except Exception:
        pass
    os.replace(temp_path, file_path)

def save_notifications(notifications):
    _atomic_write_json(NOTIFICATIONS_FILE, notifications)

def load_outages():
    try:
        with open(OUTAGES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_outages(outages):
    _atomic_write_json(OUTAGES_FILE, outages)

def _record_outage_transition(ont_id, ont_name, old_status, new_status, event_time_iso):
    if old_status == new_status:
        return
    outages = load_outages()
    if old_status == 'ON' and new_status != 'ON':
        outages.append({
            "ont_id": ont_id, "ont_name": ont_name,
            "start_time": event_time_iso, "end_time": None
        })
        save_outages(outages)
        return
    if old_status != 'ON' and new_status == 'ON':
        for rec in reversed(outages):
            if rec.get('ont_id') == ont_id and rec.get('end_time') is None:
                rec['end_time'] = event_time_iso
                break
        save_outages(outages)

def add_notification(message, notification_type="info", ont_id=None, ont_name=None, timestamp=None):
    notifications = load_notifications()
    next_id = (max((n.get('id', 0) for n in notifications), default=0) + 1)
    new_notification = {
        "id": next_id, "message": message, "type": notification_type,
        "timestamp": (timestamp or datetime.now().isoformat()),
        "ont_id": ont_id, "ont_name": ont_name, "read": False
    }
    notifications.append(new_notification)
    _backup_notifications(notifications)
    save_notifications(notifications)
    return new_notification

def _backup_notifications(notifications):
    try:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'notifications-{timestamp}.json')
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(backup_path, 'w') as f:
            json.dump(notifications, f, indent=2)
        _cleanup_old_backups('notifications-*.json', 10)
    except Exception as e:
        print(f"Warning: Failed to backup notifications: {e}")

def _cleanup_old_backups(pattern, keep_count):
    try:
        import glob
        backup_files = glob.glob(os.path.join(BACKUP_DIR, pattern))
        backup_files.sort(key=os.path.getmtime, reverse=True)
        for old_file in backup_files[keep_count:]:
            try:
                os.remove(old_file)
            except:
                pass
    except Exception as e:
        print(f"Warning: Failed to cleanup old backups: {e}")

def save_and_backup(onts):
    os.makedirs(DATA_FILE.parent, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(onts, f, indent=2)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'onts-{timestamp}.json')
    with open(backup_path, 'w') as f:
        json.dump(onts, f, indent=2)

#@app.route('/login', methods=['GET', 'POST'])
#def login():
#    if current_user.is_authenticated:
#        return redirect(url_for('admin'))
#    
#    if request.method == 'POST':
#        username = request.form['username']
#        password = request.form['password']
#        
#        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
#            user = User(ADMIN_USERNAME)
#            login_user(user)
#            return redirect(url_for('admin'))
#        else:
#            return render_template('login.html', error="Invalid username or password")
    
    # Render login page for GET requests
#    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            user = User(ADMIN_USERNAME)
            login_user(user, remember=True)
            flash('Login berhasil! Selamat datang Admin.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin'))
        else:
            flash('Username atau password salah!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('map_view'))

@app.route('/')
def map_view():
    return render_template('map.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics_page():
    """Menampilkan halaman analitik baru."""
    return render_template('analytics.html')

@app.route('/api/onts')
def api_onts():
    return jsonify(load_data())

@app.route('/admin')
@login_required
def admin():
    onts = load_data()
    return render_template('list.html', onts=onts)

@app.route('/notifications')
def notifications():
    notifications_list = load_notifications()
    notifications_list.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('notifications.html', notifications=notifications_list)

@app.route('/api/notifications', methods=['GET', 'POST'])
def api_notifications():
    if request.method == 'POST':
        data = request.get_json()
        add_notification(data.get('message', ''), data.get('type', 'info'), None, None, timestamp=data.get('timestamp'))
        return jsonify({"success": True})
    notifications_list = load_notifications()
    notifications_list.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(notifications_list)

@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    notifications_list = load_notifications()
    for notification in notifications_list:
        if notification['id'] == notification_id:
            notification['read'] = True
            break
    save_notifications(notifications_list)
    return jsonify({"success": True})

@app.route('/api/notifications/clear-all', methods=['POST'])
def clear_all_notifications():
    try:
        current_notifications = load_notifications()
        if current_notifications:
            _backup_notifications(current_notifications)
        save_notifications([])
        return jsonify({"success": True, "message": "Semua notifikasi berhasil dihapus."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/notifications/restore-backup', methods=['POST'])
def restore_notifications_from_backup():
    try:
        current_notifications = load_notifications()
        if current_notifications:
            _backup_notifications(current_notifications)
        restored_notifications = _recover_notifications_from_backup()
        if restored_notifications:
            return jsonify({"success": True, "message": f"Berhasil memulihkan {len(restored_notifications)} notifikasi dari backup", "count": len(restored_notifications)})
        else:
            return jsonify({"success": False, "message": "Tidak ada backup yang tersedia untuk dipulihkan"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/add', methods=['GET', 'POST'])
def add_ont():
    if request.method == 'POST':
        onts = load_data()
        new_id = max([o['id'] for o in onts], default=0) + 1
        new_ont = {
            "id": new_id,
            "id_pelanggan": request.form['id_pelanggan'], "name": request.form['name'],
            "lokasi": request.form['lokasi'], "ip": request.form['ip'],
            "latitude": float(request.form['latitude']), "longitude": float(request.form['longitude']),
            "status": "OFF", "rto_count": 0
        }
        onts.append(new_ont)
        save_and_backup(onts)
        add_notification(f"ONT baru ditambahkan: {new_ont['name']} ({new_ont['id_pelanggan']})", "success", new_ont['id'], new_ont['name'])
        return redirect(url_for('admin'))
    return render_template('form.html', ont={})

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_ont(id):
    onts = load_data()
    ont = next((o for o in onts if o['id'] == id), None)
    if not ont:
        return "ONT not found", 404
    if request.method == 'POST':
        old_name = ont['name']
        old_id_pelanggan = ont['id_pelanggan']
        ont['id_pelanggan'] = request.form['id_pelanggan']
        ont['name'] = request.form['name']
        ont['lokasi'] = request.form['lokasi']
        ont['ip'] = request.form['ip']
        ont['latitude'] = float(request.form['latitude'])
        ont['longitude'] = float(request.form['longitude'])
        if 'rto_count' not in ont:
            ont['rto_count'] = 0
        save_and_backup(onts)
        add_notification(f"ONT diperbarui: {old_name} ({old_id_pelanggan}) → {ont['name']} ({ont['id_pelanggan']})", "info", ont['id'], ont['name'])
        return redirect(url_for('admin'))
    return render_template('form.html', ont=ont)

@app.route('/delete/<int:id>')
def delete_ont(id):
    onts = load_data()
    ont_to_delete = next((o for o in onts if o['id'] == id), None)
    if ont_to_delete:
        add_notification(f"ONT dihapus: {ont_to_delete['name']} ({ont_to_delete['id_pelanggan']})", "warning", ont_to_delete['id'], ont_to_delete['name'])
    onts = [o for o in onts if o['id'] != id]
    save_and_backup(onts)
    return redirect(url_for('admin'))

@app.route('/api/history', methods=['GET'])
def get_history():
    """API untuk mengambil semua data riwayat dari history.json."""
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        return jsonify(history)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])

@app.route('/api/record-history', methods=['POST'])
def record_history():
    data = request.get_json()
    user_count = data.get('users')

    if user_count is None:
        return jsonify({"success": False, "message": "User count not provided"}), 400

    new_record = {
        # PERUBAHAN: Simpan timestamp lengkap, bukan hanya waktu
        "timestamp": datetime.now().isoformat(), 
        "users": user_count
    }
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    history.append(new_record)

    MAX_HISTORY = 100
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    return jsonify({"success": True, "recorded": new_record})

# --- FUNGSI-FUNGSI OUTAGES DI BAWAH INI JUGA TETAP SAMA ---
@app.route('/api/outages', methods=['GET'])
def api_outages():
    outages = load_outages()
    outages.sort(key=lambda x: x.get('start_time') or '', reverse=True)
    return jsonify(outages)

@app.route('/api/outages/summary', methods=['GET'])
def api_outages_summary():
    outages = load_outages()
    summary = {}
    for rec in outages:
        key = rec.get('ont_id')
        name = rec.get('ont_name')
        if key not in summary:
            summary[key] = {
                'ont_id': key, 'ont_name': name, 'outage_count': 0,
                'last_start': None, 'last_end': None, 'ongoing': False
            }
        summary[key]['outage_count'] += 1
        start = rec.get('start_time')
        end = rec.get('end_time')
        if not summary[key]['last_start'] or (start and start > summary[key]['last_start']):
            summary[key]['last_start'] = start
            summary[key]['last_end'] = end
        if end is None:
            summary[key]['ongoing'] = True
    
    # ... (Sisa fungsi summary tetap sama)
    summary_list = list(summary.values())
    summary_list.sort(key=lambda x: (x['outage_count'], x['last_start'] or ''), reverse=True)
    return jsonify(summary_list)

@app.route('/api/outages/clear-all', methods=['POST'])
def clear_all_outages():
    try:
        save_outages([])
        return jsonify({"success": True, "message": "Semua data rekap outages berhasil dihapus."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/api/hotspot/active-users')
def get_active_users():
    """Menghubungkan ke MikroTik dan mengambil daftar user aktif saat ini."""
    try:
        connection = routeros_api.RouterOsApiPool(
            MIKROTIK_IP,
            username=MIKROTIK_USER,
            password=MIKROTIK_PASS,
            port=MIKROTIK_PORT,
            plaintext_login=True
        )
        api = connection.get_api()
        
        # Mengambil seluruh daftar user aktif
        active_users_list = api.get_resource('/ip/hotspot/active').get()
        connection.disconnect()
        
        # Memilih hanya data yang kita perlukan (ip dan mac address)
        cleaned_users = []
        for user in active_users_list:
            cleaned_users.append({
                'ip': user.get('address', '-'),
                'mac': user.get('mac-address', '-')
            })
            
        return jsonify(cleaned_users)

    except Exception as e:
        # Jika gagal, kirim pesan error
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/log-active-users', methods=['POST'])
def log_active_users():
    """Menerima data DETAIL user dari skrip monitoring dan menyimpannya ke user_log.json."""
    users_detail = request.get_json()
    
    if not isinstance(users_detail, list):
        return jsonify({"success": False, "message": "Invalid data format"}), 400

    new_log_entry = {
        "timestamp": datetime.now().isoformat(),
        "users": users_detail
    }
    try:
        with open(USER_LOG_FILE, 'r') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = []
    
    log_data.append(new_log_entry)

    # Batasi agar file log tidak terlalu besar (misal, simpan 2000 data terakhir)WWWWWWW
    MAX_LOG_ENTRIES = 2000
    if len(log_data) > MAX_LOG_ENTRIES:
        log_data = log_data[-MAX_LOG_ENTRIES:]

    os.makedirs(os.path.dirname(USER_LOG_FILE), exist_ok=True)
    with open(USER_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)

    return jsonify({"success": True, "message": f"Logged {len(users_detail)} users."})


@app.route('/api/analytics-data')
def get_analytics_data():
    """Membaca user_log.json, memprosesnya, dan mengirimkan data untuk halaman analitik."""
    try:
        with open(USER_LOG_FILE, 'r') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Belum ada data analitik."}), 404
    if not log_data:
        return jsonify({"error": "Belum ada data analitik."}), 404

    # --- PERUBAHAN UTAMA: MENGELOMPOKKAN DATA PER HARI ---
    daily_data = {}
    for entry in log_data:
        day = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d')
        if day not in daily_data:
            daily_data[day] = []
        daily_data[day].append(len(entry['users']))
    
    daily_summary = []
    for day, counts in daily_data.items():
        if counts:
            daily_summary.append({
                "date": day,
                "peak": max(counts),
                "trough": min(counts),
                "average": round(sum(counts) / len(counts))
            })

    daily_summary.sort(key=lambda x: x['date'])
    user_counts = [len(entry['users']) for entry in log_data]
    all_macs = set(user['mac'] for entry in log_data for user in entry['users'] if 'mac' in user)
    
    analytics_payload = {
        "summary": {
            "peak_users": max(user_counts) if user_counts else 0,
            "trough_users": min(user_counts) if user_counts else 0,
            "average_users": round(sum(user_counts) / len(user_counts), 2) if user_counts else 0,
            "unique_devices": len(all_macs)
        },
        "daily_summary": daily_summary,
        "raw_logs": log_data[-100:]
    }
    return jsonify(analytics_payload)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)
