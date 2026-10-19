import sqlite3


conn = sqlite3.connect("Chalan.db")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_name TEXT NOT NULL UNIQUE,
    fine INTEGER NOT NULL
)
""")


violations = [
    ("Triple Ride", 1000),
    ("No Parking", 100),
    ("No Helmet", 200),
    ("Overspeed", 1000)
]


cursor.executemany("""
INSERT OR IGNORE INTO violations
(
    violation_name,
    fine
)
VALUES (?, ?)
""", violations)


conn.commit()


print("--------------------------------")
print("CHALAN DATABASE")
print("--------------------------------")


cursor.execute("""
SELECT
    id,
    violation_name,
    fine
FROM violations
""")


for row in cursor.fetchall():
    print(row)


print("--------------------------------")
print("Chalan.db created successfully")
print("--------------------------------")


conn.close()