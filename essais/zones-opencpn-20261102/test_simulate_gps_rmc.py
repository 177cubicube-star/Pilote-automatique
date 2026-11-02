"""
test_simulate_gps_rmc.py

Controle automatique de simulate_gps_rmc.py (18 verifications) :
somme de controle NMEA, format des positions, deplacement, envoi TCP et UDP
en local, messages d'erreur. Aucune installation : bibliotheque standard seulement.

Utilisation : placer ce fichier dans le meme dossier que simulate_gps_rmc.py,
puis lancer :  python test_simulate_gps_rmc.py
Resultat attendu : "18 reussis, 0 en echec". Ce test n'utilise pas OpenCPN.
"""
import math
import os
import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simulate_gps_rmc as sim

SCRIPT = os.path.join(HERE, "simulate_gps_rmc.py")
results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(("OK   " if condition else "ECHEC"), name, detail)


# Verification independante de la somme de controle : exemple classique de la
# litterature NMEA, dont la somme de controle publiee est 6A.
known_body = "GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W"
check("somme de controle de l'exemple connu (6A)", sim.checksum(known_body) == "6A",
      sim.checksum(known_body))


# Analyseur independant d'une phrase RMC
def parse_rmc(line):
    m = re.fullmatch(r"\$([A-Z0-9,.]+)\*([0-9A-F]{2})\r?\n?", line)
    if not m:
        return None
    body, cs = m.groups()
    x = 0
    for ch in body:
        x ^= ord(ch)
    if f"{x:02X}" != cs:
        return None
    f = body.split(",")
    if f[0] != "GPRMC" or len(f) != 13:
        return None
    lat_deg = int(f[3][:2]) + float(f[3][2:]) / 60
    lon_deg = int(f[5][:3]) + float(f[5][3:]) / 60
    lat = lat_deg if f[4] == "N" else -lat_deg
    lon = lon_deg if f[6] == "E" else -lon_deg
    return {"status": f[2], "lat": lat, "lon": lon, "sog": float(f[7]),
            "cog": float(f[8]), "date": f[9], "mode": f[12]}


# Formats de position
for lat, lon in [(45.40, -71.89), (0.0, 0.0), (-33.8688, 151.2093),
                 (45.9999999, -71.9999999), (89.99999, 179.99999)]:
    s = sim.rmc_sentence(lat, lon, 4.0, 90.0, datetime(2026, 11, 2, 14, 30, 5, tzinfo=timezone.utc))
    p = parse_rmc(s)
    ok = p is not None and abs(p["lat"] - lat) < 2e-6 and abs(p["lon"] - lon) < 2e-6
    check(f"aller-retour position {lat}, {lon}", ok, s.strip())

# Pas de minutes egales a 60
s = sim.rmc_sentence(45.9999999, -71.9999999, 4.0, 90.0, datetime.now(timezone.utc))
check("pas de '60.0000' en minutes", ",4600.0000,N," in s and ",07200.0000,W," in s, s.strip())

# Deplacement : 1 noeud vers l'est pendant 3600 s = 1852 m environ
lat0, lon0 = 45.40, -71.89
lat1, lon1 = sim.advance(lat0, lon0, 90.0, 1.0, 3600.0)
dist_east = math.radians(lon1 - lon0) * 6371000 * math.cos(math.radians(lat0))
check("1 noeud vers l'est pendant 1 h = environ 1852 m", abs(dist_east - 1852.2) < 5 and abs(lat1 - lat0) < 1e-6,
      f"{dist_east:.1f} m")
lat2, lon2 = sim.advance(lat0, lon0, 0.0, 1.0, 3600.0)
dist_north = math.radians(lat2 - lat0) * 6371000
check("1 noeud vers le nord pendant 1 h = environ 1852 m", abs(dist_north - 1852.2) < 5, f"{dist_north:.1f} m")

# Execution reelle en mode impression seule
out = subprocess.run([sys.executable, SCRIPT, "--print-only", "--duration", "3", "--rate", "2"],
                     capture_output=True, text=True, timeout=30)
lines = [l for l in out.stdout.splitlines() if l.startswith("$")]
parsed = [parse_rmc(l.split("   (")[0]) for l in lines]
check("impression seule : code de sortie 0", out.returncode == 0, str(out.returncode))
check("impression seule : phrases valides", len(lines) >= 6 and all(parsed), f"{len(lines)} phrases")


# Test de reception TCP en local : un petit serveur joue le role d'OpenCPN
def tcp_test():
    received = []
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def serve():
        conn, _ = server.accept()
        conn.settimeout(5)
        buf = b""
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
        except socket.timeout:
            pass
        received.extend(buf.decode("ascii").split("\r\n"))
        conn.close()

    t = threading.Thread(target=serve)
    t.start()
    subprocess.run([sys.executable, SCRIPT, "--port", str(port), "--duration", "3", "--rate", "2",
                    "--quiet"], capture_output=True, text=True, timeout=30)
    t.join(timeout=10)
    server.close()
    return [l for l in received if l]


tcp = tcp_test()
tcp_parsed = [parse_rmc(l) for l in tcp]
check("TCP : phrases recues", len(tcp) >= 6, f"{len(tcp)} phrases")
check("TCP : toutes valides (somme de controle, 13 champs)", len(tcp) > 0 and all(tcp_parsed))
if tcp_parsed and all(tcp_parsed):
    check("TCP : la position avance vers l'est", tcp_parsed[-1]["lon"] > tcp_parsed[0]["lon"],
          f"{tcp_parsed[0]['lon']:.6f} -> {tcp_parsed[-1]['lon']:.6f}")


# Test de reception UDP en local
def udp_test():
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("127.0.0.1", 0))
    receiver.settimeout(6)
    port = receiver.getsockname()[1]
    proc = subprocess.Popen([sys.executable, SCRIPT, "--protocol", "udp", "--port", str(port),
                             "--duration", "3", "--rate", "2", "--quiet"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    got = []
    try:
        while True:
            data, _ = receiver.recvfrom(4096)
            got.append(data.decode("ascii"))
    except socket.timeout:
        pass
    proc.wait(timeout=10)
    receiver.close()
    return got


udp = udp_test()
udp_parsed = [parse_rmc(l) for l in udp]
check("UDP : phrases recues", len(udp) >= 6, f"{len(udp)} phrases")
check("UDP : toutes valides", len(udp) > 0 and all(udp_parsed))

# Connexion refusee : message clair et code de sortie different de 0
free = socket.socket()
free.bind(("127.0.0.1", 0))
closed_port = free.getsockname()[1]
free.close()
fail = subprocess.run([sys.executable, SCRIPT, "--port", str(closed_port), "--duration", "1"],
                      capture_output=True, text=True, timeout=30)
check("TCP sans serveur : sortie en erreur avec message", fail.returncode == 1 and "Connexion TCP impossible" in fail.stderr,
      f"code {fail.returncode}")

# Arguments invalides
bad = subprocess.run([sys.executable, SCRIPT, "--lat", "123", "--print-only"], capture_output=True, text=True, timeout=30)
check("latitude hors limites refusee", bad.returncode != 0, bad.stderr.strip().splitlines()[-1] if bad.stderr else "")

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)} reussis, {len(failed)} en echec")
sys.exit(1 if failed else 0)
