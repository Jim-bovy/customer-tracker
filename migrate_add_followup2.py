import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE customers ADD COLUMN follow_up_date_2 TEXT")
    print("✅ เพิ่มคอลัมน์ follow_up_date_2 เรียบร้อยแล้ว")
except sqlite3.OperationalError as e:
    print("⚠️ เพิ่มไม่สำเร็จ:", e)

conn.commit()
conn.close()