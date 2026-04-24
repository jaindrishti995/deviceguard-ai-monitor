"""
alert_manager.py
----------------
Smart email alerts to the IT department.
- Suppresses noise (temporary spikes during downloads / many tabs)
- Includes PC number and risk level in email
- Sends HTML-formatted email to IT dashboard
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER_EMAIL   = os.getenv("SENDER_EMAIL",   "your_email@gmail.com")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "it_dept@example.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")


# ── Risk level helper ─────────────────────────────────────────────────────────

def risk_level(risk: float) -> tuple[str, str]:
    """Returns (label, hex_color) for the risk score."""
    if risk >= 0.85:
        return "CRITICAL",  "#e53e3e"
    elif risk >= 0.70:
        return "HIGH",      "#dd6b20"
    elif risk >= 0.50:
        return "MEDIUM",    "#d69e2e"
    else:
        return "LOW",       "#38a169"


# ── Smart suppression logic ───────────────────────────────────────────────────

def is_genuine_issue(metrics: dict, risk: float, streak: int) -> tuple[bool, str]:
    """
    Returns (should_alert, reason_string).

    Rules to SUPPRESS false positives:
    - High CPU but very high RAM too → likely browser/app spike (temp, not hardware)
      → only alert if DISK or TEMPERATURE is also elevated
    - Fan spike without temperature rise → sensor noise
    - Short streak (< 5) → transient load, not degradation

    Rules to ALERT:
    - Temperature >= 75°C regardless of other factors (thermal risk)
    - Disk >= 90% (storage emergency)
    - Sustained high-risk for >= 5 consecutive checks
    - Multiple metrics elevated simultaneously (genuine system stress)
    """
    cpu   = metrics.get("cpu_raw", 0)
    ram   = metrics.get("ram_raw", 0)
    disk  = metrics.get("disk_raw", 0)
    temp  = metrics.get("temperature_raw", 0)
    fan   = metrics.get("fan_raw", 0)
    bat   = metrics.get("battery_raw", 100)

    reasons = []

    # Critical single-metric thresholds (immediate alert)
    if temp >= 80:
        reasons.append(f"Critical temperature: {temp}°C")
    if disk >= 90:
        reasons.append(f"Disk critically full: {disk}%")
    if bat <= 10:
        reasons.append(f"Battery critically low: {bat}%")

    if reasons:
        return True, " | ".join(reasons)

    # Sustained multi-metric degradation
    elevated = sum([
        cpu  > 85,
        ram  > 85,
        disk > 80,
        temp > 70,
        fan  > 3500,
    ])

    # Suppress: high CPU+RAM only (browsing/download spike) without disk/temp elevation
    if elevated == 2 and cpu > 85 and ram > 85 and disk <= 75 and temp <= 65:
        return False, "Suppressed: likely browser/download spike"

    if elevated >= 3 and streak >= 5:
        reasons.append(
            f"Sustained degradation: {elevated} metrics elevated for {streak} checks"
        )
        if cpu  > 85: reasons.append(f"CPU {cpu}%")
        if ram  > 85: reasons.append(f"RAM {ram}%")
        if disk > 80: reasons.append(f"Disk {disk}%")
        if temp > 70: reasons.append(f"Temp {temp}°C")
        return True, " | ".join(reasons)

    return False, "Below threshold"


# ── Email sender ──────────────────────────────────────────────────────────────

def send_alert(metrics: dict, risk: float, streak: int,
               pc_number: str = "UNKNOWN", reason: str = "") -> bool:
    if not EMAIL_PASSWORD:
        print("❌ EMAIL_PASSWORD env var not set — skipping email")
        return False

    level, color = risk_level(risk)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    subject = f"🚨 [{level}] System Alert — PC#{pc_number} — Risk {round(risk*100, 1)}%"

    html_body = f"""
    <html><body style="font-family: 'Segoe UI', sans-serif; background:#0f172a; color:#e2e8f0; padding:24px;">
      <div style="max-width:600px; margin:auto; border:1px solid #334155; border-radius:12px; overflow:hidden;">

        <div style="background:{color}; padding:20px 24px;">
          <h1 style="margin:0; font-size:22px; color:#fff;">
            ⚠️ System Health Alert
          </h1>
          <p style="margin:4px 0 0; font-size:14px; color:rgba(255,255,255,0.85);">
            {now}
          </p>
        </div>

        <div style="padding:24px; background:#1e293b;">
          <table style="width:100%; border-collapse:collapse;">
            <tr>
              <td style="padding:10px; border-bottom:1px solid #334155; color:#94a3b8; width:40%">PC Number</td>
              <td style="padding:10px; border-bottom:1px solid #334155; font-weight:700; font-size:18px;">
                #{pc_number}
              </td>
            </tr>
            <tr>
              <td style="padding:10px; border-bottom:1px solid #334155; color:#94a3b8;">Risk Level</td>
              <td style="padding:10px; border-bottom:1px solid #334155;">
                <span style="background:{color}; color:#fff; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:700;">
                  {level} — {round(risk*100, 1)}%
                </span>
              </td>
            </tr>
            <tr>
              <td style="padding:10px; border-bottom:1px solid #334155; color:#94a3b8;">Consecutive Alerts</td>
              <td style="padding:10px; border-bottom:1px solid #334155;">{streak} checks</td>
            </tr>
            <tr>
              <td style="padding:10px; border-bottom:1px solid #334155; color:#94a3b8;">Reason</td>
              <td style="padding:10px; border-bottom:1px solid #334155; color:#fbbf24;">{reason or "Sustained high risk"}</td>
            </tr>
          </table>

          <h3 style="margin:20px 0 10px; color:#cbd5e1; font-size:14px; text-transform:uppercase; letter-spacing:1px;">
            Current Metrics
          </h3>
          <table style="width:100%; border-collapse:collapse;">
            {"".join([
              f'<tr><td style="padding:8px; color:#94a3b8;">{label}</td>'
              f'<td style="padding:8px; font-weight:600;">{value}</td></tr>'
              for label, value in [
                ("🖥️  CPU",         f"{metrics.get('cpu_raw', '?')}%"),
                ("💾  RAM",         f"{metrics.get('ram_raw', '?')}%"),
                ("💿  Disk",        f"{metrics.get('disk_raw', '?')}%"),
                ("🌡️  Temperature", f"{metrics.get('temperature_raw', '?')}°C"),
                ("💧  Humidity",    f"{metrics.get('humidity_raw', '?')}%"),
                ("🌀  Fan",         f"{metrics.get('fan_raw', '?')} RPM"),
                ("🔋  Battery",     f"{metrics.get('battery_raw', '?')}%"),
              ]
            ])}
          </table>

          <div style="margin-top:24px; padding:14px; background:#0f172a; border-radius:8px; font-size:13px; color:#64748b;">
            Login to the IT Dashboard to view full history and health graphs for PC #{pc_number}.
          </div>
        </div>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Alert email sent for PC#{pc_number} — {level} ({round(risk*100,1)}%)")
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False