from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
from markupsafe import Markup
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'customers.db'

# ✅ สร้างตารางหากยังไม่มี
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ✅ สร้างตาราง customers ถ้ายังไม่มี
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            location TEXT,
            note TEXT,
            details TEXT,
            price TEXT,
            status TEXT,
            follow_up_date TEXT
        )
    ''')

    # ✅ ตรวจสอบว่าคอลัมน์ details มีหรือยัง
    c.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in c.fetchall()]

    if 'details' not in columns:
        try:
            c.execute("ALTER TABLE customers ADD COLUMN details TEXT")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


init_db()


# ✅ หน้าแรก + ค้นหา + ส่งข้อมูลแบบ JSON
@app.route('/')
def index():
    search = request.args.get('search', '')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if search:
        c.execute("SELECT * FROM customers WHERE name LIKE ?", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM customers")
    customers = c.fetchall()
    conn.close()

    # ✅ แปลง customers เป็น JSON สำหรับ Chart.js
    customers_json = Markup(json.dumps([dict(row) for row in customers]))

    return render_template('index.html', customers=customers, customers_json=customers_json)

# ✅ เพิ่มลูกค้า
@app.route('/add', methods=['POST'])
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    location = request.form['location']
    note = request.form['note']
    details = request.form['proposal_details']
    price = request.form['proposal_price']
    follow_up_date = request.form.get('follow_up_date')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO customers (name, phone, location, note, details, price, status, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, location, note, details, price or None, 'รอตัดสินใจ', follow_up_date or None))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ✅ ลบลูกค้า
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ✅ อัปเดตสถานะลูกค้า
@app.route('/update_status/<int:customer_id>', methods=['POST'])
def update_status(customer_id):
    new_status = request.form['new_status']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE customers SET status = ? WHERE id = ?', (new_status, customer_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)