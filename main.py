import time
from db import get_connection, fetch_pending_approvals, get_c_level_users
from db import get_last_email_log, insert_email_log, insert_ceo_approval
from email_sender import send_email, send_email_to_ceo
from dotenv import load_dotenv
import os

load_dotenv()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))  # menit


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

    for row in approvals:
        # ======= C-Level =======
        for ceo in c_levels:
            last_email = get_last_email_log(conn, row["id"], "ceo")
            if not last_email:
                ceo_approval_id = insert_ceo_approval(
                    conn, row["program_request_id"], ceo["id"]
                )
                insert_email_log(
                    conn, ceo_approval_id, row["program_request_id"], "ceo"
                )
                send_email_to_ceo(ceo["email"], row)
                print(f"📤 CEO {ceo['name']} dikirimin approval {row['nama_program']}")

        # ======= Head =======
        last_email_head = get_last_email_log(conn, row["id"], "head")
        if not last_email_head:
            insert_email_log(conn, row["id"], row["program_request_id"], "head")
            send_email(row["email"], row)
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
