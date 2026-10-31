"""Q1-H — vérifie raw_command = ±(cal[0] + |speed|·cal[1]) sur chaque paire (speed, raw) d'une même boucle pypilot.
Usage : python verif_calib.py <fichier _pypilot.csv> <cal_port0> <cal_port1> <cal_tri0> <cal_tri1>"""
import csv, sys
from collections import defaultdict
f, p0, p1, s0, s1 = sys.argv[1], *map(float, sys.argv[2:6])
cal = {"port": (p0, p1), "starboard": (s0, s1)}
by = defaultdict(dict)
for t, k, v in list(csv.reader(open(f)))[1:]:
    if k in ("servo.speed", "servo.raw_command"):
        try:
            by[t].setdefault(k, []).append(float(v))
        except ValueError:
            pass
n = ok = 0; ecart = 0.0; mins = []
for d in by.values():
    sp = [x for x in d.get("servo.speed", []) if x != 0]
    if not sp or "servo.raw_command" not in d or d["servo.raw_command"][-1] == 0:
        continue
    s, raw = sp[-1], d["servo.raw_command"][-1]
    c = cal["port"] if s > 0 else cal["starboard"]
    att = (c[0] + abs(s) * c[1]) * (1 if s > 0 else -1)
    n += 1; e = abs(att - raw); ecart = max(ecart, e); ok += e < 1e-3; mins.append(abs(s))
print(f"paires {n}, concordantes (<1e-3) {ok}, écart max {ecart:.5f}, |speed| min {min(mins) if mins else None}")
