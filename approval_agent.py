#!/usr/bin/env python3
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv
import os
import time
from jinja2 import Environment, FileSystemLoader
import signal
import sys

# Load env vars
load_dotenv()

# DB config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "production_requests"),
}

# SMTP config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your_email_password")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

# App URL for links in email
APP_URL = os.getenv("APP_URL", "http://localhost")

# Check interval in minutes
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", 10))

# Setup Jinja2 template env
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("email_template.html")

# SQL to get pending approvals > 24h
SQL_GET_PENDING = """
SELECT pa.id, pa.uuid, pa.program_request_id, pa.status, pa.created_at,
       head.name as head_name, head.email,
       pr.nama_program, pr.judul_episode,
       creator.name as pembuat
FROM program_approvals pa
JOIN users head ON head.id = pa.head_user_id
JOIN program_requests pr ON pr.id = pa.program_request_id
JOIN users creator ON creator.id = pr.user_id
WHERE pa.status = 'pending'
  AND TIMESTAMPDIFF(HOUR, pa.created_at, NOW()) > 24
"""

# Check last sent email log for approval
SQL_CHECK_LOG = """
SELECT sent_at FROM approval_email_logs
WHERE approval_id = %s
ORDER BY sent_at DESC
LIMIT 1
"""

# Insert new email log
SQL_INSERT_LOG = """
INSERT INTO approval_email_logs (approval_id) VALUES (%s)
"""


def send_email(to_email, approval_data):
    try:
        body_html = template.render(
            head_name=approval_data["head_name"],
            nama_program=approval_data["nama_program"],
            judul_episode=approval_data["judul_episode"],
            pembuat=approval_data["pembuat"],
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
    except Exception as e:
        print(f"[{datetime.now()}] Gagal kirim email ke {to_email}: {e}")


def can_send_email(cursor, approval_id):
    cursor.execute(SQL_CHECK_LOG, (approval_id,))
    last_sent = cursor.fetchone()
    if not last_sent:
        return True
    sent_at = last_sent["sent_at"]
    now = datetime.now()
    diff = now - sent_at
    return diff.total_seconds() > 24 * 3600  # lebih dari 24 jam


def check_approvals():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(SQL_GET_PENDING)
        results = cursor.fetchall()

        if not results:
            print(f"[{datetime.now()}] Tidak ada approval pending > 24 jam.")
        else:
            for row in results:
                approval_id = row["id"]
                if can_send_email(cursor, approval_id):
                    approval_data = {
                        "head_name": row["head_name"],
                        "nama_program": row["nama_program"],
                        "judul_episode": row["judul_episode"],
                        "pembuat": row["pembuat"],
                        "approval_uuid": row["uuid"],
                    }
                    send_email(row["email"], approval_data)
                    cursor.execute(SQL_INSERT_LOG, (approval_id,))
                    conn.commit()
                else:
                    print(
                        f"[{datetime.now()}] Email untuk approval {approval_id} sudah dikirim dalam 24 jam terakhir, skip."
                    )

    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


# Graceful shutdown setup
running = True


def signal_handler(sig, frame):
    global running
    print(f"\n[{datetime.now()}] Dapat sinyal stop, shutting down dengan rapi...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print(f"[{datetime.now()}] Agent started. Interval {CHECK_INTERVAL_MINUTES} menit.")
    while running:
        check_approvals()
        for _ in range(CHECK_INTERVAL_MINUTES * 60):
            if not running:
                break
            time.sleep(1)

    print(f"[{datetime.now()}] Agent sudah berhenti dengan rapi.")
    sys.exit(0)
