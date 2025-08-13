#!/usr/bin/env python3
import time
import signal
import sys
import os
from datetime import datetime

from db import (
    get_connection,
    fetch_pending_approvals,
    get_last_email_log,
    insert_email_log,
    get_last_ceo_log,
    insert_ceo_log,
)
from email_sender import send_email

from dotenv import load_dotenv

load_dotenv()

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", 10))
CEO_EMAIL = os.getenv("CEO_EMAIL", "gultom4715@gmail.com")

running = True


def can_send_email(conn, approval_id):
    last_sent = get_last_email_log(conn, approval_id)
    if not last_sent:
        return True
    sent_at = last_sent["sent_at"]
    now = datetime.now()
    diff = now - sent_at
    return diff.total_seconds() > 24 * 3600


def check_approvals():
    try:
        conn = get_connection()
        approvals = fetch_pending_approvals(conn)

        if not approvals:
            print(f"[{datetime.now()}] Tidak ada approval pending > 24 jam.")
        else:
            program_requests_seen = set()

            for row in approvals:
                approval_id = row["id"]
                program_request_id = row["program_request_id"]
                judul_episode = row["judul_episode"]

                # Kirim email ke head
                if can_send_email(conn, approval_id):
                    approval_data = {
                        "head_name": row["head_name"],
                        "nama_program": row["nama_program"],
                        "judul_episode": row["judul_episode"],
                        "inisiator": row["inisiator"],
                        "approval_uuid": row["uuid"],
                    }
                    if send_email(row["email"], approval_data):
                        insert_email_log(conn, approval_id)
                else:
                    print(
                        f"[{datetime.now()}] Email head '{judul_episode}' sudah dikirim <24 jam, skip."
                    )

                # Kirim email ke CEO sekali per program_request_id
                if program_request_id not in program_requests_seen:
                    last_ceo_sent = get_last_ceo_log(conn, program_request_id)
                    if not last_ceo_sent:
                        ceo_data = {
                            "head_name": "CEO",
                            "nama_program": row["nama_program"],
                            "judul_episode": row["judul_episode"],
                            "inisiator": row["inisiator"],
                            "approval_uuid": row["uuid"],
                        }
                        if send_email(CEO_EMAIL, ceo_data):
                            insert_ceo_log(conn, program_request_id)
                    program_requests_seen.add(program_request_id)

        conn.close()
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")


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
