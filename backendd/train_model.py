#train_model.py
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

from preprocessing import load_and_process

FEATURES = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]

print("🔄 Loading dataset …")
df, features = load_and_process(n_rows=5000, save_scaler=True)

# Label creation
df["label"] = (
    (df["cpu"] > 0.75).astype(int) +
    (df["ram"] > 0.75).astype(int) +
    (df["disk"] > 0.80).astype(int) +
    (df["temperature"] > 0.65).astype(int) +
    (df["fan"] > 0.70).astype(int) +
    (df["humidity"] > 0.75).astype(int)
)
df["label"] = (df["label"] >= 2).astype(int)

X = df[FEATURES]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_leaf=4,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\nAccuracy:", model.score(X_test, y_test))
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

joblib.dump(model, "model.pkl")
print("✅ model.pkl saved")