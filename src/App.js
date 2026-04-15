import React, { useState, useEffect, useRef, useCallback } from "react";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import "./App.css";
import { PieChart, Pie, Cell, Tooltip } from "recharts";

const API = "http://localhost:5000/predict";

function App() {
  const [loggedIn, setLoggedIn]   = useState(false);
  const [metrics, setMetrics]     = useState({});
  const [health, setHealth]       = useState(null);
  const [message, setMessage]     = useState("");
  const [severity, setSeverity]   = useState("healthy");
  const [alertSent, setAlertSent] = useState(false);
  const [streak, setStreak]       = useState(0);
  const intervalRef               = useRef(null);


  
  const fetchMetrics = useCallback(async () => {
    try {
      const res  = await fetch(API);
      if (!res.ok) throw new Error("Non-200");
      const data = await res.json();

      setMetrics(data.metrics);
      setSeverity(data.severity);
      setAlertSent(data.alert_sent);
      setStreak(data.high_risk_streak);

      const healthValue = Math.max(0, 100 - data.risk * 100);
      setHealth(healthValue);
      setMessage(data.status);
    } catch {
      setMessage("Backend not connected ❌");
    }
  }, []);

  useEffect(() => {
    if (!loggedIn) return;

    fetchMetrics();
    intervalRef.current = setInterval(fetchMetrics, 2000);

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        fetchMetrics();
        clearInterval(intervalRef.current);
        intervalRef.current = setInterval(fetchMetrics, 2000);
      } else {
        clearInterval(intervalRef.current);
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      clearInterval(intervalRef.current);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [loggedIn, fetchMetrics]);

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;

  const chartData = [
    { name: "Health", value: health || 0 },
    { name: "Used",   value: 100 - (health || 0) },
  ];

  const COLORS =
    severity === "critical"
      ? ["#ff2d55", "#0a0f1a"]
      : severity === "warning"
      ? ["#ffd60a", "#0a0f1a"]
      : ["#00d4ff", "#0a0f1a"];

  const healthColor =
    severity === "critical" ? "#ff2d55" :
    severity === "warning"  ? "#ffd60a" : "#00ff88";

  return (
    <>
      {/* ambient bg layer */}
      <div className="app-bg" />

      <div className="app">
        {/* ── NAVBAR ── */}
        <nav className="navbar">
          <h2 className="logo">DeviceGuard</h2>
          <ul>
            <li>Products</li>
            <li>Features</li>
            <li>Analytics</li>
            <li>AI Monitor</li>
          </ul>
          <button className="btn">Dashboard</button>
        </nav>

        {/* ── HERO ── */}
        <section className="hero">
          <div className="hero-text">
            <div className="hero-eyebrow">System Intelligence Active</div>

            <h1>
              AI Powered
              <span>Device Monitoring</span>
            </h1>

            <p>
              Monitor CPU, RAM, temperature and anomalies
              using real-time AI-powered insights.
            </p>

            <p className="live-tag">🟢 Live Monitoring Active</p>

            {alertSent && (
              <div className="alert-sent-badge">
                📧 Alert emailed to IT dept &nbsp;·&nbsp; streak: {streak} checks
              </div>
            )}
          </div>

          {/* ── HERO CARD ── */}
          <div className="hero-card">
            <div className="output-title">AI Monitoring Output</div>

            <div className="output-box">
              {health === null ? (
                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, color: "#4a7090", letterSpacing: 2 }}>
                  Awaiting signal...
                </p>
              ) : (
                <>
                  <PieChart width={200} height={200}>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={58}
                      outerRadius={76}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "#05101f",
                        border: "1px solid rgba(0,212,255,0.2)",
                        borderRadius: 6,
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 12,
                        color: "#e8f4ff",
                      }}
                    />
                  </PieChart>

                  {/* Live Metrics Grid */}
                  <div className="metrics-live">
                    <p>CPU&nbsp;&nbsp;{metrics.cpu ?? "--"}%</p>
                    <p>RAM&nbsp;&nbsp;{metrics.ram ?? "--"}%</p>
                    <p>DISK&nbsp;{metrics.disk ?? "--"}%</p>
                    <p>TEMP&nbsp;{metrics.temperature ?? "--"}°C</p>
                    <p>HUM&nbsp;&nbsp;{metrics.humidity ?? "--"}%</p>
                    <p>FAN&nbsp;&nbsp;{metrics.fan ?? "--"} RPM</p>
                    <p>BAT&nbsp;&nbsp;{metrics.battery ?? "--"}%</p>
                  </div>

                  {/* Health score */}
                  <div
                    className="health-score"
                    style={{ color: healthColor, textShadow: `0 0 20px ${healthColor}` }}
                  >
                    {health.toFixed(1)}
                    <span style={{ fontSize: "0.6em", opacity: 0.6, letterSpacing: 2 }}>%</span>
                  </div>

                  {severity === "critical" ? (
                    <div className="alert-box critical">⚠ CRITICAL: Immediate action required</div>
                  ) : severity === "warning" ? (
                    <div className="alert-box warning">⚠ WARNING: Degradation detected</div>
                  ) : (
                    <p className="ai-message">✓ {message}</p>
                  )}
                </>
              )}
            </div>
          </div>
        </section>

        {/* ── DASHBOARD ── */}
        <section>
          <div className="section-header">
            <h2 className="section-title">System Dashboard</h2>
            <div className="section-line" />
            <span className="section-badge">8 sensors · live</span>
          </div>
          <Dashboard metrics={metrics} />
        </section>
      </div>
    </>
  );
}

export default App;