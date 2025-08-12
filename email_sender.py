import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your_email_password")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
APP_URL = os.getenv("APP_URL", "http://localhost")

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("email_template.html")


def send_email(to_email, approval_data):
    try:
        body_html = template.render(
            head_name=approval_data["head_name"],
            nama_program=approval_data["nama_program"],
            judul_episode=approval_data["judul_episode"],
            inisiator=approval_data["inisiator"],
            app_url=APP_URL,
            approval_uuid=approval_data["approval_uuid"],
        )
        msg = MIMEText(body_html, "html")
        msg["Subject"] = "Reminder: Approval Content > 24 Jam Pending"
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[{datetime.now()}] Email terkirim ke {to_email}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Gagal kirim email ke {to_email}: {e}")
        return False
