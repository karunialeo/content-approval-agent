# Approval Reminder Agent

Agent Python untuk ngecek approval yang pending > 24 jam dan kirim email reminder ke head user.

## Setup

1. Pastikan Python 3 sudah terinstall.

2. Install dependencies:

```bash
pip install pymysql python-dotenv Jinja2
```

3. Jalankan script setup environment:

```bash
./setup_env.sh
```

Isi sesuai instruksi.

4. Pastikan file berikut ada dalam folder yang sama:

- `main.py`
- `db.py`
- `email_sender.py`
- `template.html`
- `.env`

Struktur folder :

```bash
approval_agent/
├── main.py           # entry point, loop + graceful shutdown
├── db.py             # koneksi DB + query functions
├── email_sender.py   # fungsi kirim email
├── template.html     # template email
├── .env
```

## Menjalankan Agent

Jalankan:

```bash
python main.py
```

Agent akan ngecek setiap interval (default 10 menit) dan mengirim email reminder.

## Menghentikan Agent

Tekan `Ctrl + C` untuk graceful shutdown.

---

Kalau mau customize interval, edit file `.env` di bagian `CHECK_INTERVAL`.

---

Kalau ada masalah, cek konfigurasi database dan SMTP.

---

Contact: Leo (karunialeo@gmail.com)
