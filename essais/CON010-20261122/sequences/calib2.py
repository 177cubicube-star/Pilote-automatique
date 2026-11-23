"""Calibration : position_command fonctionne-t-il pilote en veille, et quel signe fait tourner le bateau de quel côté ?"""
import json, time
from banc import *

restart()
c = Client(["imu.heading", "rudder.angle", "ap.enabled", "servo.speed.max", "servo.position_command"])
c.set("servo.speed.min", 30)
p = sailsim("pypilot_heading_hold", OUT / "calib2.csv")
# attendre que l'angle de barre soit valide (SailSim a démarré), puis 12 s de tenue de cap
while c.num("rudder.angle") is None:
    time.sleep(0.2)
time.sleep(12)
res = {}
for cmd in (+10, -10):
    c.set("ap.enabled", False, "veille")
    c.set("servo.speed.max", 60)
    h0 = c.num("imu.heading"); c.set("servo.command", 0, "contournement"); c.set("servo.position_command", cmd)
    time.sleep(4)
    res[cmd] = {"cap_avant": h0, "cap_apres": c.num("imu.heading"), "barre_pypilot": c.num("rudder.angle"),
                "speed_max_lu": c.v.get("servo.speed.max")}
    c.set("servo.command", 0); c.set("servo.position_command", 0); time.sleep(3)
c.set("servo.speed.max", 100); c.set("ap.enabled", True)
out = p.communicate()[0]
c.close()
json.dump({"resultats": res, "journal": c.log}, open(OUT / "calib2_bilan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, indent=1))
