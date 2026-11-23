"""essai_detecteur.py : essai du DetecteurPassageVent sur Skiff (pas un programme de virement).

Prépare le Lagoon au près tribord amures, puis barre à -20° (signe Skiff : l'étrave
vient sur tribord) jusqu'au passage du vent détecté, puis remet la barre à 0°.
Sert à vérifier la chaîne préparation -> pont -> détecteur, et à voir ce que
produit un retour de barre au moment exact du passage du vent.

Usage : python essai_detecteur.py --csv essai_detecteur_01.csv
"""
import argparse

from pont_skiff import Pont, SkiffClient, awa_vient_de
from preparer_essai import DetecteurPassageVent, EssaiConfig, preparer
from verin_sequence import VerinConfig

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:18081")
ap.add_argument("--cap", type=float, default=293.7)
ap.add_argument("--barre", type=float, default=-20.0, help="angle de barre pendant le virement (signe Skiff)")
ap.add_argument("--vitesse", type=float, default=8.0, help="vitesse max du vérin (°/s)")
ap.add_argument("--duree", type=float, default=25.0)
ap.add_argument("--csv", default="essai_detecteur_01.csv")
a = ap.parse_args()

client = SkiffClient(a.url)
d = preparer(client, EssaiConfig(cap_depart_deg=a.cap))
print(f"départ : cap {d.cap_depart_deg:.1f}°, awa {d.awa_deg:+.1f}°, stw {d.stw_mps:.2f} m/s, "
      f"cap_final {d.cap_final_deg:.1f}°")

det = DetecteurPassageVent()


def consigne(t, state, pos):
    det.maj(t, awa_vient_de(state))
    return 0.0 if det.passe else a.barre


pont = Pont(client, VerinConfig(max_speed_dps=a.vitesse), consigne)
pont.run(a.duree)
pont.ecrire_csv(a.csv)
fin = client.get_state()
print(f"armé : {det.arme} | passage du vent à t = {det.t_passage_s}")
print(f"fin : cap {fin['heading_true_deg']:.1f}°, stw {fin['stw_mps']:.2f} m/s, "
      f"awa {awa_vient_de(fin):+.1f}° (cap_final visé {d.cap_final_deg:.1f}°)")
print(f"{len(pont.rows)} lignes -> {a.csv}")
