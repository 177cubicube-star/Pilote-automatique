"""Q1-G / Q1-H — une exécution instrumentée avec le vrai pypilot et, au choix, sa couche servo.

Part du scénario pypilot_heading_hold (profil default) et permet de changer le cap
initial, la consigne, d'ajouter des changements de consigne, et d'envoyer à pypilot
des réglages avant le départ (gain servo, vitesses, calibrage...).

Un second client JSON-TCP journalise ce que pypilot calcule et l'état de sa couche
servo, horodatés à la réception.

Usage :
  python q1h_run.py --label L --out DOSSIER [--servo] [--duree 60] [--cap0 5.73]
                    [--consigne 0] [--manoeuvre 5:90 ...] [--set servo.gain=-1 ...]
Le clone SailSim utilisé est celui du PYTHONPATH.
"""
import argparse
import csv
import json
import math
import socket
import threading
import time

import numpy as np

from sailsim.autopilot.factory import create_autopilot
from sailsim.core.config import ManeuverConfig, ManeuverStep, load_autopilot, load_scenario, load_yacht
from sailsim.core.runner import run_scenario

p = argparse.ArgumentParser()
p.add_argument("--label", required=True)
p.add_argument("--out", required=True)
p.add_argument("--servo", action="store_true", help="couche servo pypilot (sim_servo_patch)")
p.add_argument("--duree", type=float, default=60.0)
p.add_argument("--cap0", type=float, default=None, help="cap initial [deg]")
p.add_argument("--consigne", type=float, default=0.0, help="consigne initiale [deg]")
p.add_argument("--manoeuvre", action="append", default=[], help="t:deg")
p.add_argument("--set", action="append", default=[], help="clé=valeur JSON envoyée à pypilot")
p.add_argument("--set-apres", action="append", default=[],
               help="t:clé=valeur, envoyé à pypilot t secondes (horloge murale) après le départ")
a = p.parse_args()

WATCH = ["ap.heading_command", "ap.heading", "ap.enabled", "servo.command", "servo.raw_command",
         "servo.engaged", "servo.flags", "servo.speed", "servo.state", "servo.position",
         "rudder.angle", "servo.calibration", "servo.gain", "servo.speed.min", "servo.speed.max",
         "rudder.range"]

log, stop = [], threading.Event()
s = socket.create_connection(("localhost", 23322), 2)
for kv in a.set:  # réglages avant que l'adaptateur ne se connecte
    s.sendall((kv + "\n").encode())
time.sleep(0.3)
s.sendall(("watch=" + json.dumps({k: True for k in WATCH}) + "\n").encode())
s.settimeout(0.2)


def watcher():
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


th = threading.Thread(target=watcher, daemon=True)
th.start()
time.sleep(0.5)

cfg = load_scenario("pypilot_heading_hold")
upd = {"yacht": load_yacht("default"), "duration_s": a.duree,
       "target_heading": math.radians(a.consigne)}
if a.cap0 is not None:
    upd["initial_state"] = cfg.initial_state.model_copy(update={"psi": math.radians(a.cap0)})
if a.manoeuvre:
    steps = [ManeuverStep(time_s=float(m.split(":")[0]), target_heading=math.radians(float(m.split(":")[1])))
             for m in a.manoeuvre]
    upd["maneuvers"] = ManeuverConfig(steps=steps)
cfg = cfg.model_copy(update=upd)
ap_cfg = load_autopilot("pypilot").model_copy(update={"pypilot_servo_layer": a.servo})
ap = create_autopilot(ap_cfg, cfg.yacht)
wall = []
orig_compute = ap.compute


def timed_compute(sensors, dt):
    wall.append(time.monotonic())
    return orig_compute(sensors, dt)


ap.compute = timed_compute


def envoi_differe(delai, kv):
    time.sleep(delai)
    s.sendall((kv + "\n").encode())
    log.append((time.monotonic(), "#envoi", kv))


for item in a.set_apres:
    d, kv = item.split(":", 1)
    threading.Thread(target=envoi_differe, args=(float(d), kv), daemon=True).start()
t_start = time.monotonic()
rec = run_scenario(cfg, ap)
t_total = time.monotonic() - t_start
time.sleep(0.3)
stop.set()
th.join(2)
ap.close()

rec.to_csv(f"{a.out}/{a.label}.csv")
t0 = wall[0]
with open(f"{a.out}/{a.label}_pypilot.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t_mur_s", "cle", "valeur"])
    for now, k, v in log:
        w.writerow([f"{now - t0:.3f}", k, v])

wd = np.diff(np.array(wall))
t = np.array([st.t for st in rec.steps])
cap = np.array([math.degrees(st.sensors.heading) for st in rec.steps])
cons = np.array([math.degrees(st.target_heading) for st in rec.steps]) if hasattr(rec.steps[0], "target_heading") else None
barre = np.array([math.degrees(st.control.rudder_angle) for st in rec.steps])


def num(k):
    out = []
    for now, kk, v in log:
        if kk == k:
            try:
                out.append((now - t0, float(v)))
            except ValueError:
                pass
    return out


raw = num("servo.raw_command")
# servo.flags arrive en texte (ServoFlags.get_str), ex. "SYNC ENGAGED SATURATED"
flags = [(now - t0, v.strip('"').split()) for now, k, v in log if k == "servo.flags"]
mots = sorted({m for _, ms in flags for m in ms})
# inversions de sens du moteur : intervalle entre deux commandes non nulles de signe opposé
dirs = [(tt, 1 if v > 0 else -1) for tt, v in raw if v != 0]
inv = [dirs[i][0] - dirs[i - 1][0] for i in range(1, len(dirs)) if dirs[i][1] != dirs[i - 1][1]]
sat = [tt for tt, ms in flags if "SATURATED" in ms]
butee = [tt for tt, ms in flags if "MIN_RUDDER_FAULT" in ms or "MAX_RUDDER_FAULT" in ms]
res = dict(
    label=a.label, couche_servo=a.servo, reglages=a.set, steps=len(rec.steps), wall_s=round(t_total, 2),
    dt_mur_moy_ms=round(float(wd.mean()) * 1000, 2), dt_mur_max_ms=round(float(wd.max()) * 1000, 1),
    cap_initial=round(float(cap[0]), 2), cap_final=round(float(cap[-1]), 2),
    cap_min=round(float(cap.min()), 2), cap_max=round(float(cap.max()), 2),
    barre_min=round(float(barre.min()), 2), barre_max=round(float(barre.max()), 2),
    raw_msgs=len(raw), raw_valeurs_distinctes=sorted({round(v, 4) for _, v in raw})[:12],
    inversions=len(inv), inversion_min_s=round(min(inv), 3) if inv else None,
    drapeaux_vus=mots,
    premier_saturated_s=round(sat[0], 2) if sat else None,
    premiere_butee_s=round(butee[0], 2) if butee else None,
    angle_pypilot_min=round(min((v for _, v in num("rudder.angle")), default=0), 2),
    angle_pypilot_max=round(max((v for _, v in num("rudder.angle")), default=0), 2),
    servo_command_min=round(min((v for _, v in num("servo.command")), default=0), 3),
    servo_command_max=round(max((v for _, v in num("servo.command")), default=0), 3),
    consigne_pypilot=sorted({v for _, v in num("ap.heading_command")})[:6],
)
print(json.dumps(res, ensure_ascii=False))
with open(f"{a.out}/{a.label}_bilan.json", "w") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
