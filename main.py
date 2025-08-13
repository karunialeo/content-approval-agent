import time
from db import (
    get_connection,
    fetch_pending_approvals,
    get_c_level_users,
    get_last_email_log,
    insert_email_log,
    insert_ceo_approval,
)
from email_sender import send_email, send_email_to_ceo
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
        last_email_ceo = get_last_email_log(conn, program["program_request_id"], "ceo")
        if last_email_ceo:
            print(f"⏸ CEO sudah dikirimin email untuk {program['nama_program']}, skip")
            continue

        for ceo in c_levels:
            # Cek apakah approval CEO sudah ada
            ceo_approval_id = insert_ceo_approval(
                conn, program["program_request_id"], ceo["id"]
            )

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

        print(f"📤 CEO dikirimin approval {program['nama_program']}")

    # ======= Head per 24 jam =======
    for row in approvals:
        last_email_head = get_last_email_log(conn, row["id"], "head")
        send_head = False

        if not last_email_head:
            send_head = True
            print(
                f"🆕 Head {row['head_name']} belum pernah dikirimin email, akan dikirim"
            )
        else:
            sent_at = last_email_head["sent_at"]
            if isinstance(sent_at, str):
                sent_at = datetime.strptime(sent_at, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - sent_at > timedelta(hours=24):
                send_head = True
                print(
                    f"⏰ Sudah >24 jam sejak email terakhir ke Head {row['head_name']}, akan dikirim"
                )
            else:
                print(
                    f"⏸ Head {row['head_name']} sudah dikirimin email kurang dari 24 jam, skip"
                )

        if send_head:
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
                f"📤 Head {row['head_name']} dikirimin reminder {row['nama_program']}"
            )

    conn.close()


if __name__ == "__main__":
    while True:
        try:
            check_approvals()
        except Exception as e:
            print("❌ Error saat check approvals:", e)
        time.sleep(CHECK_INTERVAL * 60)
