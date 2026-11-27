"""vent_sim.py : vent réel simulé, et vent apparent vu du pont ou de la tête de mât.

Vent RÉEL : direction d'où il vient (0 = nord) et vitesse, avec une oscillation
lente de direction, des bascules franches et des rafales de vitesse.

Vent APPARENT : celui que « sent » le bateau en avançant. On compose le vent réel
avec le vent de la vitesse du bateau :
    air vu du bateau = vitesse du vent − vitesse du bateau
Angle de vent apparent (AWA) : d'où vient ce vent, par rapport à l'étrave,
positif à TRIBORD, négatif à BÂBORD (convention de Signal K).

En TÊTE DE MÂT, deux effets s'ajoutent, que la girouette ne sait pas séparer :
  - la gîte : la girouette tourne dans le plan du mât penché ; elle ne voit que la
    part du vent perpendiculaire au mât ;
  - le mouvement du mât : quand le bateau roule, la tête de mât balaie l'air de
    bâbord à tribord (vitesse = vitesse de roulis × hauteur), ce qui fait osciller
    l'angle mesuré.
C'est la « correction de la gîte et du mouvement » prévue par DEC-005 (disposition 14).

Tout est HYPOTHÈSE de simulation. Stdlib seulement.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from bateau_sim import ned_vers_corps

NOEUD = 0.514444


def enrouler_180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


@dataclass(frozen=True)
class Bascule:
    debut_s: float
    angle_deg: float          # rotation du vent réel (positif = vers la droite, adonnante ou refusante selon l'amure)
    duree_s: float = 10.0     # temps pour tourner


@dataclass(frozen=True)
class Renforcement:
    """Séquence « le vent forcit et tourne » : montée, palier, retour."""
    debut_s: float
    gain_vitesse: float = 0.5      # +50 % de vitesse au palier
    rotation_deg: float = 15.0     # le vent tourne en même temps (positif = vers la droite)
    montee_s: float = 8.0
    palier_s: float = 30.0
    descente_s: float = 10.0

    def part(self, t: float) -> float:
        """De 0 (hors séquence) à 1 (au palier)."""
        d = t - self.debut_s
        if d <= 0 or d >= self.montee_s + self.palier_s + self.descente_s:
            return 0.0
        if d < self.montee_s:
            return d / self.montee_s
        if d < self.montee_s + self.palier_s:
            return 1.0
        return 1.0 - (d - self.montee_s - self.palier_s) / self.descente_s


@dataclass(frozen=True)
class ConfigVent:
    direction_deg: float = 270.0        # d'où vient le vent réel (0 = nord)
    vitesse_ms: float = 6.0             # ≈ 11,7 nœuds
    oscillation_deg: float = 5.0        # oscillation lente de direction
    periode_oscillation_s: float = 90.0
    rafale_ratio: float = 0.15          # ± 15 % de vitesse
    periode_rafale_s: float = 25.0
    bascules: tuple = ()
    renforcements: tuple = ()


class VentReel:
    def __init__(self, cfg: ConfigVent, graine: int = 0):
        self.cfg = cfg
        rng = random.Random(graine + 4241)
        self._ph1, self._ph2, self._ph3 = (rng.uniform(0, 2 * math.pi) for _ in range(3))

    def a(self, t: float):
        """(direction d'où vient le vent en degrés, vitesse en m/s) à l'instant t."""
        c = self.cfg
        d = c.direction_deg + c.oscillation_deg * math.sin(2 * math.pi * t / c.periode_oscillation_s + self._ph1)
        for b in c.bascules:
            if t > b.debut_s:
                d += b.angle_deg * min(1.0, (t - b.debut_s) / max(b.duree_s, 1e-6))
        w1 = 2 * math.pi / c.periode_rafale_s
        v = c.vitesse_ms * (1 + c.rafale_ratio * (0.7 * math.sin(w1 * t + self._ph2)
                                                  + 0.3 * math.sin(2.7 * w1 * t + self._ph3)))
        for r in c.renforcements:
            k = r.part(t)
            v *= 1 + r.gain_vitesse * k
            d += r.rotation_deg * k
        return d % 360.0, max(v, 0.0)


def air_relatif_ned(direction_deg: float, vitesse_ms: float, cap_deg: float, vitesse_bateau_ms: float):
    """Vitesse de l'air par rapport au bateau, dans le repère terrestre (nord, est, bas)."""
    d, c = math.radians(direction_deg), math.radians(cap_deg)
    vent = (-vitesse_ms * math.cos(d), -vitesse_ms * math.sin(d))      # le vent VA vers l'opposé
    bateau = (vitesse_bateau_ms * math.cos(c), vitesse_bateau_ms * math.sin(c))
    return (vent[0] - bateau[0], vent[1] - bateau[1], 0.0)


def angle_et_vitesse(ux: float, uy: float):
    """D'où vient l'air (angle depuis l'étrave, positif tribord) et sa vitesse, depuis
    sa vitesse (ux vers l'avant, uy vers tribord) dans le plan de mesure."""
    return math.degrees(math.atan2(-uy, -ux)), math.hypot(ux, uy)


def apparent_au_pont(direction_deg, vitesse_ms, cap_deg, vitesse_bateau_ms):
    """Vent apparent « vrai » au niveau du bateau (sans gîte ni mouvement de mât)."""
    n, e, _ = air_relatif_ned(direction_deg, vitesse_ms, cap_deg, vitesse_bateau_ms)
    c = math.radians(cap_deg)
    ux = n * math.cos(c) + e * math.sin(c)
    uy = -n * math.sin(c) + e * math.cos(c)
    return angle_et_vitesse(ux, uy)


def apparent_en_tete_de_mat(direction_deg, vitesse_ms, cap_deg, vitesse_bateau_ms,
                            gite_deg, tangage_deg, vitesses_corps_rad, hauteur_mat_m):
    """Ce que voit une girouette parfaite en tête de mât (plan perpendiculaire au mât)."""
    air = air_relatif_ned(direction_deg, vitesse_ms, cap_deg, vitesse_bateau_ms)
    ux, uy, _ = ned_vers_corps(air, math.radians(gite_deg), math.radians(tangage_deg),
                               math.radians(cap_deg))
    p, q, _r = vitesses_corps_rad
    h = hauteur_mat_m                              # tête de mât en (0, 0, −h) dans le repère corps
    v_mat_x, v_mat_y = -q * h, p * h               # ω × r
    return angle_et_vitesse(ux - v_mat_x, uy - v_mat_y)
