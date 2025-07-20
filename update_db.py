import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# ตรวจสอบคอลัมน์ในตาราง customers
c.execute("PRAGMA table_info(customers)")
columns = [col[1] for col in c.fetchall()]

def add_column_if_missing(column_name, column_type):
    if column_name not in columns:
        try:
            c.execute(f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}")
            print(f"✅ เพิ่มคอลัมน์ {column_name} เรียบร้อยแล้ว")
        except sqlite3.OperationalError as e:
            print(f"⚠️ เพิ่มไม่ได้: {column_name} ->", e)
    else:
        print(f"ℹ️ คอลัมน์ {column_name} มีอยู่แล้ว")

# รายการคอลัมน์ที่ต้องเช็กและเพิ่ม
add_column_if_missing('sale_name', 'TEXT')
add_column_if_missing('contact_date', 'TEXT')
add_column_if_missing('agency_type', 'TEXT')
add_column_if_missing('location', 'TEXT')
add_column_if_missing('work_type', 'TEXT')
add_column_if_missing('note', 'TEXT')
add_column_if_missing('product_type', 'TEXT')

conn.commit()
conn.close()