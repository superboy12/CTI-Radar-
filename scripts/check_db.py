import sqlite3

db = sqlite3.connect("d:/SS/backend/cti_dev.db")
cur = db.cursor()

# Cek domain premanharum
cur.execute("SELECT domain, status, classification FROM domains WHERE domain LIKE '%harum%'")
print(cur.fetchall())
