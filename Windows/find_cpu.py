import requests
import json

d = requests.get('http://localhost:8085/data.json', timeout=3).json()

def find_cpu_temp(node, depth=0):
    """Cari suhu CPU spesifik"""
    text = node.get('Text', '')
    
    # Cek jika ini adalah CPU
    if 'CPU' in text.upper():
        for c in node.get('Children', []):
            if 'Temperature' in c.get('Text', ''):
                val = c.get('Value', '')
                if val and '°C' in str(val):
                    # Ambil angka dari format "91,0 °C"
                    try:
                        num = float(val.replace(' °C', '').replace(',', '.'))
                        return text, num
                    except:
                        pass
    
    # Recursive
    for c in node.get('Children', []):
        result = find_cpu_temp(c, depth+1)
        if result:
            return result
    
    return None

# Cari CPU
result = find_cpu_temp(d)
if result:
    print(f"CPU: {result[0]} = {result[1]}°C")
else:
    print("CPU tidak ditemukan,ambil suhu tertinggi")
    
    # Ambil suhu tertinggi
    def find_all_temp(node):
        result = []
        for c in node.get('Children', []):
            if 'Temperature' in c.get('Text', '') and c.get('Value'):
                try:
                    val = str(c.get('Value', '')).replace(' °C', '').replace(',', '.')
                    num = float(val)
                    result.append((c.get('Text'), num))
                except:
                    pass
            result.extend(find_all_temp(c))
        return result
    
    temps = find_all_temp(d)
    if temps:
        max_temp = max(temps, key=lambda x: x[1])
        print(f"Suhu tertinggi: {max_temp[1]}°C")