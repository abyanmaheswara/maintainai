import sqlite3
import json
from datetime import datetime

DB_NAME = "maintainai.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diagnoses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_name TEXT,
        machine_type TEXT,
        machine_age INTEGER,
        suara TEXT,
        getaran TEXT,
        suhu TEXT,
        performa TEXT,
        gejala_lain TEXT,
        jam_operasi INTEGER,
        last_maintenance INTEGER,
        beban TEXT,
        severity TEXT,
        ai_result TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

def save_diagnosis(machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, severity, ai_result):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO diagnoses (machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, severity, ai_result, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, severity, json.dumps(ai_result), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_diagnoses():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM diagnoses ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "id": r[0], "machine_name": r[1], "machine_type": r[2], "machine_age": r[3],
            "suara": r[4], "getaran": r[5], "suhu": r[6], "performa": r[7],
            "gejala_lain": r[8], "jam_operasi": r[9], "last_maintenance": r[10],
            "beban": r[11], "severity": r[12], "ai_result": json.loads(r[13]), "timestamp": r[14]
        })
    return results

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM diagnoses")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM diagnoses WHERE severity='HIGH'")
    high = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM diagnoses WHERE severity='MEDIUM'")
    medium = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM diagnoses WHERE severity='LOW'")
    low = c.fetchone()[0]
    conn.close()
    return {"total": total, "high": high, "medium": medium, "low": low}

def get_last_n(n=5):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT machine_name, severity, timestamp FROM diagnoses ORDER BY id DESC LIMIT ?", (n,))
    rows = c.fetchall()
    conn.close()
    return [{"machine_name": r[0], "severity": r[1], "timestamp": r[2]} for r in rows]
