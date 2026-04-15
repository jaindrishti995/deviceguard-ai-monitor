#preprocessing.py
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler

FEATURES = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]

def _simulate_dataset(n):
    rng = np.random.default_rng(42)

    cpu  = rng.uniform(5, 95, n)
    ram  = rng.uniform(10, 95, n)
    disk = rng.uniform(5, 90, n)

    temperature = np.clip(30 + cpu * 0.45 + rng.normal(0, 3, n), 20, 100)
    humidity    = np.clip(30 + temperature * 0.15 + rng.normal(0, 4, n), 20, 90)

    fan  = np.clip(temperature * 35 + cpu * 18 + rng.normal(0, 80, n), 0, 5000)
    dust = np.clip(disk * 0.25 + fan * 0.004 + rng.uniform(0, 10, n), 0, 100)
    battery = np.clip(100 - (cpu * 0.3 + temperature * 0.2), 5, 100)

    return pd.DataFrame({
        "cpu": cpu, "ram": ram, "disk": disk,
        "temperature": temperature, "humidity": humidity,
        "fan": fan, "dust": dust, "battery": battery
    })

def load_and_process(n_rows=5000, save_scaler=True):
    df = _simulate_dataset(n_rows)

    scaler = MinMaxScaler()
    df[FEATURES] = scaler.fit_transform(df[FEATURES])

    if save_scaler:
        joblib.dump(scaler, "scaler.pkl")
        print("💾 scaler.pkl saved")

    return df, FEATURES