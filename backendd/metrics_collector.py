"""
metrics_collector.py
Real metrics: cpu, ram, disk, battery
Simulated: temperature, humidity, fan, dust
(using formulas consistent with training data)
"""

import psutil
import numpy as np
import time

_rng = np.random.default_rng()

_dust_accumulator = 0.0
_last_time = time.time()


def get_system_metrics() -> dict:
    global _dust_accumulator, _last_time

    # ── Real metrics ──────────────────────────────────────────────
    cpu_raw  = psutil.cpu_percent(interval=1)
    ram_raw  = psutil.virtual_memory().percent
    disk_raw = psutil.disk_usage("/").percent

    battery = psutil.sensors_battery()
    battery_raw = battery.percent if battery else 80.0

    # ── Simulated metrics (match training distributions) ──────────
    # Temperature: correlated with CPU, with noise
    temperature_raw = float(np.clip(
        30 + cpu_raw * 0.45 + _rng.normal(0, 3),
        20, 100
    ))

    # Humidity: loosely correlated with temperature
    humidity_raw = float(np.clip(
        30 + temperature_raw * 0.15 + _rng.normal(0, 4),
        20, 90
    ))

    # Fan speed: driven by temp + CPU
    fan_raw = float(np.clip(
        temperature_raw * 35 + cpu_raw * 18 + _rng.normal(0, 80),
        0, 5000
    ))

    # Dust: accumulates slowly based on disk use and fan activity
    now = time.time()
    dt = now - _last_time
    _last_time = now
    _dust_accumulator = float(np.clip(
        _dust_accumulator
        + (disk_raw * 0.00002 + fan_raw * 0.000001) * dt
        + _rng.uniform(0, 0.001),
        0, 100
    ))
    dust_raw = _dust_accumulator

    # ── Normalised [0,1] for model input ─────────────────────────
    return {
        # Raw (for display & alert logic)
        "cpu_raw":         round(cpu_raw, 1),
        "ram_raw":         round(ram_raw, 1),
        "disk_raw":        round(disk_raw, 1),
        "temperature_raw": round(temperature_raw, 1),
        "humidity_raw":    round(humidity_raw, 1),
        "fan_raw":         round(fan_raw, 1),
        "dust_raw":        round(dust_raw, 2),
        "battery_raw":     round(battery_raw, 1),

        # Normalised (model features)
        "cpu":         round(cpu_raw  / 100,  4),
        "ram":         round(ram_raw  / 100,  4),
        "disk":        round(disk_raw / 100,  4),
        "temperature": round(temperature_raw / 120, 4),
        "humidity":    round(humidity_raw    / 100, 4),
        "fan":         round(fan_raw         / 5000,4),
        "dust":        round(dust_raw        / 100, 4),
        "battery":     round(battery_raw     / 100, 4),
    }