import json

p = 'wifi_sleman.json'
try:
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('OK: loaded', len(data), 'items from', p)
    print('sample:', data[0])
except Exception as e:
    print('ERROR:', e)
