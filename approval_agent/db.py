import os
import pymysql
import uuid
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("DB_NAME", "approval_system_db"),
        "cursorclass": pymysql.cursors.DictCursor,
    }
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print("❌ Gagal koneksi ke DB:", e)
        return None


def get_c_level_users(conn):
    sql = "SELECT id, name, email FROM users WHERE role_id = 6 AND deleted_at IS NULL"
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def fetch_pending_approvals(conn):
    sql = """
    SELECT pa.id, pa.uuid, pa.program_request_id, pa.status, pa.created_at,
           pa.head_user_id,
           head.name as head_name, head.email,
           pr.nama_program, pr.judul_episode,
           creator.name as pembuat
    FROM program_approvals pa
    JOIN users head ON head.id = pa.head_user_id
    JOIN program_requests pr ON pr.id = pa.program_request_id
    JOIN users creator ON creator.id = pr.user_id
    WHERE pa.status = 'pending'
      AND TIMESTAMPDIFF(HOUR, pa.created_at, NOW()) > 24
      AND pa.deleted_at IS NULL
      AND pr.deleted_at IS NULL
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def get_last_email_log(conn, approval_id, email_type):
    sql = """
    SELECT sent_at FROM approval_email_logs
    WHERE approval_id = %s AND email_type = %s
    ORDER BY sent_at DESC
    LIMIT 1
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, email_type))
        return cursor.fetchone()


def insert_email_log(conn, approval_id, program_request_id, email_type):
    sql = """
    INSERT INTO approval_email_logs (approval_id, program_request_id, email_type)
    VALUES (%s, %s, %s)
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, program_request_id, email_type))
    conn.commit()


def insert_ceo_approval(conn, program_request_id, ceo_id):
    # Cek dulu apakah program request masih ada (deleted_at IS NULL)
    sql_check = "SELECT id FROM program_requests WHERE id = %s AND deleted_at IS NULL"
    with conn.cursor() as cursor:
        cursor.execute(sql_check, (program_request_id,))
        result = cursor.fetchone()
        if not result:
            print(
                f"⚠️ Program request {program_request_id} sudah dihapus. CEO approval dibatalkan."
            )
            return None

    # Insert approval CEO
    new_uuid = str(uuid.uuid4())
    sql_insert = """
    INSERT INTO program_approvals (program_request_id, head_user_id, uuid, status, created_at)
    VALUES (%s, %s, %s, 'pending', NOW())
    """
    with conn.cursor() as cursor:
        cursor.execute(sql_insert, (program_request_id, ceo_id, new_uuid))
        conn.commit()
        return cursor.lastrowid
