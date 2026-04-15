#alert_manager.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "receiver@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

def send_alert(metrics, risk, streak, reason="High Risk"):
    if not EMAIL_PASSWORD:
        print("❌ EMAIL_PASSWORD not set")
        return False

    msg = MIMEMultipart()
    msg["Subject"] = f"🚨 Alert {round(risk*100,1)}%"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    body = f"""
    Risk: {risk}
    Streak: {streak}
    Reason: {reason}
    CPU: {metrics.get('cpu_raw')}
    """

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Email Sent")
        return True
    except Exception as e:
        print(e)
        return False