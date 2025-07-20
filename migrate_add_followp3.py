import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE customers ADD COLUMN follow_up_date_3 TEXT")
    print("✅ เพิ่มคอลัมน์ follow_up_date_3 สำเร็จแล้ว")
except sqlite3.OperationalError as e:
    print("⚠️ เพิ่มคอลัมน์ไม่สำเร็จ:", e)

conn.commit()
conn.close()