"""
clean_datasets.py
-----------------
Cleans and merges two Kaggle datasets:
1. Environmental Sensor Data (132k) - provides temperature, humidity
   Source: https://www.kaggle.com/datasets/garystafford/environmental-sensor-data-132k
   Expected CSV columns: ts, device, co, humidity, light, lpg, motion, smoke, temp

2. System Resources (CPU/RAM/Disk/Network) - provides cpu, ram, disk
   Source: https://www.kaggle.com/datasets/omnamahshivai/dataset-system-resources-cpu-ram-disk-network
   Expected CSV columns: cpu_percent, memory_percent, disk_percent, net_bytes_sent, net_bytes_recv, ...

Usage:
    python clean_datasets.py \
        --env  path/to/iot_telemetry_data.csv \
        --sys  path/to/system_resources.csv \
        --out  cleaned_dataset.csv \
        --rows 10000
"""

import argparse
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

FEATURES = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]


# ─── Cleaning helpers ────────────────────────────────────────────────────────

def clean_env_dataset(path: str, n: int) -> pd.DataFrame:
    """
    Loads and cleans the environmental sensor dataset.
    Extracts: temperature (temp), humidity.
    """
    df = pd.read_csv(path)
    print(f"  ENV raw shape: {df.shape}")

    # Rename to standard names
    rename = {}
    for col in df.columns:
        lc = col.lower().strip()
        if lc in ("temp", "temperature"):
            rename[col] = "temperature_raw"
        elif lc in ("humidity",):
            rename[col] = "humidity_raw"
    df = df.rename(columns=rename)

    needed = [c for c in ["temperature_raw", "humidity_raw"] if c in df.columns]
    df = df[needed].dropna()

    # Clip to realistic ranges
    if "temperature_raw" in df.columns:
        df = df[(df["temperature_raw"] > 0) & (df["temperature_raw"] < 120)]
    if "humidity_raw" in df.columns:
        df = df[(df["humidity_raw"] >= 0) & (df["humidity_raw"] <= 100)]

    df = df.sample(min(n, len(df)), random_state=42).reset_index(drop=True)
    print(f"  ENV cleaned shape: {df.shape}")
    return df


def clean_sys_dataset(path: str, n: int) -> pd.DataFrame:
    """
    Loads and cleans the system resources dataset.
    Extracts: cpu_percent, memory_percent, disk_percent.
    """
    df = pd.read_csv(path)
    print(f"  SYS raw shape: {df.shape}")

    rename = {}
    for col in df.columns:
        lc = col.lower().strip().replace(" ", "_")
        if "cpu" in lc and "percent" in lc:
            rename[col] = "cpu_raw"
        elif "mem" in lc and "percent" in lc:
            rename[col] = "ram_raw"
        elif "disk" in lc and "percent" in lc:
            rename[col] = "disk_raw"

    df = df.rename(columns=rename)

    needed = [c for c in ["cpu_raw", "ram_raw", "disk_raw"] if c in df.columns]
    df = df[needed].dropna()

    # Clip to [0, 100]
    for col in needed:
        df = df[(df[col] >= 0) & (df[col] <= 100)]

    df = df.sample(min(n, len(df)), random_state=42).reset_index(drop=True)
    print(f"  SYS cleaned shape: {df.shape}")
    return df


def simulate_missing_features(df: pd.DataFrame, rng) -> pd.DataFrame:
    """
    Derives fan, dust, battery from existing cleaned columns.
    Uses formulas consistent with metrics_collector.py.
    """
    cpu = df["cpu_raw"].values
    temp = df["temperature_raw"].values
    disk = df["disk_raw"].values

    fan_raw = np.clip(temp * 40 + cpu * 20 + rng.normal(0, 80, len(df)), 0, 5000)
    dust_raw = np.clip(disk * 0.3 + fan_raw * 0.005 + rng.uniform(0, 10, len(df)), 0, 100)
    battery_raw = np.clip(100 - (cpu * 0.3 + temp * 0.2) + rng.normal(0, 3, len(df)), 5, 100)

    df["fan_raw"] = fan_raw
    df["dust_raw"] = dust_raw
    df["battery_raw"] = battery_raw
    return df


def build_merged_dataset(env_path, sys_path, n_rows, out_path):
    rng = np.random.default_rng(42)

    print("\n[1] Cleaning ENV dataset...")
    env_df = clean_env_dataset(env_path, n_rows)

    print("\n[2] Cleaning SYS dataset...")
    sys_df = clean_sys_dataset(sys_path, n_rows)

    # Align lengths by taking minimum
    n = min(len(env_df), len(sys_df), n_rows)
    env_df = env_df.iloc[:n].reset_index(drop=True)
    sys_df = sys_df.iloc[:n].reset_index(drop=True)

    print(f"\n[3] Merging {n} rows...")
    df = pd.concat([sys_df, env_df], axis=1)

    print("\n[4] Simulating fan, dust, battery...")
    df = simulate_missing_features(df, rng)

    # ── Normalise to [0,1] ──
    raw_cols = ["cpu_raw", "ram_raw", "disk_raw", "temperature_raw",
                "humidity_raw", "fan_raw", "dust_raw", "battery_raw"]
    norm_names = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]
    divisors   = [100,   100,   100,   120,            100,          5000,  100,   100]

    for raw, norm, div in zip(raw_cols, norm_names, divisors):
        df[norm] = (df[raw] / div).clip(0, 1)

    # ── Label creation (same logic as train_model.py) ──
    df["label"] = (
        (df["cpu"]         > 0.75).astype(int) +
        (df["ram"]         > 0.75).astype(int) +
        (df["disk"]        > 0.80).astype(int) +
        (df["temperature"] > 0.65).astype(int) +
        (df["fan"]         > 0.70).astype(int) +
        (df["humidity"]    > 0.75).astype(int)
    )
    df["label"] = (df["label"] >= 2).astype(int)

    print(f"\n[5] Label distribution:\n{df['label'].value_counts()}")

    # ── Save scaler from cleaned real data ──
    scaler = MinMaxScaler()
    df[norm_names] = scaler.fit_transform(df[norm_names])
    save_dir = os.path.dirname(out_path) or "."
    os.makedirs(save_dir, exist_ok=True)   # 🔥 THIS LINE FIXES EVERYTHING
    joblib.dump(scaler, os.path.join(save_dir, "scaler.pkl"))
    
    print("\n💾 scaler.pkl saved")

    df.to_csv(out_path, index=False)
    print(f"✅ Saved cleaned dataset → {out_path}  ({len(df)} rows)")
    return df


# ─── Fallback: pure simulation (if no CSVs available) ────────────────────────

def generate_simulated_dataset(n_rows, out_path):
    """
    If Kaggle CSVs are not available, generates a realistic simulated dataset.
    This keeps train_model.py working even without the raw files.
    """
    print(f"\n[SIMULATION MODE] Generating {n_rows} rows...")
    rng = np.random.default_rng(42)

    cpu_raw  = rng.uniform(5,  95, n_rows)
    ram_raw  = rng.uniform(10, 95, n_rows)
    disk_raw = rng.uniform(5,  90, n_rows)

    temp_raw = np.clip(30 + cpu_raw * 0.45 + rng.normal(0, 3, n_rows), 20, 100)
    hum_raw  = np.clip(30 + temp_raw * 0.15 + rng.normal(0, 4, n_rows), 20, 90)
    fan_raw  = np.clip(temp_raw * 40 + cpu_raw * 20 + rng.normal(0, 80, n_rows), 0, 5000)
    dust_raw = np.clip(disk_raw * 0.25 + fan_raw * 0.004 + rng.uniform(0, 10, n_rows), 0, 100)
    bat_raw  = np.clip(100 - (cpu_raw * 0.3 + temp_raw * 0.2), 5, 100)

    df = pd.DataFrame({
        "cpu_raw": cpu_raw, "ram_raw": ram_raw, "disk_raw": disk_raw,
        "temperature_raw": temp_raw, "humidity_raw": hum_raw,
        "fan_raw": fan_raw, "dust_raw": dust_raw, "battery_raw": bat_raw,
    })

    norm_names = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]
    divisors   = [100, 100, 100, 120, 100, 5000, 100, 100]
    for raw, norm, div in zip(
        ["cpu_raw","ram_raw","disk_raw","temperature_raw","humidity_raw","fan_raw","dust_raw","battery_raw"],
        norm_names, divisors
    ):
        df[norm] = (df[raw] / div).clip(0, 1)

    df["label"] = (
        (df["cpu"] > 0.75).astype(int) +
        (df["ram"] > 0.75).astype(int) +
        (df["disk"] > 0.80).astype(int) +
        (df["temperature"] > 0.65).astype(int) +
        (df["fan"] > 0.70).astype(int) +
        (df["humidity"] > 0.75).astype(int)
    )
    df["label"] = (df["label"] >= 2).astype(int)

    scaler = MinMaxScaler()
    df[norm_names] = scaler.fit_transform(df[norm_names])
    save_dir = os.path.dirname(out_path) or "."
    print("Saving scaler to:", save_dir)   # 👈 debug print (important)
    os.makedirs(save_dir, exist_ok=True)
    joblib.dump(scaler, os.path.join(save_dir, "scaler.pkl"))

    df.to_csv(out_path, index=False)
    print(f"✅ Simulated dataset saved → {out_path}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env",  type=str, default=None, help="Path to env sensor CSV")
    parser.add_argument("--sys",  type=str, default=None, help="Path to system resources CSV")
    parser.add_argument("--out",  type=str, default="../backend/cleaned_dataset.csv")
    parser.add_argument("--rows", type=int, default=10000)
    args = parser.parse_args()

    if args.env and args.sys:
        build_merged_dataset(args.env, args.sys, args.rows, args.out)
    else:
        print("⚠️  No CSV paths given — running in simulation mode.")
        generate_simulated_dataset(args.rows, args.out)