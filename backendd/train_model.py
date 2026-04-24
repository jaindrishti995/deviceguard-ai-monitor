"""
train_model.py
Trains a Random Forest classifier and saves model.pkl + scaler.pkl.

Usage:
  python train_model.py                          # uses simulation
  python train_model.py --data cleaned_dataset.csv
"""

import argparse
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import MinMaxScaler

from preprocessing import generate_simulated_dataset, FEATURES

DATA_PATH   = "cleaned_dataset.csv"
MODEL_PATH  = "model.pkl"
SCALER_PATH = "scaler.pkl"


def train(data_path=DATA_PATH):
    try:
        df = pd.read_csv(data_path)
        print(f"📂 Loaded dataset: {df.shape}")
    except FileNotFoundError:
        print(f"⚠️  {data_path} not found — generating simulation data...")
        df = generate_simulated_dataset(10000, data_path)

    X = df[FEATURES].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n🏋️  Training on {len(X_train)} samples...")
    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    print("\n📊 Evaluation on test set:")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Healthy", "At Risk"]))

    joblib.dump(clf, MODEL_PATH)
    print(f"✅ model.pkl saved → {MODEL_PATH}")

    # Importance
    imp = sorted(zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1])
    print("\n📌 Feature importances:")
    for feat, score in imp:
        bar = "█" * int(score * 40)
        print(f"  {feat:12s} {bar} {score:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=DATA_PATH)
    args = parser.parse_args()
    train(args.data)