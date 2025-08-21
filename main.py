import time
from approval_agent.db import (
    get_connection,
    fetch_pending_approvals,
    get_c_level_users,
    get_last_email_log,
    insert_email_log,
    insert_ceo_approval,
)
from approval_agent.email_sender import send_email, send_email_to_ceo
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))  # menit
APP_URL = os.getenv("APP_URL", "http://localhost")


def check_approvals():
    conn = get_connection()
    if not conn:
        print("❌ Tidak bisa konek ke DB")
        return

    approvals = fetch_pending_approvals(conn)
    if not approvals:
        print("✅ Tidak ada approval pending")
        conn.close()
        return

    c_levels = get_c_level_users(conn)

    # ======= CEO per program request =======
    for program in approvals:
        for ceo in c_levels:
            # cek dulu apakah approval CEO sudah ada
            sql = """
            SELECT id, uuid FROM program_approvals
            WHERE program_request_id=%s AND head_user_id=%s
            """
            with conn.cursor() as cursor:
                cursor.execute(sql, (program["program_request_id"], ceo["id"]))
                existing = cursor.fetchone()

            if existing:
                ceo_approval_id = existing["id"]
                ceo_uuid = existing["uuid"]
            else:
                ceo_approval_id = insert_ceo_approval(
                    conn, program["program_request_id"], ceo["id"]
                )
                ceo_uuid = None  # uuid akan diambil dari insert jika perlu

            # cek log, apakah email CEO sudah dikirim
            last_email_ceo = get_last_email_log(conn, ceo_approval_id, "ceo")
            if last_email_ceo:
                print(
                    f"[{datetime.now()}] Skip email CEO untuk program '{program['nama_program']}'"
                )
                continue

            # kirim email
            ceo_email_data = {
                "ceo_name": ceo["name"],
                "nama_program": program["nama_program"],
                "judul_episode": program["judul_episode"],
                "inisiator": program["pembuat"],
                "approval_uuid": program["uuid"],
                "app_url": APP_URL,
            }
            send_email_to_ceo(ceo["email"], ceo_email_data)
            insert_email_log(
                conn, ceo_approval_id, program["program_request_id"], "ceo"
            )
            print(
                f"[{datetime.now()}] 📤 Approval {program['nama_program']} terkirim ke CEO"
            )

    # ======= Head per 24 jam =======
    for row in approvals:
        last_email_head = get_last_email_log(conn, row["id"], "head")
        send_email_head = False
        if not last_email_head:
            send_email_head = True
        else:
            sent_at = last_email_head["sent_at"]
            if sent_at + timedelta(hours=24) < datetime.now():
                send_email_head = True

        if send_email_head:
            head_email_data = {
                "head_name": row["head_name"],
                "nama_program": row["nama_program"],
                "judul_episode": row["judul_episode"],
                "inisiator": row["pembuat"],
                "approval_uuid": row["uuid"],
                "app_url": APP_URL,
            }
            send_email(row["email"], head_email_data)
            insert_email_log(conn, row["id"], row["program_request_id"], "head")
            print(
                f"[{datetime.now()}] 📤 Reminder {row['nama_program']} untuk Head {row['head_name']} terkirim"
            )
        else:
            print(
                f"[{datetime.now()}] Skip email ke Head {row['head_name']} untuk program '{row['nama_program']}'"
            )

    conn.close()


if __name__ == "__main__":
    while True:
        try:
            check_approvals()
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Error saat check approvals: {e}")
        time.sleep(CHECK_INTERVAL * 60)
