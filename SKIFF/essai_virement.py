"""essai_virement.py : virement à phases (spécification de Mathieu) sur le Lagoon de Skiff.

1. preparer() : près tribord amures, établi 10 s (fenêtre de virement_spec.py) ;
2. pont + ProgrammeVirementPhases : phases, puis reprise du cap sur Hfinal ;
3. mesures façon analyse_spec.py -> <tag>.csv, <tag>_journal.json, <tag>_mesures.json.

Pour un essai A/B, ne changer QUE --vitesse (vitesse max du vérin simulé).
Exemples :
  python essai_virement.py --vitesse 10 --tag virement_A_v10
  python essai_virement.py --vitesse 5  --tag virement_B_v5
  python essai_virement.py --phases essai3 --tag virement_essai3
  python essai_virement.py --phases "[[-15,10,0],[20,10,3],[25,5,8],[10,5,2],[0,5,0]]"
"""
import argparse
import json
import pathlib

from pont_skiff import Pont, SkiffClient
from preparer_essai import EssaiConfig, angle_symetrique, preparer
from verin_sequence import VerinConfig
from virement_phases import PHASES_ESSAI3, PHASES_ESSAI4, Phase, ProgrammeVirementPhases, mesurer

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:18081")
ap.add_argument("--cap", type=float, default=293.7, help="cap d'approche (près tribord amures)")
ap.add_argument("--angle", default="134", help="angle de virement (°) ou auto = près symétrique")
ap.add_argument("--vitesse", type=float, default=10.0, help="vitesse max du vérin simulé (°/s)")
ap.add_argument("--phases", default="essai4", help="essai4, essai3 ou liste JSON [[angle, °/s, s], ...]")
ap.add_argument("--duree", type=float, default=60.0, help="durée d'enregistrement après le TACK (s)")
ap.add_argument("--vent", type=float, default=7.2, help="vent vrai (m/s), du 000°")
ap.add_argument("--awa", type=float, default=40.0, help="vent apparent visé à l'approche (°)")
ap.add_argument("--tag", default="virement")
ap.add_argument("--dossier", default=".")
a = ap.parse_args()

phases = {"essai4": PHASES_ESSAI4, "essai3": PHASES_ESSAI3}.get(a.phases)
if phases is None:
    phases = tuple(Phase(*p) for p in json.loads(a.phases))

cfg_essai = EssaiConfig(cap_depart_deg=a.cap, vent_mps=a.vent, awa_cible_deg=a.awa, duree_stable_s=10.0)
client = SkiffClient(a.url)
d = preparer(client, cfg_essai)
angle = angle_symetrique(d.cap_depart_deg, cfg_essai) if a.angle == "auto" else float(a.angle)
print(f"approche : cap {d.cap_depart_deg:.1f}°, awa {d.awa_deg:+.1f}°, stw {d.stw_mps:.2f} m/s, "
      f"rotation {d.rotation_dps:+.2f} °/s")

prog = ProgrammeVirementPhases(phases, angle_virement_deg=angle, sens_virage=cfg_essai.sens_depart)
pont = Pont(client, VerinConfig(max_speed_dps=a.vitesse), prog)
pont.run(a.duree)

out = pathlib.Path(a.dossier)
out.mkdir(parents=True, exist_ok=True)
pont.ecrire_csv(str(out / f"{a.tag}.csv"))
m = mesurer(pont.rows, prog, vent_vient_de_deg=cfg_essai.vent_vient_de_deg)
m["reglages"] = {"vitesse_verin_dps": a.vitesse, "angle_virement_deg": angle,
                 "vent_mps": a.vent, "awa_approche_deg": a.awa,
                 "phases": [[p.angle_deg, p.vitesse_dps, p.maintien_s] for p in phases],
                 "approche": {"cap": d.cap_depart_deg, "awa": d.awa_deg, "stw": d.stw_mps}}
json.dump(prog.journal, open(out / f"{a.tag}_journal.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(m, open(out / f"{a.tag}_mesures.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for e in prog.journal:
    print("   ", e)
print(json.dumps(m, ensure_ascii=False, indent=1))
