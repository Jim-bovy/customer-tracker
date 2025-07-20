import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# เพิ่มคอลัมน์ sale_name
c.execute("ALTER TABLE customers ADD COLUMN sale_name TEXT")

conn.commit()
conn.close()

print("✅ เพิ่มคอลัมน์ sale_name สำเร็จแล้ว")