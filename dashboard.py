from flask import Flask, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

# ------------------ DATABASE ------------------

def get_latest_networks():
    conn = sqlite3.connect("wifi_scanner.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM networks
        WHERE id IN (
            SELECT MAX(id)
            FROM networks
            GROUP BY bssid
        )
        ORDER BY rssi DESC
        LIMIT 20
    """)

    data = cursor.fetchall()
    conn.close()
    return data


# ------------------ API ------------------

@app.route("/data")
def data():
    rows = get_latest_networks()

    result = []

    for row in rows:
        result.append({
            "node": row[1],
            "ssid": row[2],
            "bssid": row[3],
            "rssi": row[4],
            "channel": row[5],
            "encryption": row[6],
            "last_seen": row[11],
            "status": row[10],
            "flags": row[9]
        })

    return jsonify(result)


# ------------------ FRONTEND ------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>WiFi Security Dashboard</title>

<style>
body {
    font-family: Arial;
    background: #0f172a;
    color: #e2e8f0;
    margin: 20px;
}

h2 {
    text-align: center;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 10px;
}

th {
    background: #020617;
}

tr {
    border-bottom: 1px solid #1e293b;
}

tr:hover {
    background: #1e293b;
}

.green { color: lime; }
.orange { color: orange; }
.red { color: red; }
</style>

<script>
async function loadData() {
    const res = await fetch('/data');
    const data = await res.json();

    let table = "";

    data.forEach(n => {
        let rssiClass = n.rssi > -60 ? "green" :
                        n.rssi > -75 ? "orange" : "red";

        let status = n.status ? "⚠️" : "OK";

        table += `
        <tr>
            <td>${n.node}</td>
            <td>${n.ssid}</td>
            <td>${n.bssid}</td>
            <td class="${rssiClass}">${n.rssi}</td>
            <td>${n.channel}</td>
            <td>${n.encryption}</td>
            <td>${n.last_seen}</td>
            <td class="${n.status ? 'red':'green'}">${status}</td>
            <td>${n.flags}</td>
        </tr>
        `;
    });

    document.getElementById("tableBody").innerHTML = table;
}

// 🔥 Slower refresh (clean + realistic)
setInterval(loadData, 7000);
window.onload = loadData;
</script>

</head>

<body>

<h2>🔐 WiFi Security Dashboard</h2>

<table>
<tr>
<th>Node</th>
<th>SSID</th>
<th>BSSID</th>
<th>RSSI</th>
<th>Channel</th>
<th>Encryption</th>
<th>Last Seen</th>
<th>Status</th>
<th>Reason</th>
</tr>

<tbody id="tableBody"></tbody>
</table>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


# ------------------ RUN ------------------

app.run(host="0.0.0.0", port=5000)