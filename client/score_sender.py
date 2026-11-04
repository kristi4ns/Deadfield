import json
import threading
import urllib.request

# Servera adrese (serveris darbojas tavā datorā)
SERVER_URL = "http://127.0.0.1:8000"

# Pastāsta spēlei, kas notika: "idle", "sending", "saved" vai "failed"
send_status = "idle"


def send_score_now(player_name, points):
    # "global" ļauj šai funkcijai mainīt send_status augstāk
    global send_status

    data = json.dumps({"name": player_name, "points": points}).encode("utf-8")
    request = urllib.request.Request(
        SERVER_URL + "/scores",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=3):
            send_status = "saved"
    except OSError:
        # Serveris nedarbojas vai nepieņēma rezultātu
        send_status = "failed"


def send_score(player_name, points):
    # Sūtīšana notiek fonā, lai spēle neuzkaras, kamēr gaida serveri
    global send_status
    send_status = "sending"

    sender = threading.Thread(target=send_score_now, args=(player_name, points), daemon=True)
    sender.start()