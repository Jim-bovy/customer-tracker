import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# เพิ่มคอลัมน์ agency_type
try:
    c.execute("ALTER TABLE customers ADD COLUMN agency_type TEXT")
    print("✅ เพิ่มคอลัมน์ agency_type เรียบร้อยแล้ว")
except sqlite3.OperationalError as e:
    print("⚠️ เพิ่มคอลัมน์ไม่สำเร็จ:", e)

conn.commit()
conn.close()