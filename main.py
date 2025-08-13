# main.py
from db import (
    get_connection,
    fetch_pending_approvals,
    get_c_level_users,
    get_last_email_log,
    insert_email_log,
    insert_ceo_approval,
)
from datetime import datetime


def check_approvals():
    conn = get_connection()
    approvals = fetch_pending_approvals(conn)
    c_levels = get_c_level_users(conn)

    for approval in approvals:
        # 1️⃣ C-Level: kirim sekali per approval
        for ceo in c_levels:
            last_email = get_last_email_log(conn, approval["id"], ceo["id"])
            if not last_email:
                # kirim email ke ceo["email"]
                print(
                    f"Sending email to CEO {ceo['name']} for program request {approval['program_request_id']}"
                )
                insert_email_log(conn, approval["id"], ceo["id"])

        # 2️⃣ Head biasa: kirim 1x per 24 jam
        head_id = approval["head_user_id"]
        last_email = get_last_email_log(conn, approval["id"], head_id)
        if (
            not last_email
            or (datetime.now() - last_email["sent_at"]).total_seconds() > 86400
        ):
            # kirim email ke head
            print(
                f"Sending email to Head {approval['head_name']} for program request {approval['program_request_id']}"
            )
            insert_email_log(conn, approval["id"], head_id)


if __name__ == "__main__":
    check_approvals()
