import React from "react";
import "./Dashboard.css";


const CARDS = [
  { label: "CPU Usage",      key: "cpu",         unit: "%",   icon: "⚡", max: 100 },
  { label: "RAM Usage",      key: "ram",         unit: "%",   icon: "🧠", max: 100 },
  { label: "Disk Usage",     key: "disk",        unit: "%",   icon: "💾", max: 100 },
  { label: "Fan Speed",      key: "fan",         unit: "RPM", icon: "🌀", max: 5000 },
  { label: "Temperature",    key: "temperature", unit: "°C",  icon: "🌡", max: 100 },
  { label: "Dust Level",     key: "dust",        unit: "%",   icon: "🌫", max: 100 },
  { label: "Battery Health", key: "battery",     unit: "%",   icon: "🔋", max: 100 },
  { label: "Humidity",       key: "humidity",    unit: "%",   icon: "💧", max: 100 },
];

function getState(key, value) {
  if (value === undefined || value === null) return "normal";
  const v = Number(value);
  if (key === "temperature") {
    if (v > 85) return "critical";
    if (v > 70) return "warning";
    return "normal";
  }
  if (key === "fan") {
    if (v > 4000) return "critical";
    if (v > 3000) return "warning";
    return "normal";
  }
  if (v > 85) return "critical";
  if (v > 70) return "warning";
  return "normal";
}

function getBarColor(key, value, state) {
  if (state === "critical") return "#ff2d55";
  if (state === "warning")  return "#ffd60a";
  const palette = {
    cpu:         "#00d4ff",
    ram:         "#7b2fff",
    disk:        "#00a8ff",
    fan:         "#00ffe5",
    temperature: "#ff6b35",
    dust:        "#a8a8a8",
    battery:     "#00ff88",
    humidity:    "#4fc3f7",
  };
  return palette[key] || "#00d4ff";
}

function getStatusText(state) {
  if (state === "critical") return "CRITICAL";
  if (state === "warning")  return "WARNING";
  return "NOMINAL";
}

export default function Dashboard({ metrics }) {
  return (
    <div className="dashboard">
      {CARDS.map(({ label, key, unit, icon, max }, idx) => {
        const raw   = metrics[key];
        const value = raw !== undefined ? Number(raw) : null;
        const pct   = value !== null ? Math.min(100, (value / max) * 100) : 0;
        const state = value !== null ? getState(key, value) : "normal";
        const color = getBarColor(key, value, state);

        return (
          <div className={`metric-card state-${state}`} key={key}>
            <span className="card-index">{String(idx + 1).padStart(2, "0")}</span>

            <span className="metric-icon">{icon}</span>

            <div className="metric-label">{label}</div>

            <div className="metric-value">
              {value !== null ? value : "--"}
              <span className="unit">{unit}</span>
            </div>

            <div className="metric-bar-bg">
              <div
                className="metric-bar-fill"
                style={{
                  width: `${pct}%`,
                  background: color,
                  boxShadow: `0 0 6px ${color}`,
                }}
              />
            </div>

            <div className="metric-status">
              <span
                className="status-dot"
                style={{
                  background: color,
                  boxShadow: `0 0 6px ${color}`,
                }}
              />
              {getStatusText(state)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

import "./Login.css";

export default function Login({ onLogin }) {
  return (
    <div className="login-container">
      <div className="login-grid" />

      <div className="login-card">
        <h1 className="login-logo">DeviceGuard</h1>
        <p className="login-tag">AI · Powered · Device · Security</p>

        <div className="login-input-group">
          <label className="login-input-label">Full Name</label>
          <input type="text" placeholder="Enter your name" />
        </div>

        <div className="login-input-group">
          <label className="login-input-label">Email Address</label>
          <input type="email" placeholder="you@company.com" />
        </div>

        <div className="login-input-group">
          <label className="login-input-label">Password</label>
          <input type="password" placeholder="••••••••••••" />
        </div>

        <div className="login-divider" />

        <button className="login-btn" onClick={onLogin}>
          Initialize Session
        </button>

        <p className="login-footer">
          Secured · Encrypted · v2.4.1
        </p>
      </div>
    </div>
  );
}
const BASE = "http://localhost:5000";

export const fetchPredict   = () => fetch(`${BASE}/predict`).then(r => r.json());
export const fetchHistory   = (n=50) => fetch(`${BASE}/history?n=${n}`).then(r => r.json());
export const postTestAlert  = () => fetch(`${BASE}/test-alert`, { method: "POST" }).then(r => r.json());
export const fetchHealth    = () => fetch(`${BASE}/health`).then(r => r.json());
import React from "react";
import "./Login.css";

export default function Login({ onLogin }) {
  return (
    <div className="login-container">
      <div className="login-grid" />

      <div className="login-card">
        <h1 className="login-logo">DeviceGuard</h1>
        <p className="login-tag">AI · Powered · Device · Security</p>

        <div className="login-input-group">
          <label className="login-input-label">Full Name</label>
          <input type="text" placeholder="Enter your name" />
        </div>

        <div className="login-input-group">
          <label className="login-input-label">Email Address</label>
          <input type="email" placeholder="you@company.com" />
        </div>

        <div className="login-input-group">
          <label className="login-input-label">Password</label>
          <input type="password" placeholder="••••••••••••" />
        </div>

        <div className="login-divider" />

        <button className="login-btn" onClick={onLogin}>
          Initialize Session
        </button>

        <p className="login-footer">
          Secured · Encrypted · v2.4.1
        </p>
      </div>
    </div>
  );
}
