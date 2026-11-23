"""chercher_cap.py : trouve le cap d'approche (tribord amures) qui donne le vent apparent visé.

Le cap qui donne +40° apparents dépend du vent et de la vitesse du bateau. On prépare
avec une tolérance large, on mesure l'angle obtenu, on corrige le cap de l'écart
(cap qui monte = plus près du vent = angle apparent qui baisse), et on recommence.
Usage : python chercher_cap.py --vent 10 --awa 40
"""
import argparse

from pont_skiff import SkiffClient
from preparer_essai import EssaiConfig, preparer

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:18081")
ap.add_argument("--vent", type=float, default=7.2)
ap.add_argument("--awa", type=float, default=40.0)
ap.add_argument("--cap", type=float, default=293.7, help="cap de départ de la recherche")
ap.add_argument("--iterations", type=int, default=4)
a = ap.parse_args()

c, cap = SkiffClient(a.url), a.cap
for i in range(1, a.iterations + 1):
    d = preparer(c, EssaiConfig(cap_depart_deg=cap, vent_mps=a.vent, awa_cible_deg=a.awa, awa_tol_deg=30.0))
    ecart = d.awa_deg - a.awa
    print(f"essai {i} : cap {cap:.1f}° -> awa {d.awa_deg:+.1f}°, stw {d.stw_mps:.2f} m/s (écart {ecart:+.1f}°)")
    if abs(ecart) <= 1.5:
        break
    cap = (cap + ecart) % 360.0
print(f"CAP {cap:.1f}")
