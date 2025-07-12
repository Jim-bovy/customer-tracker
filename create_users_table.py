import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# สร้างตาราง users ถ้ายังไม่มี
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("✅ สร้างตาราง users เรียบร้อยแล้ว")