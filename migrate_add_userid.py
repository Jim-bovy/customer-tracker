import sqlite3

def add_user_id_column():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    try:
        # ตรวจสอบว่ามีคอลัมน์ user_id แล้วหรือยัง
        c.execute("PRAGMA table_info(customers)")
        columns = [col[1] for col in c.fetchall()]
        if 'user_id' not in columns:

            print("✅ เพิ่ม user_id ให้ตาราง customers แล้ว")
        else:
            print("⚠️ คอลัมน์ user_id มีอยู่แล้วใน customers")

        # ทำแบบเดียวกันกับตาราง customer_proposals
        c.execute("PRAGMA table_info(customer_proposals)")
        columns = [col[1] for col in c.fetchall()]
        if 'user_id' not in columns:
            c.execute("ALTER TABLE customer_proposals ADD COLUMN user_id INTEGER")
            print("✅ เพิ่ม user_id ให้ตาราง customer_proposals แล้ว")
        else:
            print("⚠️ คอลัมน์ user_id มีอยู่แล้วใน customer_proposals")

        conn.commit()
    except Exception as e:
        print("❌ เกิดข้อผิดพลาด:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_user_id_column()