#main.py
import time
import threading
from datetime import datetime
from collections import deque

import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
import joblib

from metrics_collector import get_system_metrics
from alert_manager import send_alert

app = Flask(__name__)
CORS(app)

model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")

FEATURES = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]

latest_result = {}
history = deque(maxlen=100)

alert_sent = False
high_risk_count = 0

RISK_THRESHOLD = 0.7
STREAK_TRIGGER = 5
INTERVAL = 5

def check_system():
    global latest_result, alert_sent, high_risk_count

    data = get_system_metrics()

    X = pd.DataFrame([{f: data[f] for f in FEATURES}])
    X_scaled = scaler.transform(X)

    prob = model.predict_proba(X_scaled)[0][1]

    if prob >= RISK_THRESHOLD:
        high_risk_count += 1
    else:
        high_risk_count = 0
        alert_sent = False

    if high_risk_count >= STREAK_TRIGGER and not alert_sent:
        send_alert(data, prob, high_risk_count)
        alert_sent = True

    result = {
        "metrics": data,
        "risk": prob,
        "status": "⚠ Warning" if prob > 0.6 else "✅ Healthy",
        "timestamp": datetime.now().isoformat()
    }

    latest_result = result
    history.append(result)

def loop():
    while True:
        check_system()
        time.sleep(INTERVAL)

@app.route("/predict")
def predict():
    return jsonify(latest_result)

@app.route("/history")
def get_history():
    return jsonify(list(history))

if __name__ == "__main__":
    check_system()
    threading.Thread(target=loop, daemon=True).start()
    app.run(port=5000)