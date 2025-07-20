import sqlite3

def add_column(table, column, datatype):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
        print(f"✅ เพิ่มคอลัมน์ {column} ใน {table} แล้ว")
    except sqlite3.OperationalError as e:
        print(f"⚠️ {column} อาจมีอยู่แล้ว: {e}")
    conn.commit()
    conn.close()

def create_table_customer_payments():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS customer_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                payment_date TEXT,
                payment_type TEXT,
                payment_amount TEXT,
                note TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')
        print("✅ สร้างตาราง customer_payments แล้ว")
    except sqlite3.OperationalError as e:
        print(f"⚠️ เกิดข้อผิดพลาด: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_column('customers', 'agency_type', 'TEXT')
    add_column('customers', 'work_type', 'TEXT')
    add_column('customers', 'attachment', 'TEXT')
    add_column('customers', 'contact_date', 'TEXT')
    add_column('customers', 'sale_name', 'TEXT')

    try:
        create_table_customer_payments()
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดตอนสร้างตาราง: {e}")