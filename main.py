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
)
from email_sender import send_email

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", 10))

running = True


def can_send_email(conn, approval_id):
    last_sent = get_last_email_log(conn, approval_id)
    if not last_sent:
        return True
    sent_at = last_sent["sent_at"]
    now = datetime.now()
    diff = now - sent_at
    return diff.total_seconds() > 24 * 3600  # lebih dari 24 jam


def check_approvals():
    try:
        conn = get_connection()
        approvals = fetch_pending_approvals(conn)

        if not approvals:
            print(f"[{datetime.now()}] Tidak ada approval pending > 24 jam.")
        else:
            for row in approvals:
                approval_id = row["id"]
                if can_send_email(conn, approval_id):
                    approval_data = {
                        "head_name": row["head_name"],
                        "nama_program": row["nama_program"],
                        "judul_episode": row["judul_episode"],
                        "pembuat": row["pembuat"],
                        "approval_uuid": row["uuid"],
                    }
                    if send_email(row["email"], approval_data):
                        insert_email_log(conn, approval_id)
                else:
                    print(
                        f"[{datetime.now()}] Email untuk approval {approval_id} sudah dikirim dalam 24 jam terakhir, skip."
                    )

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
