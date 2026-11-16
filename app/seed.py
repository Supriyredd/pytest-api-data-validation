"""Deterministic synthetic data for the demo pharmacy API. No real patient data."""
import random
import sqlite3

FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Riley", "Morgan", "Jamie", "Avery", "Quinn"]
LAST = ["Smith", "Lee", "Patel", "Garcia", "Nguyen", "Brown", "Khan", "Lopez", "Wilson", "Clark"]
DRUGS = [("DRG-100", "Amoxicillin 500mg"), ("DRG-200", "Lisinopril 10mg"), ("DRG-300", "Metformin 850mg"),
         ("DRG-400", "Atorvastatin 20mg"), ("DRG-500", "Albuterol Inhaler")]
STATUSES = ["PENDING", "FILLED", "PICKED_UP", "CANCELLED"]


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS prescriptions;
        DROP TABLE IF EXISTS patients;
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            mrn TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_year INTEGER NOT NULL
        );
        CREATE TABLE prescriptions (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            drug_code TEXT NOT NULL,
            drug_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            refills_remaining INTEGER NOT NULL CHECK (refills_remaining >= 0),
            status TEXT NOT NULL
        );
        """
    )


def seed(conn: sqlite3.Connection, patients: int = 25, seed_value: int = 42) -> None:
    rnd = random.Random(seed_value)
    create_schema(conn)
    rx_id = 1
    for pid in range(1, patients + 1):
        conn.execute(
            "INSERT INTO patients VALUES (?,?,?,?,?)",
            (pid, f"SYN{pid:06d}", rnd.choice(FIRST), rnd.choice(LAST), rnd.randint(1940, 2005)),
        )
        for _ in range(rnd.randint(1, 4)):
            code, name = rnd.choice(DRUGS)
            conn.execute(
                "INSERT INTO prescriptions VALUES (?,?,?,?,?,?,?)",
                (rx_id, pid, code, name, rnd.choice([30, 60, 90]), rnd.randint(0, 5), rnd.choice(STATUSES)),
            )
            rx_id += 1
    conn.commit()
