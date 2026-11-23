"""verin_sequence.py : séquences de commande d'un vérin de barre.

Une séquence est une liste d'ÉTAPES : « va à tel angle, à telle vitesse (ou en
telle durée), puis tiens X secondes ». Angle, vitesse et durée varient d'une
étape à l'autre.

Trois niveaux, du plus simple au plus proche du banc :
  1. step_verin()      : fait avancer le vérin d'UN pas de temps. C'est la brique
                         que le Pi (ou Skiff) peut appeler toutes les 50 ms avec
                         une consigne qui change selon la réaction du bateau.
  2. build_profile() + simulate() : rejoue un profil CHRONOMÉTRÉ (le maintien
                         démarre quand la CONSIGNE atteint la cible).
  3. run_closed_loop() : exécute les étapes avec RETOUR D'ANGLE (le maintien
                         démarre quand la POSITION entre dans une tolérance).

Chaque échantillon garde côte à côte trois angles :
  req_deg : ce que le Pi demande (avant toute limite)
  cmd_deg : la consigne après limites (vitesse max, butées)
  pos_deg : la position obtenue du vérin simulé

Unités : degrés de barre, secondes, °/s. La conversion en millimètres de course
dépend de la géométrie (non décidée) : elle n'est pas ici. Stdlib seulement.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field


def _finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} doit être un nombre fini (reçu {value!r})")


def _clamp(v: float, lo: float, hi: float) -> float:
    return min(max(v, lo), hi)


@dataclass(frozen=True)
class VerinConfig:
    angle_min_deg: float = -35.0   # butée côté bâbord
    angle_max_deg: float = 35.0    # butée côté tribord
    max_speed_dps: float = 8.0     # vitesse maximale du vérin (°/s de barre)
    tau_s: float = 0.10            # retard du 1er ordre (même idée que Skiff)
    dt_s: float = 0.05             # pas de simulation (20 Hz, comme Skiff)

    def __post_init__(self):
        for name in ("angle_min_deg", "angle_max_deg", "max_speed_dps", "tau_s", "dt_s"):
            _finite(name, getattr(self, name))
        if self.angle_min_deg >= self.angle_max_deg:
            raise ValueError("angle_min_deg doit être < angle_max_deg")
        if self.max_speed_dps <= 0 or self.tau_s <= 0 or self.dt_s <= 0:
            raise ValueError("max_speed_dps, tau_s et dt_s doivent être > 0")


@dataclass(frozen=True)
class Step:
    """Une étape : aller à target_deg, puis tenir hold_s secondes.

    Rapidité du déplacement, AU PLUS une des deux :
      speed_dps  : vitesse (°/s)
      duration_s : durée (s) ; la vitesse en est déduite
    Aucune des deux -> vitesse maximale du vérin.
    """
    target_deg: float
    speed_dps: float | None = None
    duration_s: float | None = None
    hold_s: float = 0.0

    def __post_init__(self):
        _finite("target_deg", self.target_deg)
        _finite("hold_s", self.hold_s)
        if self.speed_dps is not None:
            _finite("speed_dps", self.speed_dps)
        if self.duration_s is not None:
            _finite("duration_s", self.duration_s)
        if self.speed_dps is not None and self.duration_s is not None:
            raise ValueError("speed_dps et duration_s sont exclusifs")
        if self.speed_dps is not None and self.speed_dps <= 0:
            raise ValueError("speed_dps doit être > 0")
        if self.duration_s is not None and self.duration_s <= 0:
            raise ValueError("duration_s doit être > 0")
        if self.hold_s < 0:
            raise ValueError("hold_s doit être >= 0")


def _interp(points: list[tuple[float, float]], t: float) -> float:
    times = [p[0] for p in points]
    if t <= times[0]:
        return points[0][1]
    if t >= times[-1]:
        return points[-1][1]
    i = bisect.bisect_right(times, t)
    t0, a0 = points[i - 1]
    t1, a1 = points[i]
    if t1 == t0:
        return a1
    return a0 + (a1 - a0) * (t - t0) / (t1 - t0)


@dataclass
class Profile:
    """Deux consignes par morceaux linéaires, liste de (temps, angle) :
    points            : après limites (ce qu'on envoie au vérin)
    requested_points  : avant limites (ce que le Pi a demandé)"""
    points: list[tuple[float, float]]
    requested_points: list[tuple[float, float]]
    warnings: list[str] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return max(self.points[-1][0], self.requested_points[-1][0])

    def at(self, t: float) -> float:
        return _interp(self.points, t)

    def requested_at(self, t: float) -> float:
        return _interp(self.requested_points, t)


def build_profile(steps: list[Step], cfg: VerinConfig, start_deg: float = 0.0) -> Profile:
    """Transforme les étapes en consignes. Rien n'est corrigé en silence :
    toute limite appliquée est écrite dans Profile.warnings."""
    if not steps:
        raise ValueError("séquence vide")
    _finite("start_deg", start_deg)
    warnings: list[str] = []

    start = _clamp(start_deg, cfg.angle_min_deg, cfg.angle_max_deg)
    if start != start_deg:
        warnings.append(f"départ {start_deg:g}° hors butées, ramené à {start:g}°")

    t_l = t_r = 0.0                 # temps (consigne limitée / demandée)
    ang_l = ang_r = start
    pts_l = [(0.0, start)]
    pts_r = [(0.0, start)]

    for n, s in enumerate(steps, start=1):
        tgt_r = s.target_deg
        tgt_l = _clamp(tgt_r, cfg.angle_min_deg, cfg.angle_max_deg)
        if tgt_l != tgt_r:
            warnings.append(f"étape {n}: angle {tgt_r:g}° hors butées, ramené à {tgt_l:g}°")

        d_r, d_l = abs(tgt_r - ang_r), abs(tgt_l - ang_l)
        if s.duration_s is not None:
            v_r, v_l = d_r / s.duration_s, d_l / s.duration_s
        else:
            v_r = v_l = s.speed_dps if s.speed_dps is not None else cfg.max_speed_dps

        if v_l > cfg.max_speed_dps:
            warnings.append(
                f"étape {n}: vitesse demandée {v_l:.2f}°/s > max {cfg.max_speed_dps:g}°/s, "
                f"ramenée au max (le déplacement durera plus longtemps)")
            v_l = cfg.max_speed_dps

        move_r = d_r / v_r if d_r > 0 else 0.0
        move_l = d_l / v_l if d_l > 0 else 0.0
        for move, hold_pts, which in ((move_r, pts_r, "r"), (move_l, pts_l, "l")):
            if which == "r":
                t_r += move
                tgt, t_now = tgt_r, t_r
            else:
                t_l += move
                tgt, t_now = tgt_l, t_l
            if move > 0 or s.hold_s == 0:
                hold_pts.append((t_now, tgt))
            if s.hold_s > 0:
                if which == "r":
                    t_r += s.hold_s
                    hold_pts.append((t_r, tgt_r))
                else:
                    t_l += s.hold_s
                    hold_pts.append((t_l, tgt_l))
        ang_r, ang_l = tgt_r, tgt_l

    return Profile(points=pts_l, requested_points=pts_r, warnings=warnings)


@dataclass(frozen=True)
class Sample:
    t: float
    req_deg: float      # demande du Pi (avant limites)
    cmd_deg: float      # consigne après limites
    pos_deg: float      # position obtenue (vérin simulé)
    speed_dps: float    # vitesse instantanée obtenue


def step_verin(pos_deg: float, cmd_deg: float, cfg: VerinConfig,
               dt_s: float | None = None) -> tuple[float, float]:
    """Fait avancer le vérin d'UN pas de temps.
    dt_s : durée réellement écoulée (sur le Pi : écart entre deux lectures de
    time.monotonic()). Par défaut cfg.dt_s (banc hors ligne, pas fixe).
    cmd_deg doit être la consigne qui était active PENDANT cet intervalle.
    Ordre : retard du 1er ordre, puis limite de vitesse, puis butées.
    Retourne (nouvelle_position, vitesse_instantanée)."""
    if dt_s is None:
        dt_s = cfg.dt_s
    _finite("dt_s", dt_s)
    if dt_s <= 0:
        raise ValueError("dt_s doit être > 0")
    alpha = -math.expm1(-dt_s / cfg.tau_s)              # = 1 - exp(-dt/tau), plus précis
    max_move = cfg.max_speed_dps * dt_s
    move = _clamp(alpha * (cmd_deg - pos_deg), -max_move, max_move)
    new_pos = _clamp(pos_deg + move, cfg.angle_min_deg, cfg.angle_max_deg)
    return new_pos, (new_pos - pos_deg) / dt_s


def simulate(profile: Profile, cfg: VerinConfig, start_deg: float | None = None,
             settle_s: float = 1.0) -> list[Sample]:
    """Rejoue un profil chronométré sur le vérin simulé.
    Par défaut le vérin part du point de départ du profil. Passer start_deg permet
    de tester VOLONTAIREMENT un décalage ; hors butées -> ValueError."""
    _finite("settle_s", settle_s)
    if settle_s < 0:
        raise ValueError("settle_s doit être >= 0")
    if start_deg is None:
        start_deg = profile.points[0][1]
    _finite("start_deg", start_deg)
    if not cfg.angle_min_deg <= start_deg <= cfg.angle_max_deg:
        raise ValueError(f"start_deg {start_deg:g}° hors butées")

    pos = start_deg
    out = [Sample(0.0, profile.requested_at(0.0), profile.at(0.0), pos, 0.0)]
    n = int(math.ceil((profile.duration_s + settle_s) / cfg.dt_s))
    for k in range(1, n + 1):
        t = k * cfg.dt_s
        pos, speed = step_verin(pos, profile.at(t), cfg)
        out.append(Sample(t, profile.requested_at(t), profile.at(t), pos, speed))
    return out


@dataclass
class RunResult:
    samples: list[Sample]
    warnings: list[str]


def _ramp(cur: float, target: float, speed: float, dt: float) -> float:
    step = speed * dt
    if abs(target - cur) <= step:
        return target
    return cur + math.copysign(step, target - cur)


def run_closed_loop(steps: list[Step], cfg: VerinConfig, start_deg: float = 0.0,
                    tol_deg: float = 0.2, step_timeout_s: float = 30.0,
                    settle_s: float = 1.0) -> RunResult:
    """Exécute les étapes AVEC retour d'angle : le maintien (hold_s) ne démarre que
    lorsque la consigne a atteint la cible ET que la position est à tol_deg près.
    Si la position n'y arrive pas en step_timeout_s, un avertissement est écrit et
    on passe à l'étape suivante SANS maintien (rien n'est présenté comme atteint)."""
    if not steps:
        raise ValueError("séquence vide")
    for name, v in (("start_deg", start_deg), ("tol_deg", tol_deg),
                    ("step_timeout_s", step_timeout_s), ("settle_s", settle_s)):
        _finite(name, v)
    if tol_deg <= 0 or step_timeout_s <= 0 or settle_s < 0:
        raise ValueError("tol_deg et step_timeout_s doivent être > 0, settle_s >= 0")

    dt = cfg.dt_s
    warnings: list[str] = []
    pos = _clamp(start_deg, cfg.angle_min_deg, cfg.angle_max_deg)
    if pos != start_deg:
        warnings.append(f"départ {start_deg:g}° hors butées, ramené à {pos:g}°")
    cmd = req = pos
    t = 0.0
    samples = [Sample(0.0, req, cmd, pos, 0.0)]

    def tick(tgt_r, v_r, tgt_l, v_l):
        nonlocal t, pos, cmd, req
        req = _ramp(req, tgt_r, v_r, dt)
        cmd = _ramp(cmd, tgt_l, v_l, dt)
        pos, speed = step_verin(pos, cmd, cfg)
        t += dt
        samples.append(Sample(t, req, cmd, pos, speed))

    for n, s in enumerate(steps, start=1):
        tgt_r = s.target_deg
        tgt_l = _clamp(tgt_r, cfg.angle_min_deg, cfg.angle_max_deg)
        if tgt_l != tgt_r:
            warnings.append(f"étape {n}: angle {tgt_r:g}° hors butées, ramené à {tgt_l:g}°")
        if s.duration_s is not None:
            v_r, v_l = abs(tgt_r - req) / s.duration_s, abs(tgt_l - cmd) / s.duration_s
        else:
            v_r = v_l = s.speed_dps if s.speed_dps is not None else cfg.max_speed_dps
        if v_l > cfg.max_speed_dps:
            warnings.append(
                f"étape {n}: vitesse demandée {v_l:.2f}°/s > max {cfg.max_speed_dps:g}°/s, "
                f"ramenée au max")
            v_l = cfg.max_speed_dps

        elapsed, reached = 0.0, False
        while elapsed <= step_timeout_s:
            if cmd == tgt_l and abs(pos - tgt_l) <= tol_deg:
                reached = True
                break
            tick(tgt_r, v_r, tgt_l, v_l)
            elapsed += dt
        if not reached:
            warnings.append(
                f"étape {n}: {tgt_l:g}° non atteint à ±{tol_deg:g}° en {step_timeout_s:g} s "
                f"(position {pos:.2f}°), maintien sauté")
            continue
        held = 0.0
        while held < s.hold_s - 1e-9:
            tick(tgt_r, v_r, tgt_l, v_l)
            held += dt

    for _ in range(int(math.ceil(settle_s / dt))):
        tick(req, 0.0, cmd, 0.0)
    return RunResult(samples=samples, warnings=warnings)


def max_tracking_error(samples: list[Sample]) -> float:
    return max(abs(s.cmd_deg - s.pos_deg) for s in samples)


if __name__ == "__main__":
    cfg = VerinConfig()
    seq = [
        Step(10, duration_s=2.0, hold_s=1.0),   # en 2 s ; maintien dès que la POSITION y est
        Step(-15, speed_dps=5.0, hold_s=0.5),   # lent
        Step(25, duration_s=1.0),               # trop rapide pour le vérin -> limité
        Step(0, duration_s=4.0),                # retour doux
    ]
    res = run_closed_loop(seq, cfg)
    for w in res.warnings:
        print("AVERTISSEMENT:", w)
    print("  t(s)  demande  consigne  position  vitesse")
    for s in res.samples[::10]:
        print(f"{s.t:6.1f} {s.req_deg:8.2f} {s.cmd_deg:9.2f} {s.pos_deg:9.2f} {s.speed_dps:8.2f}")
