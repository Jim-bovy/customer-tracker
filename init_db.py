import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ตาราง users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')

    # สร้างผู้ใช้แอดมิน
    admin_username = 'admin'
    admin_password = '1234'
    hashed_password = generate_password_hash(admin_password)

    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (admin_username, hashed_password, 'admin'))
        print("✅ เพิ่มแอดมินสำเร็จแล้ว")
    except sqlite3.IntegrityError:
        print("⚠️ แอดมินมีอยู่แล้ว")

    # ตาราง customer_proposals (หรือ customers ตามชื่อที่ใช้จริง)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            location TEXT,
            price REAL,
            product_type TEXT,
            decision_status TEXT,
            follow_up_date TEXT,
            contact_date TEXT,
            proposal_date TEXT,
            reason TEXT,
            note TEXT,
            attachment TEXT,
            sale_name TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ สร้างฐานข้อมูลเสร็จสิ้นแล้ว")

if __name__ == '__main__':
    init_db()