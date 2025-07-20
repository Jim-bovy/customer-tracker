# ไฟล์: create_proposals_table.py

import sqlite3

def create_table_customer_proposals():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            proposal_date TEXT,
            price REAL,
            follow_up_date TEXT,
            decision_status TEXT,
            reason TEXT,
            note TEXT,
            
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ สร้างตาราง customer_proposals เรียบร้อยแล้ว")