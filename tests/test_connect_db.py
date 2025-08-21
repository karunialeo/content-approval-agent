# Kita perlu sedikit trik agar Python bisa menemukan folder approval_agent
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from approval_agent.db import get_connection

conn = get_connection()
if conn:
    print("✅ Koneksi ke database berhasil!")
    conn.close()
else:
    print("❌ Gagal konek ke database")
