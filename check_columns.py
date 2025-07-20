import sqlite3

def check_columns():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # เช็กตาราง customers
    c.execute("PRAGMA table_info(customers)")
    customer_columns = [col[1] for col in c.fetchall()]
    print("📋 customers table:", customer_columns)

    # เช็กตาราง customer_proposals
    c.execute("PRAGMA table_info(customer_proposals)")
    proposal_columns = [col[1] for col in c.fetchall()]
    print("📋 customer_proposals table:", proposal_columns)

    conn.close()

if __name__ == '__main__':
    check_columns()