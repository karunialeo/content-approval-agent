# db.py
import os
import pymysql
import uuid
from datetime import datetime
from dotenv import load_dotenv


# ========================
# DB Connection
# ========================
def get_connection():
    load_dotenv()  # baca file .env

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("DB_NAME", "approval_system_db"),
        "cursorclass": pymysql.cursors.DictCursor,
    }

    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        print("❌ Gagal koneksi ke DB:", e)
        return None


# ========================
# Users / C-Level
# ========================
def get_c_level_users(conn):
    sql = "SELECT id, name, email FROM users WHERE role_id = 6 AND deleted_at IS NULL"
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


# ========================
# Pending Approvals
# ========================
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
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


# ========================
# Email Logs
# ========================
def get_last_email_log(conn, approval_id, head_user_id):
    sql = """
    SELECT sent_at FROM approval_email_logs
    WHERE approval_id = %s AND head_user_id = %s
    ORDER BY sent_at DESC
    LIMIT 1
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, head_user_id))
        return cursor.fetchone()


def insert_email_log(conn, approval_id, head_user_id):
    sql = "INSERT INTO approval_email_logs (approval_id, head_user_id) VALUES (%s, %s)"
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, head_user_id))
    conn.commit()


# ========================
# Insert CEO Approval
# ========================
def insert_ceo_approval(conn, program_request_id, ceo_id):
    new_uuid = str(uuid.uuid4())  # generate UUID baru
    sql = """
    INSERT INTO program_approvals (program_request_id, head_user_id, uuid, status, created_at)
    VALUES (%s, %s, %s, 'pending', NOW())
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (program_request_id, ceo_id, new_uuid))
    conn.commit()
    return cursor.lastrowid
