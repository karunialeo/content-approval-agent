import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

env = Environment(loader=FileSystemLoader("."))

template_head = env.get_template("email_template.html")
template_ceo = env.get_template("email_template_ceo.html")


def send_email(to_email, approval_data):
    try:
        body_html = template_head.render(**approval_data)
        msg = MIMEText(body_html, "html")
        msg["Subject"] = "Reminder: Approval Content > 24 Jam Pending"
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[{datetime.now()}] Email Head terkirim ke {to_email}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Gagal kirim email ke Head {to_email}: {e}")
        return False


def send_email_to_ceo(to_email, data):
    try:
        body_html = template_ceo.render(**data)
        msg = MIMEText(body_html, "html")
        msg["Subject"] = "Laporan Pending Approval > 24 Jam"
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[{datetime.now()}] Email CEO terkirim ke {to_email}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Gagal kirim email ke CEO {to_email}: {e}")
        return False
