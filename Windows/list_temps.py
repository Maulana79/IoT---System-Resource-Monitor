import requests
import json

d = requests.get('http://localhost:8085/data.json', timeout=3).json()

# Ambil semua temperatures
temps = d['Children'][0]['Children'][0]['Children'][0]['Children'][1]['Children']

print("=== Semua Sensor Suhu ===")
for c in temps:
    print(f"{c['Text']}: {c.get('Value')}")