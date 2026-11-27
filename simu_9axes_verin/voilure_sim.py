"""voilure_sim.py : effet du vent sur le voilier, en plusieurs « bateaux plausibles ».

Pourquoi ce module (étape 1, 2026-11-26)
----------------------------------------
Jusqu'ici, le banc faisait gîter le bateau selon une loi simple (carré de la
vitesse du vent × |sin(angle)|), instantanée, et l'ardeur était constante.
L'anticipation apprenait une loi de la même forme : elle retrouvait ce que le
banc avait mis dedans. Pour comparer des algorithmes honnêtement, la physique doit
DIFFÉRER de leurs hypothèses, et un bon algorithme doit tenir sur plusieurs
bateaux, pas sur un seul.

Ce que chaque profil peut changer (toutes les valeurs sont des HYPOTHÈSES
plausibles, aucune n'est mesurée sur le Capri 22) :
  - table de gîte : force de gîte selon l'angle de vent apparent, irrégulière
    (au lieu de |sin|) ;
  - retard de gîte : la force dans les voiles s'établit avec un retard ;
  - ardeur non linéaire : la tendance à remonter au vent grandit avec la gîte ;
  - moment des voiles : un couple de lacet direct, selon l'angle, en plus de
    l'effet de la gîte ;
  - polaire : la vitesse du bateau suit le vent réel et l'allure ; elle change le
    vent apparent et l'efficacité du safran (force en vitesse²).

Conventions : angles en degrés ; vent de tribord (angle > 0) -> gîte sur bâbord
(< 0) ; perturbation positive = le cap augmente (degrés de barre équivalents).
Stdlib seulement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

AWS_REFERENCE_MS = 7.0
TWS_REFERENCE_MS = 6.0


def interpoler(table, x: float) -> float:
    """Interpolation linéaire dans une table ((x, y), ...) triée ; bornée aux extrémités."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def _verifier_table(nom, table):
    if table is None:
        return
    xs = [p[0] for p in table]
    if len(table) < 2 or xs != sorted(xs) or xs[0] > 0 or xs[-1] < 180:
        raise ValueError(f"{nom} : au moins 2 points, triés, couvrant 0 à 180°")


@dataclass(frozen=True)
class ProfilVoilier:
    nom: str
    description: str
    gite_ref_deg: float = 12.0              # gîte pour un coefficient 1 et 7 m/s apparents
    table_gite: tuple | None = None         # None : |sin(angle)| (loi du banc v3)
    tau_gite_s: float = 0.0                 # retard d'établissement de la force
    gite_max_deg: float = 35.0
    k_gite_lacet: float = 0.15              # ardeur à faible gîte (° de barre par ° de gîte)
    k_gite_lacet_par_deg: float = 0.0       # ardeur supplémentaire par degré de gîte
    table_lacet_voiles: tuple | None = None  # couple direct, ° de barre éq. à 7 m/s, selon |angle|
    polaire: bool = False
    vitesse_ref_ms: float = 2.5
    table_vitesse: tuple = ((0, 0.0), (35, 0.55), (50, 0.85), (90, 1.0), (135, 1.0), (180, 0.8))
    exposant_vent: float = 0.5               # vitesse ∝ (vent réel / 6 m/s) ^ exposant
    vitesse_max_ms: float = 3.0              # HYPOTHÈSE : vitesse de carène d'un 22 pieds (≈ 5,8 nœuds)
    tau_vitesse_s: float = 10.0

    def __post_init__(self):
        _verifier_table("table_gite", self.table_gite)
        _verifier_table("table_lacet_voiles", self.table_lacet_voiles)
        _verifier_table("table_vitesse", self.table_vitesse)
        for nom in ("gite_ref_deg", "tau_gite_s", "gite_max_deg", "k_gite_lacet",
                    "k_gite_lacet_par_deg", "vitesse_ref_ms", "vitesse_max_ms", "tau_vitesse_s"):
            if getattr(self, nom) < 0:
                raise ValueError(f"{nom} doit être >= 0")


class Voilure:
    """État du profil (retards) ; à appeler à chaque pas, après le pas du bateau."""

    def __init__(self, profil: ProfilVoilier):
        self.p = profil
        self.gite_vent = 0.0
        self.vitesse = profil.vitesse_ref_ms
        self._premier = True

    def coef_gite(self, angle_abs: float) -> float:
        if self.p.table_gite is None:
            return abs(math.sin(math.radians(angle_abs)))
        return interpoler(self.p.table_gite, angle_abs)

    def vitesse_polaire(self, vent_reel_ms: float, angle_vent_reel_deg: float) -> float:
        p = self.p
        v = (p.vitesse_ref_ms * (max(vent_reel_ms, 0.0) / TWS_REFERENCE_MS) ** p.exposant_vent
             * interpoler(p.table_vitesse, abs(angle_vent_reel_deg)))
        return min(max(v, 0.3), p.vitesse_max_ms)

    def pas(self, dt, angle_apparent_deg, vitesse_apparente_ms, vent_reel_ms, angle_vent_reel_deg,
            gite_bateau_deg):
        """Retourne (gîte due au vent, perturbation de lacet en ° de barre, vitesse du bateau)."""
        p = self.p
        signe = math.copysign(1.0, angle_apparent_deg)
        cible = -signe * min(p.gite_ref_deg * (vitesse_apparente_ms / AWS_REFERENCE_MS) ** 2
                             * self.coef_gite(abs(angle_apparent_deg)), p.gite_max_deg)
        if self._premier or p.tau_gite_s == 0:
            self.gite_vent = cible
        else:
            self.gite_vent += (cible - self.gite_vent) * min(dt / p.tau_gite_s, 1.0)
        ardeur = p.k_gite_lacet + p.k_gite_lacet_par_deg * abs(gite_bateau_deg)
        perturbation = -ardeur * gite_bateau_deg
        if p.table_lacet_voiles is not None:
            perturbation += signe * interpoler(p.table_lacet_voiles, abs(angle_apparent_deg)) \
                * (vitesse_apparente_ms / AWS_REFERENCE_MS) ** 2
        if p.polaire:
            cible_v = self.vitesse_polaire(vent_reel_ms, angle_vent_reel_deg)
            if self._premier or p.tau_vitesse_s == 0:
                self.vitesse = cible_v
            else:
                self.vitesse += (cible_v - self.vitesse) * min(dt / p.tau_vitesse_s, 1.0)
        self._premier = False
        return self.gite_vent, perturbation, self.vitesse


# Table de gîte « irrégulière » : forte du près au travers, creux au bon plein, faible au portant
TABLE_GITE_IRREGULIERE = ((0, 0.0), (25, 0.55), (40, 1.0), (55, 1.15), (70, 0.95), (90, 1.05),
                          (110, 0.7), (135, 0.4), (160, 0.2), (180, 0.1))
# Couple direct des voiles : lofe au près (grand-voile), s'inverse au portant (spi absent)
TABLE_LACET_VOILES = ((0, 0.0), (30, 0.8), (45, 1.2), (60, 0.9), (90, 0.3), (120, -0.4),
                      (150, -0.8), (180, 0.0))

TABLE_LACET_VOILES_MODERE = tuple((a, v * 0.5) for a, v in TABLE_LACET_VOILES)

PROFILS = {p.nom: p for p in (
    ProfilVoilier("reference", "Physique du banc v3 (contrôle : doit redonner les mêmes chiffres)"),
    ProfilVoilier("ardent", "Comme la référence, ardeur 0,40 (banc v3, renfort_compas_ardent)",
                  k_gite_lacet=0.40),
    ProfilVoilier("ardeur_progressive", "L'ardeur grandit avec la gîte : 0,20 à plat, 0,60 à 20°",
                  k_gite_lacet=0.20, k_gite_lacet_par_deg=0.02),
    ProfilVoilier("gite_lente", "Ardent, la force s'établit en 3 s (retard entre la rafale et la gîte)",
                  k_gite_lacet=0.40, tau_gite_s=3.0),
    ProfilVoilier("voiles_irregulieres", "Table de gîte irrégulière et couple direct des voiles, ardeur 0,25",
                  k_gite_lacet=0.25, table_gite=TABLE_GITE_IRREGULIERE,
                  table_lacet_voiles=TABLE_LACET_VOILES),
    ProfilVoilier("polaire", "La vitesse suit le vent et l'allure (safran en vitesse²), ardeur 0,30",
                  k_gite_lacet=0.30, polaire=True),
    ProfilVoilier("tout", "Tout à la fois (ardeur 0,15 + 0,01/°, retard 3 s, voiles irrégulières "
                  "à couple modéré, polaire) : environ 9° de barre ardente en permanence",
                  k_gite_lacet=0.15, k_gite_lacet_par_deg=0.01, tau_gite_s=3.0,
                  table_gite=TABLE_GITE_IRREGULIERE, table_lacet_voiles=TABLE_LACET_VOILES_MODERE,
                  polaire=True),
)}
