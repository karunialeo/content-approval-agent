from db import get_connection

try:
    conn = get_connection()
    print("✅ Koneksi ke database berhasil!")
    conn.close()
except Exception as e:
    print("❌ Gagal konek ke database:")
    print(e)
