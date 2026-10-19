import sqlite3
import os


conn = sqlite3.connect("user.db")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vehicle_reg TEXT NOT NULL UNIQUE,
    vehicle_type TEXT NOT NULL,
    vehnum TEXT NOT NULL,
    mobile TEXT NOT NULL,
    driver_photo TEXT
)
""")


users = [
    (
        "Srinivas",
        "TS10EX2850",
        "Bike",
        "V001",
        "9876543210",
        "driver_photos/srinivas.jpg"
    ),

    (
        "Raj",
        "TS09PA3330",
        "Car",
        "V002",
        "9876543211",
        "driver_photos/raj.jpg"
    ),

    (
        "Kiran",
        "TS10ED8176",
        "Bike",
        "V003",
        "9876543212",
        "driver_photos/kiran.jpg"
    )
]


cursor.executemany("""
INSERT OR IGNORE INTO users
(
    name,
    vehicle_reg,
    vehicle_type,
    vehnum,
    mobile,
    driver_photo
)
VALUES (?, ?, ?, ?, ?, ?)
""", users)


conn.commit()


print("--------------------------------")
print("USER DATABASE")
print("--------------------------------")


cursor.execute("""
SELECT
    id,
    name,
    vehicle_reg,
    vehicle_type,
    vehnum,
    mobile,
    driver_photo
FROM users
""")


for row in cursor.fetchall():
    print(row)


print("--------------------------------")
print("user.db created successfully")
print("--------------------------------")


conn.close()