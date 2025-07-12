import sqlite3
from werkzeug.security import generate_password_hash

# เชื่อมต่อกับฐานข้อมูล
conn = sqlite3.connect('database.db')
c = conn.cursor()

# ✅ สร้างตาราง users ถ้ายังไม่มี
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# ✅ ตั้งค่า username และ password ที่ต้องการ
username = 'admin'
password = '1234'

# ✅ เข้ารหัส password ก่อนเก็บลงฐานข้อมูล
hashed_password = generate_password_hash(password)

try:
    # ✅ เพิ่มผู้ใช้เข้าไปในตาราง
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    print(f"✅ เพิ่มผู้ใช้ '{username}' เรียบร้อยแล้ว")
except sqlite3.IntegrityError:
    print(f"⚠️ ผู้ใช้ '{username}' มีอยู่แล้วในระบบ")

conn.close()