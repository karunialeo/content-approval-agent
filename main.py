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
    get_ceo_user,
    check_ceo_approval_exists,
    insert_ceo_approval,
)
from email_sender import send_email, send_email_to_ceo

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", 10))
running = True


def can_send_email(conn, approval_id, email_type="head"):
    last_sent = get_last_email_log(conn, approval_id, email_type=email_type)
    if not last_sent:
        return True
    sent_at = last_sent["sent_at"]
    diff = datetime.now() - sent_at
    return diff.total_seconds() > 24 * 3600  # >24 jam


def check_approvals():
    conn = get_connection()

    # --- Head email ---
    approvals = fetch_pending_approvals(conn)
    for row in approvals:
        if can_send_email(conn, row["id"], email_type="head"):
            approval_data = {
                "head_name": row["head_name"],
                "nama_program": row["nama_program"],
                "judul_episode": row["judul_episode"],
                "inisiator": row["inisiator"],
                "approval_uuid": row["uuid"],
            }
            if send_email(row["email"], approval_data):
                insert_email_log(conn, row["id"], email_type="head")

        # --- Generate CEO approval if not exists ---
        if not check_ceo_approval_exists(conn, row["program_request_id"]):
            ceo_approval_id = insert_ceo_approval(conn, row["program_request_id"])
            ceo_user = get_ceo_user(conn)
            ceo_data = {
                "ceo_name": ceo_user["name"],
                "nama_program": row["nama_program"],
                "judul_episode": row["judul_episode"],
                "inisiator": row["inisiator"],
            }
            if send_email_to_ceo(ceo_user["email"], ceo_data):
                insert_email_log(
                    conn, program_request_id=row["program_request_id"], email_type="ceo"
                )

    conn.close()


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
