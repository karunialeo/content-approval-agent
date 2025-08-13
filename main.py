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

    for program in approvals:
        # ===== CEO =====
        for ceo in c_levels:
            # cek dulu apakah approval CEO sudah ada
            ceo_approval = program.get(f"ceo_approval_id_{ceo['id']}")
            if not ceo_approval:
                # buat approval record untuk CEO
                ceo_approval_id = insert_ceo_approval(
                    conn, program["program_request_id"], ceo["id"]
                )
            else:
                ceo_approval_id = ceo_approval

            # cek log apakah email CEO udah pernah dikirim
            last_email_ceo = get_last_email_log(conn, ceo_approval_id, "ceo")
            if not last_email_ceo:
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
                    f"📤 CEO {ceo['name']} dikirimin approval {program['nama_program']}"
                )

        # ===== Head =====
        last_email_head = get_last_email_log(conn, program["id"], "head")
        if not last_email_head:
            head_email_data = {
                "head_name": program["head_name"],
                "nama_program": program["nama_program"],
                "judul_episode": program["judul_episode"],
                "inisiator": program["pembuat"],
                "approval_uuid": program["uuid"],
                "app_url": APP_URL,
            }
            send_email(program["email"], head_email_data)
            insert_email_log(conn, program["id"], program["program_request_id"], "head")
            print(
                f"📤 Head {program['head_name']} dikirimin reminder {program['nama_program']}"
            )

    conn.close()


if __name__ == "__main__":
    while True:
        try:
            check_approvals()
        except Exception as e:
            print("❌ Error saat check approvals:", e)
        time.sleep(CHECK_INTERVAL * 60)
