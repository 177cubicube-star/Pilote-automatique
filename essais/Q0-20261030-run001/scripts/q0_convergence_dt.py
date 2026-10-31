"""Q0-05 — convergence en pas de temps sur SailSim (herostrat/sailsim ef1e293).

Rejoue calm_heading_hold avec le pilote Nomoto à dt = 0.05, 0.025, 0.0125 s
et compare le cap aux mêmes instants. Écart par rapport au pas le plus fin.
Usage : python -I q0_convergence_dt.py <profil>
"""

import math
import sys

from sailsim.autopilot.factory import create_autopilot
from sailsim.core.config import load_autopilot, load_scenario, load_yacht
from sailsim.core.runner import run_scenario

profil = sys.argv[1] if len(sys.argv) > 1 else "default"
pas = [0.05, 0.025, 0.0125]
instants = [1.0, 2.0, 5.0, 10.0, 20.0, 60.0, 120.0]
resultats = {}

for dt in pas:
    cfg = load_scenario("calm_heading_hold")
    yacht = load_yacht(profil)
    cfg = cfg.model_copy(update={"yacht": yacht, "dt": dt})
    pilote = create_autopilot(load_autopilot("nomoto"), yacht)
    rec = run_scenario(cfg, pilote)
    caps = []
    for t in instants:
        s = min(rec.steps, key=lambda st: abs(st.t - t))
        caps.append(math.degrees(s.sensors.heading))
    resultats[dt] = caps

print(f"profil {profil} — cap (°) par instant")
print("dt (s)   " + "".join(f"t={t:>5.0f}s " for t in instants))
for dt in pas:
    print(f"{dt:<8} " + "".join(f"{c:9.3f} " for c in resultats[dt]))
ref = resultats[pas[-1]]
for dt in pas[:-1]:
    ecart = max(abs(a - b) for a, b in zip(resultats[dt], ref))
    print(f"écart max dt={dt} vs dt={pas[-1]} : {ecart:.4f}°")
