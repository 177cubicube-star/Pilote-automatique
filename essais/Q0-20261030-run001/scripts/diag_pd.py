"""Le J24 simulé est-il barrable ? Essai avec un PD simple à gains positifs.

Loi : barre = Kp * erreur - Kd * vitesse_de_lacet, erreur = consigne - cap.
Signe vérifié en Q0-06 (profil default) : barre positive => cap croissant.
Avec limite de position (rudder_max du profil) et limite de vitesse de barre.
Scénario calm_heading_hold (vent 5 m/s au 60°, consigne 0°, 120 s).
"""

import math
import sys

import numpy as np

from sailsim.core.config import load_scenario, load_yacht
from sailsim.core.runner import run_scenario
from sailsim.core.types import ControlCommand
from sailsim.physics.aerodynamics import optimal_sail_trim


class PDSimple:
    def __init__(self, kp, kd, rudder_max, rate_deg_s):
        self.kp, self.kd, self.max = kp, kd, rudder_max
        self.rate = math.radians(rate_deg_s)
        self.cible = 0.0
        self.prec = 0.0

    def set_target_heading(self, h):
        self.cible = h

    def compute(self, s, dt):
        e = math.atan2(math.sin(self.cible - s.heading), math.cos(self.cible - s.heading))
        d = self.kp * e - self.kd * s.yaw_rate
        d = max(-self.max, min(self.max, d))
        d = self.prec + max(-self.rate * dt, min(self.rate * dt, d - self.prec))
        self.prec = d
        return ControlCommand(rudder_angle=d, sail_trim=optimal_sail_trim(s.apparent_wind_angle))


def essai(profil, kp, kd, rate, modifs=None):
    y = load_yacht(profil).model_copy(update=modifs or {})
    cfg = load_scenario("calm_heading_hold").model_copy(update={"yacht": y})
    rec = run_scenario(cfg, PDSimple(kp, kd, y.rudder_max, rate))
    caps = (np.array([math.degrees(st.sensors.heading) for st in rec.steps]) + 180) % 360 - 180
    barre = np.array([math.degrees(st.control.rudder_angle) for st in rec.steps])
    moy, mx = float(np.mean(np.abs(caps))), float(np.max(np.abs(caps)))
    # établissement : premier instant après lequel |cap| reste < 2°
    hors = np.where(np.abs(caps) >= 2.0)[0]
    t_etab = rec.steps[hors[-1] + 1].t if len(hors) and hors[-1] + 1 < len(rec.steps) else (0.0 if not len(hors) else float("nan"))
    porte = "PASS" if (moy <= 3 and mx <= 10) else "FAIL"
    return (f"Kp={kp:<4} Kd={kd:<4} vitesse barre {rate:>4}°/s | err moy {moy:5.2f}° | max {mx:5.2f}° | "
            f"établi(<2°) à {t_etab:5.1f} s | barre moy fin {np.mean(barre[-200:]):6.1f}° | "
            f"v fin {rec.steps[-1].sensors.speed_through_water:4.2f} m/s | {porte}")


if __name__ == "__main__":
    profils = sys.argv[1:] or ["j24"]
    for p in profils:
        print(f"== {p}")
        for kp, kd, rate in [(1.0, 1.0, 5), (1.5, 1.5, 5), (2.0, 2.0, 5), (1.0, 1.0, 10), (2.0, 2.0, 10)]:
            print("   " + essai(p, kp, kd, rate))
