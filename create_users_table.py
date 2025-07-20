import sqlite3
from werkzeug.security import generate_password_hash

def create_users_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ✅ สร้างตาราง users พร้อมคอลัมน์ role
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')

    # ✅ สร้างผู้ใช้ admin
    admin_username = 'admin'
    admin_password = '1234'
    hashed_password = generate_password_hash(admin_password)

    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (admin_username, hashed_password, 'admin'))
        print("✅ เพิ่มผู้ใช้ admin เรียบร้อยแล้ว")
    except sqlite3.IntegrityError:
        print("ℹ️ ผู้ใช้ admin มีอยู่แล้ว")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_users_table()