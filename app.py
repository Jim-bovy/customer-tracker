# ส่วน import ด้านบนสุดของ app.py
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from requests import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from xhtml2pdf import pisa
from io import BytesIO
from werkzeug.utils import secure_filename  # 📌 วางไว้บนสุดของไฟล์ app.py
from create_proposals_table import create_table_customer_proposals
# 🔽 เพิ่มส่วนนี้เข้ามาใต้ import
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 🔽 ลงทะเบียนฟอนต์ THSarabun
pdfmetrics.registerFont(TTFont('THSarabun', 'static/fonts/THSarabunNew.ttf'))

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# -------------------------- Database Setup --------------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ตารางผู้ใช้งาน
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # ตารางลูกค้า
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            sale_name TEXT,
            location TEXT,
            price REAL,
            product_type TEXT,
            decision_status TEXT,
            follow_up_date TEXT,
            follow_up_date_2 TEXT,
            follow_up_date_3 TEXT,
            note TEXT,
            user_id INTEGER,
            attachment TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # ตารางการเสนอราคา
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            proposal_date TEXT,
            job_value REAL,
            decision_status TEXT,
            reason TEXT,
            note TEXT,
            follow_up_date TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')

    # ตารางสัญญา
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            got_job BOOLEAN,
            contract_date TEXT,
            payment_schedule TEXT,
            work_start TEXT,
            work_end TEXT,
            note TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')

    # ตารางการชำระเงิน
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            payment_date TEXT,
            payment_phase TEXT,
            amount REAL,
            note TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')

    conn.commit()
    conn.close()

def create_admin_user():
    username = 'admin'
    password = '1234'
    hashed = generate_password_hash(password)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        print("✅ เพิ่มผู้ใช้ admin แล้ว (รหัสผ่าน: 1234)")
    conn.commit()
    conn.close()


@app.route('/')
def home():
    return redirect(url_for('login'))


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
            return render_template('register.html', error="ชื่อผู้ใช้นี้มีแล้ว")
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
        c.execute("SELECT id, password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password_input):
            session['user_id'] = user[0]
            session['role'] = user[2]
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="ชื่อผู้ใช้หรือรหัสผ่านผิด")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role')
    today = date.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ✅ ดึงลูกค้าทั้งหมด
    if role == 'admin':
        c.execute("SELECT * FROM customers")
    else:
        c.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    customers = c.fetchall()

    # ✅ ดึงผู้ใช้ทั้งหมด
    c.execute("SELECT id, username FROM users")
    users = c.fetchall()
    usernames = {u['id']: u['username'] for u in users}

    # ✅ ลูกค้าที่ต้องติดตามวันนี้
    if role == 'admin':
        c.execute("SELECT * FROM customers WHERE follow_up_date = ?", (today,))
    else:
        c.execute("SELECT * FROM customers WHERE user_id = ? AND follow_up_date = ?", (user_id, today))
    due_today = c.fetchall()

    # ✅ สรุปจำนวนลูกค้าที่ได้รับงาน
    if role == 'admin':
        c.execute("SELECT COUNT(*) FROM customers WHERE decision_status = 'ได้รับงาน'")
    else:
        c.execute("SELECT COUNT(*) FROM customers WHERE user_id = ? AND decision_status = 'ได้รับงาน'", (user_id,))
    ordered = c.fetchone()[0]

    # ✅ สรุปจำนวนลูกค้าที่ไม่ได้รับงาน
    if role == 'admin':
        c.execute("SELECT COUNT(*) FROM customers WHERE decision_status = 'ไม่ได้รับงาน'")
    else:
        c.execute("SELECT COUNT(*) FROM customers WHERE user_id = ? AND decision_status = 'ไม่ได้รับงาน'", (user_id,))
    not_ordered = c.fetchone()[0]

    # (optional) debug ค่าที่มี
    print("⚠️ ค่า decision_status ทั้งหมด:", [row[0] for row in customers])

    conn.close()

    return render_template('dashboard.html',
                           customers=customers,
                           due_today=due_today,
                           usernames=usernames,
                           username=session['username'],
                           ordered=ordered,
                           not_ordered=not_ordered)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        sale_name = request.form.get('sale_name', '')
        contact_date = request.form.get('contact_date', '')
        follow_up_date = request.form.get('follow_up_date', '')
        agency_type = request.form.get('agency_type', '')
        location = request.form.get('location', '')
        work_type = request.form.get('work_type', '')
        note = request.form.get('note', '')
        product_types = request.form.getlist('product_type[]')
        product_type = ', '.join(product_types)

        user_id = session['user_id']  # ⭐ ผูก user_id

        file = request.files.get('attachment')
        filename = ''
        if file and file.filename:
            filename = secure_filename(file.filename)  # ✅ ปลอดภัย
            file.save(os.path.join('static/uploads', filename))  # ✅ บันทึกไฟล์ลงโฟลเดอร์

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO customers (
                name, phone, sale_name, contact_date, follow_up_date,
                agency_type, location, work_type, note,
                product_type, attachment, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, sale_name, contact_date, follow_up_date,
              agency_type, location, work_type, note,
              product_type, filename, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('add_customer.html')
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('THSarabun', 'static/fonts/THSarabunNew.ttf'))

c = canvas.Canvas("test.pdf")
c.setFont("THSarabun", 16)
c.drawString(100, 750, "ทดสอบภาษาไทยจากฟอนต์")
c.save()


@app.route('/export_customer/<int:customer_id>')
def export_customer(customer_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
    customer = c.fetchone()

    c.execute("SELECT * FROM customer_proposals WHERE customer_id=?", (customer_id,))
    proposals = c.fetchall()
    proposal = proposals[0] if proposals else None  # ✅ ป้องกัน IndexError

    c.execute("SELECT * FROM customer_contracts WHERE customer_id=?", (customer_id,))
    contracts = c.fetchall()
    contract = contracts[0] if contracts else None  # ✅ ป้องกัน IndexError

    c.execute("SELECT * FROM customer_payments WHERE customer_id=?", (customer_id,))
    payments = c.fetchall()

    conn.close()

    body_html = render_template('export_customer.html',
                                customer=customer,
                                proposal=proposal,
                                contract=contract,
                                payments=payments)

    full_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'THSarabun';
                src: url('static/fonts/THSarabunNew.ttf') format("truetype");
            }}
            body {{
                font-family: 'THSarabun';
                font-size: 16pt;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #000;
                padding: 8px;
            }}
        </style>
    </head>
    <body>
    {body_html}
    </body>
    </html>
    """

    result = BytesIO()
    pisa.CreatePDF(full_html, dest=result)
    result.seek(0)
    filename = f"customer_{customer_id}.pdf"
    return send_file(result, mimetype='application/pdf',
                     download_name=filename, as_attachment=True)

@app.route('/visit1/<int:customer_id>', methods=['GET', 'POST'])
def visit1(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        sale_name = request.form.get('sale_name')
        contact_date = request.form.get('contact_date')
        follow_up_date = request.form.get('follow_up_date')
        name = request.form.get('name')
        phone = request.form.get('phone')
        agency_type = request.form.get('agency_type')
        location = request.form.get('location')
        work_type = request.form.get('work_type')
        note = request.form.get('note')
        product_types = request.form.getlist('product_type[]')
        attached_files = request.form.getlist('attached_files[]')
        product_type = ', '.join(product_types)
        attached_file = ', '.join(attached_files)

        c.execute('''
            UPDATE customers
            SET sale_name=?, contact_date=?, follow_up_date=?,
                agency_type=?, location=?, work_type=?,
                product_type=?, attached_files=?
            WHERE id=?
        ''', (
            sale_name, contact_date, follow_up_date,
            agency_type, location, work_type,
            product_type, attached_file, customer_id
        ))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.row_factory = sqlite3.Row
    c.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
    customer = c.fetchone()
    conn.close()
    return render_template('visit1.html', customer=customer)

@app.route('/visit2/<int:customer_id>', methods=['GET', 'POST'])
def visit2(customer_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        proposal_date = request.form['proposal_date']
        job_value = request.form['job_value']
        follow_up_date = request.form['follow_up_date_2']
        decision_status = request.form['decision_status']
        reason = request.form['reason']
        note = request.form['note']

        # ✅ รับไฟล์แนบ
        file = request.files.get('attachment')
        filename = ''
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join('static/uploads', filename))

        # ✅ เพิ่มข้อมูลลง customer_proposals พร้อมแนบไฟล์
        c.execute('''
            INSERT INTO customer_proposals (
                customer_id, proposal_date, job_value,
                decision_status, reason, note, follow_up_date, attachment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, proposal_date, job_value,
              decision_status, reason, note, follow_up_date, filename))

        # ✅ อัปเดตสถานะในตาราง customers ด้วย
        c.execute('''
            UPDATE customers
            SET decision_status = ?, follow_up_date_2 = ?
            WHERE id = ?
        ''', (decision_status, follow_up_date, customer_id))

        conn.commit()
        conn.close()
        return redirect(url_for('visit3', customer_id=customer_id))

    # GET: แสดงฟอร์ม
    c.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = c.fetchone()
    conn.close()
    return render_template('visit2.html', customer=customer)

@app.route('/visit3/<int:customer_id>', methods=['GET', 'POST'])
def visit3(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        got_job = request.form.get('got_job') == 'on'
        contract_date = request.form.get('contract_date')
        payment_schedule = request.form.get('payment_schedule')
        work_start = request.form.get('work_start')
        work_end = request.form.get('work_end')
        note = request.form.get('note')

        # บันทึกข้อมูลทำสัญญา
        c.execute('''
            INSERT INTO customer_contracts (
                customer_id, got_job, contract_date,
                payment_schedule, work_start, work_end, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, got_job, contract_date, payment_schedule, work_start, work_end, note))

        # ✅ อัปเดต follow_up_date_3 จาก work_start
        if work_start:
            c.execute("UPDATE customers SET follow_up_date_3=? WHERE id=?", (work_start, customer_id))

        # ✅ ถ้าได้งาน → อัปเดต status
        if got_job:
            c.execute("UPDATE customers SET decision_status=? WHERE id=?", ('ได้รับงาน', customer_id))

        # รับเงิน
        payment_date = request.form.get('payment_date')
        payment_phase = request.form.get('payment_phase')
        amount = request.form.get('amount')
        payment_note = request.form.get('payment_note')

        if payment_date and amount:
            c.execute('''
                INSERT INTO customer_payments (
                    customer_id, payment_date, payment_phase, amount, note
                ) VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, payment_date, payment_phase, amount, payment_note))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
    customer = c.fetchone()
    c.execute("SELECT * FROM customer_payments WHERE customer_id = ?", (customer_id,))
    payments = c.fetchall()
    conn.close()
    print("✅ เปิดหน้า visit3 แล้ว")
    return render_template('visit3.html', customer=customer, payments=payments)
@app.route('/view_customer/<int:customer_id>')
def view_customer(customer_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
    customer = c.fetchone()

    c.execute("SELECT * FROM customer_proposals WHERE customer_id=?", (customer_id,))
    proposals = c.fetchall()

    c.execute("SELECT * FROM customer_contracts WHERE customer_id=?", (customer_id,))
    contracts = c.fetchall()
    contract = contracts[0] if contracts else None
    c.execute("SELECT * FROM customer_payments WHERE customer_id=?", (customer_id,))
    payments = c.fetchall()

    conn.close()

    # ✅ แก้ตรงนี้ให้ส่ง proposal เป็น `proposal=proposals[0]` ถ้ามี
    return render_template('view_customer.html',
                           customer=customer,
                           proposal=proposals[0] if proposals else None,
                           contract=contract,
                           payments=payments)


@app.route('/edit_payment/<int:payment_id>', methods=['GET', 'POST'])
def edit_payment(payment_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if request.method == 'POST':
        payment_date = request.form['payment_date']
        payment_phase = request.form['payment_phase']
        amount = request.form['amount']
        note = request.form['note']
        c.execute('''
            UPDATE customer_payments
            SET payment_date=?, payment_phase=?, amount=?, note=?
            WHERE id=?
        ''', (payment_date, payment_phase, amount, note, payment_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    c.execute("SELECT * FROM customer_payments WHERE id=?", (payment_id,))
    payment = c.fetchone()
    conn.close()
    return render_template('edit_payment.html', payment=payment)

@app.route('/delete/<int:customer_id>')
def delete_customer(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    c.execute("DELETE FROM customer_proposals WHERE customer_id=?", (customer_id,))
    c.execute("DELETE FROM customer_contracts WHERE customer_id=?", (customer_id,))
    c.execute("DELETE FROM customer_payments WHERE customer_id=?", (customer_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/accepted_customers')
def accepted_customers():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role')  # 👈 เพิ่มการดึงบทบาท

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("🧪 user_id:", user_id)
    print("🧪 role:", role)

    if role == 'admin':
        c.execute("SELECT * FROM customers WHERE decision_status='ได้รับงาน'")
    else:
        c.execute("SELECT * FROM customers WHERE user_id=? AND decision_status='ได้รับงาน'", (user_id,))

    customers = c.fetchall()
    print("🧪 ลูกค้าที่ได้รับงาน:", [dict(row) for row in customers])

    conn.close()
    return render_template('accepted_customers.html', customers=customers)

@app.route('/rejected_customers')
def rejected_customers():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("🧪 user_id:", user_id)
    print("🧪 role:", role)

    if role == 'admin':
        c.execute("SELECT * FROM customers WHERE decision_status='ไม่ได้รับงาน'")
    else:
        c.execute("SELECT * FROM customers WHERE user_id=? AND decision_status='ไม่ได้รับงาน'", (user_id,))

    customers = c.fetchall()
    print("🧪 ลูกค้าที่ไม่ได้รับงาน:", [dict(row) for row in customers])

    conn.close()
    return render_template('rejected_customers.html', customers=customers)
# -------------------------- Migrations --------------------------
def migrate_customer_proposals():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            proposal_date TEXT,
            job_value REAL,
            decision_status TEXT,
            reason TEXT,
            note TEXT,
            follow_up_date TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    conn.commit()
    conn.close()

def migrate_customer_contracts():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            got_job BOOLEAN,
            contract_date TEXT,
            payment_schedule TEXT,
            work_start TEXT,
            work_end TEXT,
            note TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    conn.commit()
    conn.close()

def migrate_customer_payments():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            payment_date TEXT,
            payment_phase TEXT,
            amount REAL,
            note TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    conn.commit()
    conn.close()

# -------------------------- Run Server --------------------------
if __name__ == '__main__':
    import os

    # 🟡 comment พวก migrate ออกถ้าจะ deploy ขึ้น Render
    # migrate_customer_proposals()
    # migrate_customer_contracts()
    # create_admin_user()
    # migrate_customer_payments()
    # create_table_customer_proposals()
    # updated for render host fix (again)

    port = int(os.environ.get("PORT", 5050))
    app.run(host='0.0.0.0', port=port)






























