"""
main.py  –  Flask backend
Endpoints:
  POST /login          — user auth (demo credentials)
  GET  /predict        — latest metrics + risk for THIS machine
  GET  /history        — rolling 100-point history
  GET  /history/all    — full stored history (IT dashboard)
  POST /history/clear  — reset stored history
"""

import os
import time
import uuid
import json
import threading
from datetime import datetime
from collections import deque

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib

from metrics_collector import get_system_metrics
from alert_manager import send_alert, is_genuine_issue

app = Flask(__name__)
CORS(app)

# ── Auth (demo — replace with DB in production) ───────────────────────────────
USERS = {
    "user@demo.com":    {"password": "user123",  "role": "user",  "name": "Student User"},
    "it@dept.com":      {"password": "itadmin",  "role": "admin", "name": "IT Admin"},
}

SESSION_STORE = {}   # token -> {email, role, name}

# ── Model ─────────────────────────────────────────────────────────────────────
model  = joblib.load("../model.pkl")
scaler = joblib.load("../scaler.pkl")

FEATURES = ["cpu", "ram", "disk", "temperature", "humidity", "fan", "dust", "battery"]

# ── State ─────────────────────────────────────────────────────────────────────
PC_NUMBER      = os.getenv("PC_NUMBER", f"PC-{os.getpid() % 1000:03d}")
latest_result  = {}
history        = deque(maxlen=200)
alert_sent     = False
high_risk_count = 0

RISK_THRESHOLD  = 0.70
STREAK_TRIGGER  = 5
INTERVAL        = 5


# ── Background loop ───────────────────────────────────────────────────────────

def check_system():
    global latest_result, alert_sent, high_risk_count

    data = get_system_metrics()
    X = pd.DataFrame([{f: data[f] for f in FEATURES}])
    X_scaled = scaler.transform(X)
    prob = float(model.predict_proba(X_scaled)[0][1])

    if prob >= RISK_THRESHOLD:
        high_risk_count += 1
    else:
        high_risk_count = 0
        alert_sent = False

    if high_risk_count >= STREAK_TRIGGER and not alert_sent:
        genuine, reason = is_genuine_issue(data, prob, high_risk_count)
        if genuine:
            send_alert(data, prob, high_risk_count, pc_number=PC_NUMBER, reason=reason)
            alert_sent = True

    if prob >= 0.85:
        status = "CRITICAL"
    elif prob >= 0.70:
        status = "HIGH RISK"
    elif prob >= 0.50:
        status = "WARNING"
    else:
        status = "HEALTHY"

    result = {
        "pc_number":  PC_NUMBER,
        "metrics":    data,
        "risk":       round(prob, 4),
        "risk_pct":   round(prob * 100, 1),
        "status":     status,
        "streak":     high_risk_count,
        "timestamp":  datetime.now().isoformat(),
    }

    latest_result = result
    history.append(result)


def loop():
    while True:
        try:
            check_system()
        except Exception as e:
            print(f"[loop error] {e}")
        time.sleep(INTERVAL)


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@app.route("/login", methods=["POST"])
def login():
    body = request.get_json() or {}
    email    = body.get("email", "").strip().lower()
    password = body.get("password", "")

    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    token = str(uuid.uuid4())
    SESSION_STORE[token] = {"email": email, "role": user["role"], "name": user["name"]}
    return jsonify({"token": token, "role": user["role"], "name": user["name"]})


@app.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    SESSION_STORE.pop(token, None)
    return jsonify({"ok": True})


def auth_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in SESSION_STORE:
            return jsonify({"error": "Unauthorized"}), 401
        request.user = SESSION_STORE[token]
        return fn(*args, **kwargs)
    return wrapper


# ── Data endpoints ─────────────────────────────────────────────────────────────

@app.route("/predict")
def predict():
    return jsonify(latest_result)


@app.route("/history")
def get_history():
    return jsonify(list(history))


@app.route("/status")
def status():
    return jsonify({"pc_number": PC_NUMBER, "uptime_checks": len(history)})


if __name__ == "__main__":
    check_system()
    threading.Thread(target=loop, daemon=True).start()
    app.run(port=5000, debug=False)