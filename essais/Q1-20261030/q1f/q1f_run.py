"""Q1-F — une exécution instrumentée de pypilot_heading_hold (profil default) avec le vrai pypilot.

Mesure, pour chaque pas de simulation, le temps réel écoulé (horloge murale) et enregistre en
parallèle, par un second client JSON-TCP, ce que pypilot calcule : consigne, cap filtré,
vitesse de lacet filtrée et commande servo, horodatés.

Usage : python q1f_run.py <étiquette> <dossier de sortie>
Le clone SailSim utilisé est celui du PYTHONPATH (origine ou corrigé).
"""
import csv
import json
import math
import socket
import sys
import threading
import time

import numpy as np

from sailsim.autopilot.factory import create_autopilot
from sailsim.core.config import load_autopilot, load_scenario, load_yacht
from sailsim.core.runner import run_scenario

label, outdir = sys.argv[1], sys.argv[2]
WATCH = ["ap.heading_command", "ap.heading", "ap.enabled", "servo.command",
         "imu.heading_lowpass", "imu.headingrate_lowpass"]

# ---- second client : journal de ce que voit pypilot ----------------------------------
log, stop = [], threading.Event()


def watcher():
    s = socket.create_connection(("localhost", 23322), 2)
    s.sendall(("watch=" + json.dumps({k: True for k in WATCH}) + "\n").encode())
    s.settimeout(0.2)
    buf = ""
    while not stop.is_set():
        try:
            chunk = s.recv(65536).decode()
        except socket.timeout:
            continue
        if not chunk:
            break
        buf += chunk
        *lines, buf = buf.split("\n")
        now = time.monotonic()
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                log.append((now, k, v))
    s.close()


th = threading.Thread(target=watcher, daemon=True)
th.start()
time.sleep(0.5)

# ---- exécution instrumentée -----------------------------------------------------------
cfg = load_scenario("pypilot_heading_hold")
yacht = load_yacht("default")
cfg = cfg.model_copy(update={"yacht": yacht})
ap_cfg = load_autopilot("pypilot")
ap = create_autopilot(ap_cfg, yacht)
wall = []
orig_compute = ap.compute


def timed_compute(sensors, dt):
    wall.append(time.monotonic())
    return orig_compute(sensors, dt)


ap.compute = timed_compute
t_start = time.monotonic()
rec = run_scenario(cfg, ap)
t_total = time.monotonic() - t_start
stop.set()
th.join(2)

# ---- sorties --------------------------------------------------------------------------
rec.to_csv(f"{outdir}/{label}.csv")
t0 = wall[0]
with open(f"{outdir}/{label}_pypilot.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t_mur_s", "valeur", "contenu"])
    for now, k, v in log:
        w.writerow([f"{now - t0:.3f}", k, v])

wd = np.diff(np.array(wall))
caps = np.array([math.degrees(s.sensors.heading) for s in rec.steps])
caps = (caps + 180) % 360 - 180
t = np.array([s.t for s in rec.steps])
barre = np.array([math.degrees(s.control.rudder_angle) for s in rec.steps])
fin = t >= 30
res = dict(
    label=label, steps=len(rec.steps), sim_s=float(t[-1]), wall_s=round(t_total, 2),
    dt_mur_moy_ms=round(float(wd.mean()) * 1000, 2), dt_mur_ecart_type_ms=round(float(wd.std()) * 1000, 2),
    dt_mur_max_ms=round(float(wd.max()) * 1000, 1),
    erreur_moy=round(float(np.mean(np.abs(caps))), 2), ecart_max=round(float(np.max(np.abs(caps))), 2),
    cap_moy_t30=round(float(np.mean(caps[fin])), 2), cap_t60=round(float(caps[-1]), 2),
    cap_max_10s=round(float(caps[t <= 15].max()), 2), barre_max=round(float(barre.max()), 2),
    servo_msgs=sum(1 for _, k, _ in log if k == "servo.command"),
)
print(json.dumps(res, ensure_ascii=False))
with open(f"{outdir}/{label}_bilan.json", "w") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
