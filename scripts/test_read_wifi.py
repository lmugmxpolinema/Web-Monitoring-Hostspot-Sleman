import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / 'data' / 'wifi_sleman.json'

try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('OK: loaded', len(data), 'items from', DATA_FILE.name)
    print('sample:', data[0])
except Exception as e:
    print('ERROR:', e)
