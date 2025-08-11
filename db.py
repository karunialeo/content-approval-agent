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


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def fetch_pending_approvals(conn):
    sql = """
    SELECT pa.id, pa.uuid, pa.program_request_id, pa.status, pa.created_at,
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


def get_last_email_log(conn, approval_id):
    sql = """
    SELECT sent_at FROM approval_email_logs
    WHERE approval_id = %s
    ORDER BY sent_at DESC
    LIMIT 1
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id,))
        return cursor.fetchone()


def insert_email_log(conn, approval_id):
    sql = "INSERT INTO approval_email_logs (approval_id) VALUES (%s)"
    with conn.cursor() as cursor:
        cursor.execute(sql, (approval_id,))
    conn.commit()
