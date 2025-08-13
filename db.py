import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "production_requests"),
    "cursorclass": pymysql.cursors.DictCursor,
}

CEO_ROLE_ID = 6  # C-Level


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def fetch_pending_approvals(conn):
    sql = """
    SELECT pa.id, pa.uuid, pa.program_request_id, pa.status, pa.created_at,
           head.name as head_name, head.email,
           pr.nama_program, pr.judul_episode,
           creator.name as inisiator
    FROM program_approvals pa
    JOIN users head ON head.id = pa.head_user_id
    JOIN program_requests pr ON pr.id = pa.program_request_id
    JOIN users creator ON creator.id = pr.user_id
    WHERE pa.status = 'pending'
      AND TIMESTAMPDIFF(HOUR, pa.created_at, NOW()) > 24
      AND pa.approval_type = 'ide'
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def get_last_email_log(conn, approval_id, email_type="head"):
    sql = """
    SELECT sent_at FROM approval_email_logs
    WHERE approval_id = %s AND email_type = %s
    ORDER BY sent_at DESC
    LIMIT 1
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, email_type))
        return cursor.fetchone()


def insert_email_log(
    conn, approval_id=None, program_request_id=None, email_type="head"
):
    sql = """
    INSERT INTO approval_email_logs (approval_id, program_request_id, email_type)
    VALUES (%s, %s, %s)
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id, program_request_id, email_type))
    conn.commit()


def get_ceo_user(conn):
    sql = "SELECT id, name, email FROM users WHERE role_id=%s LIMIT 1"
    with conn.cursor() as cursor:
        cursor.execute(sql, (CEO_ROLE_ID,))
        return cursor.fetchone()


def check_ceo_approval_exists(conn, program_request_id):
    sql = """
    SELECT id FROM program_approvals
    WHERE program_request_id=%s AND head_user_id=%s AND approval_type='ide'
    """
    ceo = get_ceo_user(conn)
    with conn.cursor() as cursor:
        cursor.execute(sql, (program_request_id, ceo["id"]))
        return cursor.fetchone() is not None


def insert_ceo_approval(conn, program_request_id):
    ceo = get_ceo_user(conn)
    sql = """
    INSERT INTO program_approvals
    (program_request_id, head_user_id, status, approval_type)
    VALUES (%s, %s, 'pending', 'ide')
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (program_request_id, ceo["id"]))
    conn.commit()
    with conn.cursor() as cursor:
        return cursor.lastrowid
