import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("PRAGMA table_info(customers)")
for row in c.fetchall():
    print(row)

conn.close()