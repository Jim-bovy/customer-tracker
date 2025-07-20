import sqlite3

def migrate_customer_contracts():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_date TEXT,
            contract_type TEXT,
            start_date TEXT,
            end_date TEXT,
            customer_id INTEGER,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ สร้างตาราง customer_contracts สำเร็จแล้ว")

# เรียกฟังก์ชันนี้เมื่อรันไฟล์
if __name__ == '__main__':
    migrate_customer_contracts()