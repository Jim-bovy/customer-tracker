# update_db.py
import sqlite3

def add_product_type_column():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    try:
        # พยายามเพิ่มคอลัมน์ใหม่
        c.execute("ALTER TABLE customers ADD COLUMN product_type TEXT")
        conn.commit()
        print("✅ เพิ่มคอลัมน์ product_type สำเร็จแล้ว")
    except sqlite3.OperationalError as e:
        # ถ้ามี error ว่าคอลัมน์มีอยู่แล้ว
        if "duplicate column name" in str(e).lower():
            print("⚠️ คอลัมน์ 'product_type' มีอยู่แล้วในตาราง customers")
        else:
            print("❌ เกิดข้อผิดพลาด:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_product_type_column()
