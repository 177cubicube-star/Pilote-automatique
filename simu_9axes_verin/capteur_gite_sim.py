"""capteur_gite_sim.py : sources de gîte EXTERNES à la centrale, pour le banc.

Trois sources possibles (choix `source_gite` du banc) :

  imu          : aucune source externe ; la fusion utilise l'accéléromètre de
                 l'ICM-20948 (situation actuelle).
  inclinometre : un inclinomètre du commerce. Un inclinomètre MEMS, ou un
                 pendule, mesure lui aussi la FORCE SPÉCIFIQUE : la gravité
                 mélangée aux accélérations du bateau. Il est simulé au même
                 endroit que la centrale (pas de bras de levier), sans biais, avec
                 un bruit faible et un filtre passe-bas réglable (beaucoup de
                 modèles en ont un). Hypothèse : il ne fait pas de fusion
                 gyroscopique interne (sinon, c'est une petite centrale AHRS).
  parfaite     : la gîte et le tangage VRAIS du bateau simulé. N'existe pas dans
                 la réalité : c'est la borne haute de ce qu'on peut gagner.

Stdlib seulement.
"""
from __future__ import annotations

import math
import random

from fusion_cap import ReferenceGite, inclinaison_par_accel

SOURCES_GITE = ("imu", "inclinometre", "parfaite")


class InclinometreSim:
    def __init__(self, bruit_g: float = 0.001, tau_filtre_s: float = 0.0, graine: int = 0):
        if bruit_g < 0 or tau_filtre_s < 0:
            raise ValueError("bruit_g et tau_filtre_s doivent être >= 0")
        self.bruit_g = bruit_g
        self.tau_filtre_s = tau_filtre_s
        self.rng = random.Random(graine)
        self.force = None

    def lire(self, force_corps, dt: float) -> ReferenceGite:
        g = 9.80665
        brute = [f + self.rng.gauss(0, self.bruit_g * g) for f in force_corps]
        if self.force is None or self.tau_filtre_s == 0:
            self.force = brute
        else:
            a = min(dt / self.tau_filtre_s, 1.0)
            self.force = [f + (b - f) * a for f, b in zip(self.force, brute)]
        gite, tangage = inclinaison_par_accel(self.force)
        return ReferenceGite(gite, tangage, exacte=False, force=tuple(self.force))


def reference_parfaite(gite_deg: float, tangage_deg: float) -> ReferenceGite:
    return ReferenceGite(math.radians(gite_deg), math.radians(tangage_deg), exacte=True)
