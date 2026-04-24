"""
prepare_dataset.py
Cleans Kaggle datasets and builds training data.
Falls back to simulation if CSVs not provided.

Usage:
  python prepare_dataset.py --env env_sensor.csv --sys system_resources.csv
  python prepare_dataset.py   # simulation mode
"""

import argparse
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib

FEATURES   = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]
RAW_COLS   = ["cpu_raw","ram_raw","disk_raw","temperature_raw",
              "humidity_raw","fan_raw","dust_raw","battery_raw"]
DIVISORS   = [100, 100, 100, 120, 100, 5000, 100, 100]


# ─── Cleaners ────────────────────────────────────────────────────────────────

def clean_env_dataset(path: str, n: int) -> pd.DataFrame:
    """Kaggle: garystafford/environmental-sensor-data-132k"""
    df = pd.read_csv(path)
    print(f"  ENV raw shape: {df.shape}")

    rename = {}
    for col in df.columns:
        lc = col.lower().strip()
        if lc in ("temp", "temperature"):
            rename[col] = "temperature_raw"
        elif lc == "humidity":
            rename[col] = "humidity_raw"
    df = df.rename(columns=rename)

    needed = [c for c in ["temperature_raw", "humidity_raw"] if c in df.columns]
    if not needed:
        raise ValueError("ENV CSV must have 'temp'/'temperature' and 'humidity' columns")

    df = df[needed].dropna()

    if "temperature_raw" in df.columns:
        df = df[(df["temperature_raw"] > 0) & (df["temperature_raw"] < 120)]
    if "humidity_raw" in df.columns:
        df = df[(df["humidity_raw"] >= 0) & (df["humidity_raw"] <= 100)]

    df = df.sample(min(n, len(df)), random_state=42).reset_index(drop=True)
    print(f"  ENV cleaned shape: {df.shape}")
    return df


def clean_sys_dataset(path: str, n: int) -> pd.DataFrame:
    """Kaggle: omnamahshivai/dataset-system-resources-cpu-ram-disk-network"""
    df = pd.read_csv(path)
    print(f"  SYS raw shape: {df.shape}")

    rename = {}
    for col in df.columns:
        lc = col.lower().strip().replace(" ", "_")
        if "cpu" in lc and "percent" in lc:
            rename[col] = "cpu_raw"
        elif ("mem" in lc or "ram" in lc) and "percent" in lc:
            rename[col] = "ram_raw"
        elif "disk" in lc and "percent" in lc:
            rename[col] = "disk_raw"

    df = df.rename(columns=rename)
    needed = [c for c in ["cpu_raw", "ram_raw", "disk_raw"] if c in df.columns]
    if len(needed) < 2:
        raise ValueError("SYS CSV must have cpu_percent, memory_percent, disk_percent")

    df = df[needed].dropna()
    for col in needed:
        df = df[(df[col] >= 0) & (df[col] <= 100)]

    df = df.sample(min(n, len(df)), random_state=42).reset_index(drop=True)
    print(f"  SYS cleaned shape: {df.shape}")
    return df


def simulate_derived(df: pd.DataFrame, rng) -> pd.DataFrame:
    """Derive fan, dust, battery from real data columns."""
    cpu  = df["cpu_raw"].values
    temp = df["temperature_raw"].values
    disk = df["disk_raw"].values

    fan  = np.clip(temp * 35 + cpu * 18 + rng.normal(0, 80, len(df)), 0, 5000)
    dust = np.clip(disk * 0.25 + fan * 0.004 + rng.uniform(0, 10, len(df)), 0, 100)
    bat  = np.clip(100 - (cpu * 0.3 + temp * 0.2) + rng.normal(0, 3, len(df)), 5, 100)

    df["fan_raw"]     = fan
    df["dust_raw"]    = dust
    df["battery_raw"] = bat
    return df


# ─── Label builder (shared) ───────────────────────────────────────────────────

def build_labels(df: pd.DataFrame) -> pd.DataFrame:
    df["label"] = (
        (df["cpu"]         > 0.75).astype(int) +
        (df["ram"]         > 0.75).astype(int) +
        (df["disk"]        > 0.80).astype(int) +
        (df["temperature"] > 0.65).astype(int) +
        (df["fan"]         > 0.70).astype(int) +
        (df["humidity"]    > 0.75).astype(int)
    )
    df["label"] = (df["label"] >= 2).astype(int)
    return df


# ─── Real Kaggle data path ────────────────────────────────────────────────────

def build_merged_dataset(env_path, sys_path, n_rows, out_path):
    rng = np.random.default_rng(42)

    print("\n[1] Cleaning ENV dataset...")
    env_df = clean_env_dataset(env_path, n_rows)

    print("\n[2] Cleaning SYS dataset...")
    sys_df = clean_sys_dataset(sys_path, n_rows)

    n = min(len(env_df), len(sys_df), n_rows)
    env_df = env_df.iloc[:n].reset_index(drop=True)
    sys_df = sys_df.iloc[:n].reset_index(drop=True)

    print(f"\n[3] Merging {n} rows...")
    df = pd.concat([sys_df, env_df], axis=1)

    # Fill any missing raw cols with defaults so simulate_derived works
    for col, default in [("cpu_raw", 50), ("ram_raw", 50), ("disk_raw", 50),
                          ("temperature_raw", 40), ("humidity_raw", 50)]:
        if col not in df.columns:
            df[col] = default

    print("\n[4] Simulating fan, dust, battery...")
    df = simulate_derived(df, rng)

    # Normalise
    for raw, norm, div in zip(RAW_COLS, FEATURES, DIVISORS):
        df[norm] = (df[raw] / div).clip(0, 1)

    df = build_labels(df)
    print(f"\n[5] Label distribution:\n{df['label'].value_counts()}")

    scaler = MinMaxScaler()
    df[FEATURES] = scaler.fit_transform(df[FEATURES])
    _save_scaler(scaler, out_path)

    df.to_csv(out_path, index=False)
    print(f"\n✅ Saved → {out_path}  ({len(df)} rows)")
    return df


# ─── Pure simulation fallback ─────────────────────────────────────────────────

def generate_simulated_dataset(n_rows, out_path):
    print(f"\n[SIMULATION MODE] Generating {n_rows} rows...")
    rng = np.random.default_rng(42)

    cpu  = rng.uniform(5,  95, n_rows)
    ram  = rng.uniform(10, 95, n_rows)
    disk = rng.uniform(5,  90, n_rows)
    temp = np.clip(30 + cpu * 0.45 + rng.normal(0, 3, n_rows), 20, 100)
    hum  = np.clip(30 + temp * 0.15 + rng.normal(0, 4, n_rows), 20, 90)
    fan  = np.clip(temp * 35 + cpu * 18 + rng.normal(0, 80, n_rows), 0, 5000)
    dust = np.clip(disk * 0.25 + fan * 0.004 + rng.uniform(0, 10, n_rows), 0, 100)
    bat  = np.clip(100 - (cpu * 0.3 + temp * 0.2), 5, 100)

    raw = {"cpu_raw": cpu, "ram_raw": ram, "disk_raw": disk,
           "temperature_raw": temp, "humidity_raw": hum,
           "fan_raw": fan, "dust_raw": dust, "battery_raw": bat}
    df = pd.DataFrame(raw)

    for r, n, d in zip(RAW_COLS, FEATURES, DIVISORS):
        df[n] = (df[r] / d).clip(0, 1)

    df = build_labels(df)

    scaler = MinMaxScaler()
    df[FEATURES] = scaler.fit_transform(df[FEATURES])
    _save_scaler(scaler, out_path)

    df.to_csv(out_path, index=False)
    print(f"✅ Simulated dataset saved → {out_path}")
    return df


def _save_scaler(scaler, out_path):
    d = os.path.dirname(out_path) or "."
    p = os.path.join(d, "scaler.pkl")
    joblib.dump(scaler, p)
    print(f"💾 scaler.pkl saved → {p}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env",  type=str, default=None)
    parser.add_argument("--sys",  type=str, default=None)
    parser.add_argument("--out",  type=str, default="cleaned_dataset.csv")
    parser.add_argument("--rows", type=int, default=10000)
    args = parser.parse_args()

    if args.env and args.sys:
        build_merged_dataset(args.env, args.sys, args.rows, args.out)
    else:
        print("⚠️  No CSV paths provided — running in simulation mode.")
        generate_simulated_dataset(args.rows, args.out)