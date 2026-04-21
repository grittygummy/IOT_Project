

import serial
import json
import sqlite3
from datetime import datetime
import pytz

# ------------------ CONFIG ------------------

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200
KNOWN_NETWORKS = {}

IST = pytz.timezone('Asia/Kolkata')
SAFE_SSIDS = {
    "Student",
    "Staff",
}



# ------------------ DB SETUP ------------------

def init_db():
    conn = sqlite3.connect("wifi_scanner.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS networks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node INTEGER,
        ssid TEXT,
        bssid TEXT,
        rssi INTEGER,
        channel INTEGER,
        encryption TEXT,
        is_hidden INTEGER,
        suspicious INTEGER,
        flags TEXT,
        status INTEGER,
        seen_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# ------------------ INSERT ------------------

def insert_entry(conn, entry):
    cursor = conn.cursor()

    ssid = entry["ss"]
    bssid = entry["bm"]

    suspicious = 0
    reason = []

    # --- 1. Allowlist check (FIRST) ---
    if ssid not in SAFE_SSIDS:
        suspicious = 1
        reason.append("UNKNOWN_SSID")

    # --- 2. Rogue AP detection (SECOND, only for safe SSIDs) ---
    if ssid in SAFE_SSIDS:
        if ssid in KNOWN_NETWORKS:
            if bssid not in KNOWN_NETWORKS[ssid]:
                suspicious = 1
                reason.append("ROGUE_AP_DIFFERENT_BSSID")
                KNOWN_NETWORKS[ssid].add(bssid)
        else:
            KNOWN_NETWORKS[ssid] = {bssid}

    # --- 3. Signal anomaly (OPTIONAL but useful) ---
    if entry["rs"] > -40:
        suspicious = 1
        reason.append("UNUSUAL_STRONG_SIGNAL")

    # --- 4. Hidden network ---
    if entry["hi"] == 1:
        reason.append("HIDDEN_NETWORK")

    cursor.execute("""
    INSERT INTO networks (
        node, ssid, bssid, rssi, channel,
        encryption, is_hidden, suspicious,
        flags, status, seen_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry["n"],
        ssid,
        bssid,
        entry["rs"],
        entry["ch"],
        entry["en"],
        entry["hi"],
        suspicious,
        json.dumps(reason),
        suspicious,
        datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

# ------------------ MAIN LOOP ------------------

def main():
    print("[INFO] Starting serial listener...")

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    conn = sqlite3.connect("wifi_scanner.db")

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()

            if not line:
                continue

            data = json.loads(line)

            insert_entry(conn, data)

            print(f"[Node {data['n']}] {data['ss']} | RSSI: {data['rs']}")

        except Exception as e:
            print("[ERROR]", e)


# ------------------ RUN ------------------

if __name__ == "__main__":
    init_db()
    main()