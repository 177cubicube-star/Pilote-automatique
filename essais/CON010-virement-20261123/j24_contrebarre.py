"""J/24 : approche au près avec contre-barre posée AVANT le lof (demande de Mathieu, 2026-11-23). SIMULÉ.

Le scénario SailSim démarre barre à 0° et le J/24 lofe dès t = 0. On ne peut pas démarrer avant t = 0 :
la contre-barre de −15° (côté qui fait abattre) est donc déjà en place au premier pas de calcul,
ce qui équivaut à la poser au moins 1 s avant que le lof commence.
Pilote interne de SailSim (Nomoto, heading_hold), sans Docker.

Cas :
  fixe        : −15° tenus 60 s, sans pilote (équilibre naturel du bateau avec cette barre) ;
  pilote      : pilote dès t = 0, mais il PART de −15° (limiteur de vitesse de barre initialisé à −15°) ;
  fixe3_pilote: −15° tenus 3 s, puis le pilote, en partant de −15°.
Usage (Python du .venv de SailSim) : .venv\\Scripts\\python.exe j24_contrebarre.py
"""
import math, pathlib, sys

SAILSIM = pathlib.Path(r"C:\Users\mat_g\Documents\sailsim-test")
sys.path.insert(0, str(SAILSIM / "src"))
from sailsim.core.config import load_scenario, load_yacht, load_autopilot  # noqa: E402
from sailsim.autopilot.factory import create_autopilot  # noqa: E402
from sailsim.core.types import ControlCommand  # noqa: E402
from sailsim.core.runner import run_scenario  # noqa: E402
from sailsim.physics.aerodynamics import optimal_sail_trim  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent
import os; os.chdir(SAILSIM)  # SailSim cherche configs/ depuis le dossier courant
CONTRE = math.radians(-15.0)


class ContreBarre:
    """Tient la contre-barre pendant `duree` s, puis passe la main au pilote (qui part de cette barre)."""

    def __init__(self, pilote, duree):
        self.pilote, self.duree, self.t = pilote, duree, 0.0
        if pilote is not None:
            pilote._prev_rudder = CONTRE

    def set_target_heading(self, h):
        if self.pilote is not None:
            self.pilote.set_target_heading(h)

    def compute(self, sensors, dt):
        self.t += dt
        if self.pilote is None or self.t <= self.duree:
            return ControlCommand(rudder_angle=CONTRE, sail_trim=optimal_sail_trim(sensors.apparent_wind_angle))
        return self.pilote.compute(sensors, dt)


def cas(nom, duree, avec_pilote, u0):
    cfg = load_scenario(str(OUT / "approche_j24_310.toml"))
    cfg.initial_state.u = u0
    cfg.yacht = load_yacht("j24")
    pil = create_autopilot(load_autopilot("heading_hold"), yacht=cfg.yacht) if avec_pilote else None
    ap = ContreBarre(pil, duree)
    rec = run_scenario(cfg, ap)
    f = OUT / f"j24_contre15_{nom}_u{u0}.csv"
    rec.to_csv(str(f))
    import csv
    rows = list(csv.DictReader(open(f)))
    print(f"== {nom}, u0 = {u0} m/s")
    for t in (0, 0.5, 1, 2, 3, 4, 6, 10, 20, 40, 59.9):
        r = min(rows, key=lambda r: abs(float(r["t"]) - t))
        g = lambda k: float(r[k])
        print(f"  t={g('t'):5.1f} cap={g('psi_deg') % 360:6.1f} rot={g('r') * 57.3:5.1f}°/s barre={g('rudder_deg'):6.1f} "
              f"u={g('u') * 1.944:5.1f}nd vent_app={g('aw_angle_deg'):6.1f}")


if __name__ == "__main__" and "precharge" not in sys.argv:
    for u0 in (2.5, 4.0):
        cas("fixe", 1e9, False, u0)
        cas("pilote", 0.0, True, u0)
        cas("fixe3_pilote", 3.0, True, u0)


# Cas ajouté : pilote « sans à-coup » — son intégrateur est préchargé pour qu'il PARTE en tenant −15°
# (sinon il croit qu'une barre à 0° est la bonne et relâche la contre-barre à 5°/s dès t = 0).
def precharge(u0):
    import numpy as np
    from sailsim.autopilot import nomoto as N
    cfg = load_scenario(str(OUT / "approche_j24_310.toml")); cfg.initial_state.u = u0
    cfg.yacht = load_yacht("j24")
    pil = create_autopilot(load_autopilot("heading_hold"), yacht=cfg.yacht)
    y, U = cfg.yacht, max(u0, pil.U_min)
    q = 0.5 * N.RHO_WATER * (N.WAKE_FACTOR * U) ** 2
    Yd = -q * y.rudder_area * N.CL_ALPHA_RUDDER; Nd = Yd * y.rudder_x
    D00, D01, D10, D11 = -y.Yv, -(y.Yr - y.mass * U), -y.Nv, -y.Nr
    K = (D00 * Nd - D10 * Yd) / (D00 * D11 - D01 * D10)
    Kp, Kd, Ki = N._compute_gains(K, pil._T, pil.omega_n, pil.zeta)
    pil._prev_rudder = CONTRE

    class Precharge:
        def set_target_heading(self, h):
            pil.set_target_heading(h); pil._integral = CONTRE / Ki
        def compute(self, s, dt):
            return pil.compute(s, dt)
    rec = run_scenario(cfg, Precharge())
    f = OUT / f"j24_contre15_precharge_u{u0}.csv"; rec.to_csv(str(f))
    import csv
    rows = list(csv.DictReader(open(f)))
    print(f"== precharge, u0 = {u0} m/s (Ki = {Ki:.3f}, intégrale = {CONTRE / Ki:.3f})")
    for t in (0, 1, 2, 4, 6, 10, 20, 40, 59.9):
        r = min(rows, key=lambda r: abs(float(r["t"]) - t)); g = lambda k: float(r[k])
        print(f"  t={g('t'):5.1f} cap={g('psi_deg') % 360:6.1f} rot={g('r') * 57.3:5.1f}°/s barre={g('rudder_deg'):6.1f} "
              f"u={g('u') * 1.944:5.1f}nd vent_app={g('aw_angle_deg'):6.1f}")


if __name__ == "__main__" and "precharge" in sys.argv:
    for u0 in (2.5, 4.0):
        precharge(u0)
