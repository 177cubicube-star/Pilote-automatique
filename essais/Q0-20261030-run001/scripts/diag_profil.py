"""Diagnostic du lof des profils SailSim (herostrat/sailsim ef1e293).

Rejoue calm_heading_hold (vent 5 m/s au 60°, consigne 0°, 120 s) avec le
pilote Nomoto sur des variantes d'un profil, chaque variante ne changeant
qu'un ou deux paramètres. Les gains Nomoto sont recalculés pour chaque
variante (create_autopilot reçoit le yacht modifié).

Sortie par variante : erreur moyenne |cap|, écart max, cap final,
vitesse finale, barre finale, et résultat des portes du scénario
(erreur moyenne ≤ 3°, écart max ≤ 10°).
"""

import math

import numpy as np

from sailsim.autopilot.factory import create_autopilot
from sailsim.core.config import load_autopilot, load_scenario, load_yacht
from sailsim.core.runner import run_scenario


def essai(profil: str, modifs: dict) -> str:
    base = load_yacht(profil)
    yacht = base.model_copy(update=modifs)
    cfg = load_scenario("calm_heading_hold").model_copy(update={"yacht": yacht})
    pilote = create_autopilot(load_autopilot("nomoto"), yacht)
    rec = run_scenario(cfg, pilote)
    caps = np.array([math.degrees(s.sensors.heading) for s in rec.steps])
    caps = (caps + 180.0) % 360.0 - 180.0
    erreur_moy = float(np.mean(np.abs(caps)))
    ecart_max = float(np.max(np.abs(caps)))
    fin = rec.steps[-1]
    porte = "PASS" if (erreur_moy <= 3.0 and ecart_max <= 10.0) else "FAIL"
    return (
        f"err moy {erreur_moy:6.2f}° | max {ecart_max:6.2f}° | cap fin {caps[-1]:7.2f}° | "
        f"v fin {fin.sensors.speed_through_water:4.2f} m/s | "
        f"barre fin {math.degrees(fin.control.rudder_angle) if hasattr(fin, 'control') else float('nan'):6.1f}° | {porte}"
    )


VARIANTES = [
    ("j24", "J24 tel quel", {}),
    ("j24", "barre limitée sous le décrochage (rudder_max 0,30 rad = 17°)", {"rudder_max": 0.30}),
    ("j24", "safran 0,20 m² (×2)", {"rudder_area": 0.20}),
    ("j24", "safran 0,30 m² (×3)", {"rudder_area": 0.30}),
    ("j24", "avance réduite : sail_ce_x = 0,00 (CE 0,10 m derrière la quille)", {"sail_ce_x": 0.00}),
    ("j24", "équilibre neutre : sail_ce_x = keel_x = 0,10", {"sail_ce_x": 0.10}),
    ("j24", "safran ×2 + barre 17°", {"rudder_area": 0.20, "rudder_max": 0.30}),
    ("default", "default tel quel (CE devant la quille : mou)", {}),
    ("default", "default rendu ardent comme le J24 (CE 0,25 m derrière la quille)", {"sail_ce_x": -0.55}),
]

if __name__ == "__main__":
    for profil, nom, modifs in VARIANTES:
        print(f"[{profil}] {nom}\n    {essai(profil, modifs)}")
