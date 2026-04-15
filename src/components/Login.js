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