"""Q0-06 — essais à barre fixe sur SailSim (herostrat/sailsim ef1e293).

Pour chaque profil et chaque angle de barre fixe, rejoue le scénario
calm_heading_hold (vent 5 m/s au 60°, cap initial ~5,7°, vitesse 2 m/s)
avec FixedRudderAutopilot, puis relève cap et vitesse à quelques instants.
But : vérifier le sens de giration et voir si le bateau lofe barre au neutre.
"""

import math
import sys

from sailsim.autopilot.fixed import FixedRudderAutopilot
from sailsim.core.config import load_scenario, load_yacht
from sailsim.core.runner import run_scenario

profils = sys.argv[1:] or ["default", "j24"]
angles_deg = [-10.0, -5.0, 0.0, 5.0, 10.0]
instants = [0.0, 5.0, 10.0, 30.0, 60.0]

for profil in profils:
    print(f"=== profil {profil}")
    for a in angles_deg:
        cfg = load_scenario("calm_heading_hold")
        cfg = cfg.model_copy(update={"yacht": load_yacht(profil), "duration_s": 60.0})
        rec = run_scenario(cfg, FixedRudderAutopilot(math.radians(a)))
        morceaux = []
        for t in instants:
            s = min(rec.steps, key=lambda st: abs(st.t - t))
            cap = math.degrees(s.sensors.heading)
            v = s.sensors.speed_through_water
            morceaux.append(f"t={t:>4.0f}s cap={cap:7.1f}° v={v:4.2f}")
        print(f"barre {a:+5.1f}° | " + " | ".join(morceaux))
