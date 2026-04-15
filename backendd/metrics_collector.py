#metrics_collector.py
import psutil
import random

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def get_system_metrics():
    cpu_raw = psutil.cpu_percent(interval=1)
    ram_raw = psutil.virtual_memory().percent
    disk_raw = psutil.disk_usage("/").percent

    battery_info = psutil.sensors_battery()
    battery_raw = battery_info.percent if battery_info else 75.0

    temperature_raw = 35 + cpu_raw * 0.45 + random.uniform(-2, 2)
    temperature = temperature_raw / 100

    fan_raw = clamp(temperature_raw * 40 + cpu_raw * 20, 0, 5000)
    dust_raw = clamp(disk_raw * 0.3 + fan_raw * 0.005, 0, 100)
    humidity_raw = clamp(30 + cpu_raw * 0.25 + temperature_raw * 0.15, 0, 100)

    return {
        "cpu": cpu_raw/100,
        "ram": ram_raw/100,
        "disk": disk_raw/100,
        "temperature": temperature,
        "humidity": humidity_raw/100,
        "fan": fan_raw/5000,
        "dust": dust_raw/100,
        "battery": battery_raw/100,

        "cpu_raw": cpu_raw,
        "ram_raw": ram_raw,
        "disk_raw": disk_raw,
        "temperature_raw": temperature_raw,
        "humidity_raw": humidity_raw,
        "fan_raw": fan_raw,
        "dust_raw": dust_raw,
        "battery_raw": battery_raw
    }