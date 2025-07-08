from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            location TEXT,
            price REAL,
            decision_status TEXT,
            follow_up_date TEXT,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT * FROM customers WHERE follow_up_date = ?", (today,))
    due_today = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM customers WHERE decision_status='รับงาน'")
    ordered = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE decision_status='ปฏิเสธ'")
    not_ordered = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE decision_status='รอดำเนินการ'")
    pending = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'index.html',
        customers=customers,
        due_today=due_today,
        ordered=ordered,
        not_ordered=not_ordered,
        pending=pending
    )

@app.route('/add', methods=['POST'])
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    location = request.form['location']
    price = request.form['price']
    status = request.form.get('status', 'รอดำเนินการ')
    follow_up_date = request.form['follow_up_date']
    note = request.form['note']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customers (name, phone, location, price, decision_status, follow_up_date, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, location, price, status, follow_up_date, note))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_customer(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    new_status = request.form['decision_status']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET decision_status = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5005)