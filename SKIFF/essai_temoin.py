"""essai_temoin.py : virement TÉMOIN sur Skiff (comme le témoin Nomoto de SailSim).

Même préparation que essai_virement.py, puis le maintien de cap INTERNE de Skiff reçoit
directement Hfinal (safran sans vérin, retard de 0,1 s seulement). Sert à savoir si
c'est la séquence ou le bateau simulé qui limite le virement.

Usage : python essai_temoin.py --angle 134 --tag temoin_134
"""
import argparse
import csv
import pathlib
import time

from pont_skiff import SkiffClient, awa_vient_de
from preparer_essai import EssaiConfig, angle_symetrique, preparer

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:18081")
ap.add_argument("--cap", type=float, default=293.7)
ap.add_argument("--angle", default="134", help="angle de virement (°) ou auto = près symétrique")
ap.add_argument("--duree", type=float, default=70.0)
ap.add_argument("--vent", type=float, default=7.2, help="vent vrai (m/s), du 000°")
ap.add_argument("--awa", type=float, default=40.0, help="vent apparent visé à l'approche (°)")
ap.add_argument("--tag", default="temoin")
ap.add_argument("--dossier", default=".")
a = ap.parse_args()

c = SkiffClient(a.url)
cfg = EssaiConfig(cap_depart_deg=a.cap, vent_mps=a.vent, awa_cible_deg=a.awa, duree_stable_s=10.0)
d = preparer(c, cfg)
angle = angle_symetrique(d.cap_depart_deg, cfg) if a.angle == "auto" else float(a.angle)
hf = (d.cap_depart_deg + cfg.sens_depart * angle) % 360.0
derive = c.get_state()["leeway_deg"]
c._req("POST", "/v1/sim/course", {"heading_true_deg": hf})
print(f"approche : cap {d.cap_depart_deg:.1f}°, awa {d.awa_deg:+.1f}°, stw {d.stw_mps:.2f} m/s, "
      f"dérive {derive:+.1f}° -> Hfinal {hf:.1f}° (angle {angle:.1f}°)")

out = pathlib.Path(a.dossier)
out.mkdir(parents=True, exist_ok=True)
t0, lignes, passe, prec = time.monotonic(), [], None, None
while time.monotonic() - t0 < a.duree:
    s = c.get_state()
    t, awa = time.monotonic() - t0, awa_vient_de(s)
    if prec is not None and passe is None and prec * awa < 0 and abs(awa) < 90:
        passe = t
    prec = awa
    lignes.append({"t_s": t, "heading_true_deg": s["heading_true_deg"], "rudder_deg_skiff": s["rudder_deg"],
                   "stw_mps": s["stw_mps"], "awa_vient_de_deg": awa, "skiff_elapsed_s": s["elapsed_s"]})
    time.sleep(0.1)
with open(out / f"{a.tag}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(lignes[0]))
    w.writeheader()
    w.writerows(lignes)
fin = lignes[-1]
print(f"vent apparent passe 0 à {passe if passe is None else round(passe, 1)} s | "
      f"final : cap {fin['heading_true_deg']:.1f}°, stw {fin['stw_mps']:.2f} m/s, awa {fin['awa_vient_de_deg']:+.1f}°")
