from datetime import datetime
import sqlite3


# ============================================================
# DATABASE SETTINGS
# ============================================================

DB_NAME = "Chalan.db"


# ============================================================
# CREATE CHALLANS TABLE
# ============================================================

def create_challan_table():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS challans (

            challan_id INTEGER PRIMARY KEY AUTOINCREMENT,

            violation_name TEXT NOT NULL,

            fine INTEGER NOT NULL,

            vehicle_reg TEXT NOT NULL,

            owner_name TEXT,

            vehicle_type TEXT,

            mobile TEXT,

            challan_date TEXT NOT NULL,

            status TEXT NOT NULL

        )
        """
    )

    conn.commit()

    conn.close()


# ============================================================
# GENERATE CHALLAN ID
# ============================================================

def generate_challan_id():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT challan_id
        FROM challans
        ORDER BY challan_id DESC
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    conn.close()

    if result:

        return result[0] + 1

    return 1


# ============================================================
# SAVE CHALLAN
# ============================================================

def save_challan(
    violation,
    fine,
    number_plate,
    owner_name,
    vehicle_type,
    mobile
):

    create_challan_table()

    challan_id = generate_challan_id()

    challan_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    status = "Generated"


    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO challans (

            challan_id,
            violation_name,
            fine,
            vehicle_reg,
            owner_name,
            vehicle_type,
            mobile,
            challan_date,
            status

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            challan_id,
            violation,
            fine,
            number_plate,
            owner_name,
            vehicle_type,
            mobile,
            challan_date,
            status
        )
    )


    conn.commit()

    conn.close()


    return challan_id


# ============================================================
# CREATE CHALLAN
# ============================================================

def generate_challan(
    violation,
    fine,
    number_plate,
    owner_name,
    vehicle_type,
    mobile
):

    challan_id = save_challan(

        violation=violation,

        fine=fine,

        number_plate=number_plate,

        owner_name=owner_name,

        vehicle_type=vehicle_type,

        mobile=mobile
    )


    challan_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    challan = f"""
========================================
           TRAFFIC CHALLAN
========================================

Challan ID     : {challan_id}

Violation      : {violation}

Fine           : ₹{fine}

Vehicle Number : {number_plate}

Owner Name     : {owner_name}

Vehicle Type   : {vehicle_type}

Mobile Number  : {mobile}

Date           : {challan_date}

Status         : Generated

========================================
"""


    return challan


# ============================================================
# TEST THE CHALLAN GENERATOR
# ============================================================

if __name__ == "__main__":

    challan = generate_challan(

        violation="No Helmet",

        fine=200,

        number_plate="TS10ED8176",

        owner_name="Kiran",

        vehicle_type="Bike",

        mobile="9876543212"
    )


    print()

    print(challan)