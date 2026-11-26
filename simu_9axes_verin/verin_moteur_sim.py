"""verin_moteur_sim.py : vérin linéaire de barre commandé en VITESSE, comme par motor.ino.

Différence avec `verin_sequence.py` (racine du dépôt) : là-bas, on demande un
ANGLE et le vérin y va. Ici, on reproduit ce que reçoit vraiment le contrôle
moteur dans l'architecture DEC-014 : une commande de VITESSE normalisée
u ∈ [-1, 1] (pypilot envoie 0..2000, neutre 1000 ; u = (cmd - 1000) / 1000).
La position n'est connue que par le POTENTIOMÈTRE du vérin.

Ce que le modèle contient :
  - rampe de commande : 0,2 s du neutre à la pleine consigne (mesuré au banc
    virtuel sur motor.ino, simulé, CON-011 L1) ;
  - seuil de démarrage : en dessous d'une petite commande, le moteur ne tourne pas ;
  - vitesse qui baisse avec l'effort (droite effort-vitesse d'un moteur CC) ;
  - effort du safran qui ramène la barre au centre, proportionnel à l'angle ;
  - courant qui monte avec l'effort, coupure à la limite (pypilot `servo.max_current`,
    4,5 A par défaut, lu dans CON-011) ;
  - butées de fin de course (0 et 300 mm) ;
  - vis non réversible : vérin arrêté = barre tenue ;
  - jeu mécanique dans l'attache (le potentiomètre mesure la TIGE, pas la barre) ;
  - potentiomètre lu par un CAN 10 bits avec un peu de bruit ;
  - option « vérin détaché » : la tige bouge, la barre ne suit plus.

Tous les chiffres par défaut sont des HYPOTHÈSES, sauf la course (300 mm, choix
de Mathieu), la rampe (mesurée en simulé) et la limite de courant (défaut pypilot).
Le vérin n'est pas choisi : remplacer vitesse, effort de calage et courants par
ceux de sa fiche. Le bras de barre (distance mèche-attache) viendra du calcul
M1 et du relevé EXP-003.

Géométrie simplifiée : angle = asin(décalage depuis le centre / bras).
Signe : tige qui sort (x augmente) = angle positif = le bateau vire sur tribord.
Sur le bateau, le signe dépend du côté de montage : c'est un réglage.
Stdlib seulement.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigVerin:
    course_mm: float = 300.0                 # choix de Mathieu (2026-11-16)
    vitesse_max_mm_s: float = 30.0           # HYPOTHÈSE (vérin de référence Fenix)
    rampe_s: float = 0.2                     # mesuré (simulé) sur motor.ino
    seuil_demarrage: float = 0.05            # HYPOTHÈSE : |u| plus petit = moteur arrêté
    force_calage_n: float = 1500.0           # HYPOTHÈSE (> 445 N = 100 lbf exigés)
    courant_vide_a: float = 0.8              # HYPOTHÈSE
    courant_calage_a: float = 8.0            # HYPOTHÈSE
    limite_courant_a: float = 4.5            # pypilot servo.max_current par défaut
    tension_v: float = 12.0
    bras_barre_mm: float = 300.0             # HYPOTHÈSE -> ±30° pour ±150 mm
    effort_safran_n_par_deg: float = 10.0    # HYPOTHÈSE : ≈ 300 N à 30°
    jeu_mm: float = 1.0                      # HYPOTHÈSE
    bits_can: int = 10                       # CAN du Nano (motor.ino)
    bruit_can_lsb: float = 0.5               # HYPOTHÈSE

    def __post_init__(self):
        if self.course_mm <= 0 or self.vitesse_max_mm_s <= 0 or self.rampe_s <= 0:
            raise ValueError("course, vitesse et rampe doivent être > 0")
        if self.bras_barre_mm < self.course_mm / 2:
            raise ValueError("le bras de barre doit être >= la demi-course")
        if not 0 < self.courant_vide_a < self.courant_calage_a:
            raise ValueError("0 < courant_vide < courant_calage")


def _signe(x: float) -> int:
    return (x > 0) - (x < 0)


class Verin:
    def __init__(self, cfg: ConfigVerin = ConfigVerin(), graine: int = 0,
                 angle_initial_deg: float = 0.0):
        self.cfg = cfg
        self.rng = random.Random(graine)
        self.centre = cfg.course_mm / 2
        x0 = self.centre + cfg.bras_barre_mm * math.sin(math.radians(angle_initial_deg))
        self.x_tige = min(max(x0, 0.0), cfg.course_mm)
        self.x_barre = self.x_tige
        self.u_rampe = 0.0
        self.vitesse = 0.0
        self.courant = 0.0
        self.detache = False
        # compteurs pour comparer les réglages
        self.parcours_mm = 0.0
        self.inversions = 0
        self.energie_j = 0.0
        self.surintensites = 0
        self.temps_en_butee_s = 0.0
        self.commandes_invalides = 0
        self._dernier_sens = 0

    # ------------------------------------------------------------ angles
    def _angle_de(self, x: float) -> float:
        s = (x - self.centre) / self.cfg.bras_barre_mm
        return math.degrees(math.asin(max(-1.0, min(1.0, s))))

    def angle_barre_deg(self) -> float:
        """Angle RÉEL de la barre (ce que le bateau subit)."""
        return self._angle_de(self.x_barre)

    def lecture_can(self) -> int:
        pleine = (1 << self.cfg.bits_can) - 1
        brut = self.x_tige / self.cfg.course_mm * pleine + self.rng.gauss(0, self.cfg.bruit_can_lsb)
        return int(min(max(round(brut), 0), pleine))

    def angle_mesure_deg(self) -> float:
        """Angle vu par le POTENTIOMÈTRE (tige, quantifié, sans le jeu)."""
        pleine = (1 << self.cfg.bits_can) - 1
        return self._angle_de(self.lecture_can() / pleine * self.cfg.course_mm)

    # -------------------------------------------------------------- un pas
    def pas(self, u: float, dt: float) -> None:
        c = self.cfg
        if not math.isfinite(u):
            self.commandes_invalides += 1
            u = 0.0                                   # commande absurde : neutre
        u = max(-1.0, min(1.0, u))
        d_max = dt / c.rampe_s
        self.u_rampe += max(-d_max, min(d_max, u - self.u_rampe))

        sens = _signe(self.u_rampe) if abs(self.u_rampe) >= c.seuil_demarrage else 0
        effort = 0.0
        if sens:
            # le safran pousse la barre vers le centre : il freine si on s'en éloigne
            effort = max(0.0, c.effort_safran_n_par_deg * self.angle_barre_deg() * sens)
        charge = min(effort / c.force_calage_n, 1.0)
        v = self.u_rampe * c.vitesse_max_mm_s * (1.0 - charge) if sens else 0.0
        courant = (c.courant_vide_a * abs(self.u_rampe)
                   + (c.courant_calage_a - c.courant_vide_a) * charge) if sens else 0.0
        if courant > c.limite_courant_a:
            self.surintensites += 1
            v, courant, self.u_rampe = 0.0, 0.0, 0.0  # coupure, redémarrage en rampe

        x = self.x_tige + v * dt
        if x <= 0.0 or x >= c.course_mm:
            x = min(max(x, 0.0), c.course_mm)
            self.temps_en_butee_s += dt
            v = (x - self.x_tige) / dt
        self.parcours_mm += abs(x - self.x_tige)
        sens_reel = _signe(v)
        if sens_reel and self._dernier_sens and sens_reel != self._dernier_sens:
            self.inversions += 1
        if sens_reel:
            self._dernier_sens = sens_reel
        self.x_tige, self.vitesse, self.courant = x, v, courant
        self.energie_j += c.tension_v * courant * dt

        if self.detache:
            self.x_barre += (self.centre - self.x_barre) * min(dt / 1.0, 1.0)
        else:                                          # jeu : la barre suit avec du retard
            demi = c.jeu_mm / 2
            if self.x_tige - self.x_barre > demi:
                self.x_barre = self.x_tige - demi
            elif self.x_barre - self.x_tige > demi:
                self.x_barre = self.x_tige + demi
