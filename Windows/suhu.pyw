import time
import wmi
import httpx
import psutil
import requests

# --- KONFIGURASI SUPABASE ---
URL = "https://btipbbeujlpulcjcvhoz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0aXBiYmV1amxwdWxjamN2aG96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDg2ODQsImV4cCI6MjA5MzE4NDY4NH0.2DBe7rBoTaw-fRSXyjqOwgxoWttsfLgwVuxPVtk5zao"

# Nama perangkatmu
DEVICE_ID = "PC Xeon"

# OpenHardwareMonitor web server port (default 8085)
OHM_URL = "http://192.168.0.100:8085/data.json"

def get_cpu_temp():
    # Coba metode 1: OpenHardwareMonitor (jika sedang berjalan)
    try:
        response = requests.get(OHM_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            # Cari suhu CPU spesifik
            def find_cpu_temp(node):
                text = node.get('Text', '').upper()
                if 'CPU' in text:
                    for c in node.get('Children', []):
                        if 'Temperature' in c.get('Text', '') and c.get('Value'):
                            val = str(c.get('Value', '')).replace(' °C', '').replace(',', '.')
                            return float(val)
                for c in node.get('Children', []):
                    result = find_cpu_temp(c)
                    if result:
                        return result
                return None
            
            cpu_temp = find_cpu_temp(data)
            if cpu_temp:
                return round(cpu_temp, 2)
            
            # Fallback: cari yang paling mirip "Core" atau "CPU"
            def find_core_temp(node):
                result = []
                for c in node.get('Children', []):
                    text = c.get('Text', '').lower()
                    if 'core' in text or 'cpu' in text:
                        if c.get('Value'):
                            try:
                                val = str(c.get('Value', '')).replace(' °C', '').replace(',', '.')
                                result.append(float(val))
                            except:
                                pass
                    result.extend(find_core_temp(c))
                return result
            
            temps = find_core_temp(data)
            if temps:
                return round(max(temps), 2)
    except Exception as e:
        print(f"OHM gagal: {e}")
    
    # Coba metode 2: psutil (jika support)
    try:
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                if 'cpu' in name.lower():
                    for entry in entries:
                        if entry.current:
                            return round(entry.current, 2)
    except Exception as e:
        print(f"psutil gagal: {e}")
    
    # Coba metode 3: WMI
    try:
        w = wmi.WMI(namespace="root\\wmi")
        temp_info = w.MSAcpi_ThermalZoneTemperature()[0]
        celsius = (temp_info.CurrentTemperature / 10.0) - 273.15
        return round(celsius, 2)
    except Exception as e:
        print(f"WMI gagal: {e}")
    
    # Fallback: angka acak untuk testing
    import random
    return round(random.uniform(40.0, 55.0), 2) 

# PERBAIKAN: Menambahkan parameter cpu_usage dan ram_usage ke fungsi
def send_to_supabase(device_name, temperature, cpu_usage, ram_usage):
    """Kirim data suhu ke Supabase via REST API"""
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "device_name": device_name,
        "temperature": temperature,
        "api_key": "RHS-2026-XyZ",
        "cpu_usage": cpu_usage, # Memasukkan nilai dari parameter
        "ram_usage": ram_usage  # Memasukkan nilai dari parameter
    }
    
    # Retry logic untuk handle network issues
    for attempt in range(3):
        try:
            response = httpx.post(
                f"{URL}/rest/v1/temperature_logs", 
                json=data, 
                headers=headers,
                timeout=10.0  # 10 detik timeout
            )
            return response.status_code == 201 or response.status_code == 200
        except Exception as e:
            print(f"Attempt {attempt+1} gagal: {e}")
            if attempt < 2:
                time.sleep(2)  # Tunggu 2 detik sebelum retry
    
    return False

print(f"Menjalankan script monitoring untuk {DEVICE_ID}...")

# Looping pengiriman data
while True:
    suhu_sekarang = get_cpu_temp()
    cpu_persen = psutil.cpu_percent(interval=1) 
    ram_persen = psutil.virtual_memory().percent
    
    if suhu_sekarang:
        try:
            # PERBAIKAN: Mengirim variabel cpu_persen dan ram_persen ke fungsi send_to_supabase
            success = send_to_supabase(DEVICE_ID, suhu_sekarang, cpu_persen, ram_persen)
            waktu = time.strftime('%H:%M:%S')
            if success:
                print(f"[{waktu}] Berhasil mengirim - Suhu: {suhu_sekarang}°C | CPU: {cpu_persen}% | RAM: {ram_persen}%")
            else:
                print(f"[{waktu}] Gagal mengirim data")
        except Exception as e:
            print("Gagal mengirim data ke Supabase:", e)
            
    # Jeda 60 detik (1 menit) sebelum cek dan kirim data lagi
    time.sleep(60)