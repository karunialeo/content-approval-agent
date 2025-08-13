from db import get_connection

conn = get_connection()
if conn:
    print("✅ Koneksi ke database berhasil!")
    conn.close()
else:
    print("❌ Gagal konek ke database")
