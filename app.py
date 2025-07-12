from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # เปลี่ยนเป็นค่าเฉพาะของคุณ

# -------------------------- Database Setup --------------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        location TEXT,
        price REAL,
        product_type TEXT,
        decision_status TEXT,
        follow_up_date TEXT,
        note TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

def create_admin_user():
    username = 'admin'
    password = '1234'
    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print("✅ เพิ่มผู้ใช้ admin แล้ว (รหัสผ่าน: 1234)")
    else:
        print("⚠️ มีผู้ใช้ admin อยู่แล้ว")
    conn.close()

# -------------------------- Migrate (Run Once) --------------------------
def migrate_once():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE customers ADD COLUMN product_type TEXT")
        print("✅ เพิ่ม product_type แล้ว")
    except Exception as e:
        print("⚠️", e)
    conn.commit()
    conn.close()

# -------------------------- Routes --------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user_id = session['user_id']

    c.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    customers = c.fetchall()

    c.execute("SELECT COUNT(*) FROM customers WHERE decision_status = 'รับงาน' AND user_id = ?", (user_id,))
    ordered = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM customers WHERE decision_status = 'ปฏิเสธ' AND user_id = ?", (user_id,))
    not_ordered = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM customers WHERE decision_status = 'ยังไม่ตัดสินใจ' AND user_id = ?", (user_id,))
    undecided_count = c.fetchone()[0]

    today = date.today().isoformat()
    c.execute("SELECT * FROM customers WHERE follow_up_date = ? AND user_id = ?", (today, user_id))
    due_today = c.fetchall()

    conn.close()

    return render_template('index.html',
                           customers=customers,
                           ordered=ordered,
                           not_ordered=not_ordered,
                           undecided_count=undecided_count,
                           due_today=due_today)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password_input):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))  # ✅ กลับไปหน้า dashboard ที่ใช้ index.html

        else:
            error = 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        location = request.form['location']
        price = request.form['price']
        product_type = request.form['product_type']
        decision_status = request.form['decision_status']
        follow_up_date = request.form['follow_up_date']
        note = request.form['note']
        user_id = session['user_id']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO customers 
            (name, phone, location, price, product_type, decision_status, follow_up_date, note, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, location, price, product_type, decision_status, follow_up_date, note, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add_customer.html')

@app.route('/edit_status/<int:customer_id>', methods=['GET', 'POST'])
def edit_status(customer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        new_status = request.form['decision_status']
        c.execute("UPDATE customers SET decision_status=? WHERE id=? AND user_id=?", (new_status, customer_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    c.execute("SELECT * FROM customers WHERE id=? AND user_id=?", (customer_id, session['user_id']))
    customer = c.fetchone()
    conn.close()

    if not customer:
        return "ไม่พบลูกค้ารายนี้"

    return render_template('edit_status.html', customer=customer)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()

        if user and check_password_hash(user[0], current_pw):
            new_hashed = generate_password_hash(new_pw)
            c.execute("UPDATE users SET password = ? WHERE id = ?", (new_hashed, session['user_id']))
            conn.commit()
            conn.close()
            return "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว"
        else:
            conn.close()
            return "รหัสผ่านเดิมไม่ถูกต้อง"

    return '''
        <form method="POST">
            <input type="password" name="current_password" placeholder="รหัสผ่านเดิม" required><br>
            <input type="password" name="new_password" placeholder="รหัสผ่านใหม่" required><br>
            <button type="submit">เปลี่ยนรหัสผ่าน</button>
        </form>
    '''

# -------------------------- Main --------------------------
if __name__ == '__main__':
    init_db()
    migrate_once()
    create_admin_user()
    app.run(debug=True)
