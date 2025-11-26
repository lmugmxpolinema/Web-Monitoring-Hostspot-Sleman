import json
import os
from pathlib import Path

_env_root = os.environ.get("HOTSPOT_ROOT")
if _env_root:
    PROJECT_ROOT = Path(_env_root).expanduser().resolve()
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / 'data' / 'wifi_sleman.json'

try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('OK: loaded', len(data), 'items from', DATA_FILE.name)
    print('sample:', data[0])
except Exception as e:
    print('ERROR:', e)
