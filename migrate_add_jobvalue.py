import sqlite3

def migrate_add_job_value():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE customer_proposals ADD COLUMN job_value TEXT")
        print("✅ เพิ่มคอลัมน์ job_value สำเร็จ")
    except sqlite3.OperationalError as e:
        print(f"⚠️ เกิดข้อผิดพลาด: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate_add_job_value()