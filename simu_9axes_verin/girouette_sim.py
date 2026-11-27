"""girouette_sim.py : girouette-anémomètre électronique SIMULÉE, qui parle NMEA 0183.

Même principe que la centrale : le capteur simulé produit les VRAIES phrases que
produirait une girouette du commerce, ici `$WIMWV`, et le lecteur Python
(`nmea_mwv.py`) les lit comme il lira celles du vrai capteur sur l'entrée
NMEA 0183 prévue au socle (DEC-005, disposition 11 ; DEC-008).

Phrase MWV (champs vérifiés dans la doc NMEA de gpsd et dans le convertisseur
MWV de Signal K, @signalk/nmea0183-signalk 3.20.1) :

    $WIMWV,<angle 0 à 359,9>,R,<vitesse>,N,A*hh
            angle relatif, compté depuis l'étrave dans le sens horaire
            (au-delà de 180 : vent de bâbord) ; R = relatif (apparent) ;
            vitesse en nœuds (N) ; A = donnée valide ; hh = somme de contrôle.

Défauts simulés (HYPOTHÈSES, aucun capteur n'est choisi) : bruit d'angle et de
vitesse, amortissement interne, défaut d'alignement (calibration, disposition 16),
cadence d'émission, et coupure à un instant donné.
Stdlib seulement.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

NOEUD = 0.514444


def somme_controle(corps: str) -> str:
    v = 0
    for ch in corps:
        v ^= ord(ch)
    return f"{v:02X}"


def phrase_mwv(angle_deg: float, vitesse_ms: float, valide: bool = True, emetteur: str = "WI") -> str:
    """Construit une phrase MWV relative. angle_deg : positif tribord, négatif bâbord."""
    angle = angle_deg % 360.0
    if round(angle, 1) >= 360.0:
        angle = 0.0
    corps = f"{emetteur}MWV,{angle:.1f},R,{vitesse_ms / NOEUD:.1f},N,{'A' if valide else 'V'}"
    return f"${corps}*{somme_controle(corps)}\r\n"


@dataclass(frozen=True)
class ConfigGirouette:
    cadence_hz: float = 4.0            # HYPOTHÈSE (beaucoup de capteurs : 1 à 10 Hz)
    bruit_angle_deg: float = 1.0
    bruit_vitesse_ms: float = 0.1
    amortissement_s: float = 0.3       # filtre interne du capteur
    decalage_deg: float = 0.0          # défaut d'alignement de la girouette (calibration)
    coupure_a_s: float | None = None   # le capteur se tait à partir de cet instant


class GirouetteSim:
    def __init__(self, cfg: ConfigGirouette = ConfigGirouette(), graine: int = 0):
        if cfg.cadence_hz <= 0 or cfg.amortissement_s < 0:
            raise ValueError("cadence > 0 et amortissement >= 0")
        self.cfg = cfg
        self.rng = random.Random(graine + 977)
        self._ux = self._uy = None
        self._chrono = 0.0
        self.phrases = 0

    def mettre_a_jour(self, angle_deg: float, vitesse_ms: float, t: float, dt: float) -> list:
        """Reçoit le vent vu en tête de mât ; retourne les phrases émises pendant ce pas."""
        c = self.cfg
        a = math.radians(angle_deg + c.decalage_deg)
        ux, uy = -vitesse_ms * math.cos(a), -vitesse_ms * math.sin(a)     # filtre sur le vecteur
        if self._ux is None or c.amortissement_s == 0:
            self._ux, self._uy = ux, uy
        else:
            k = min(dt / c.amortissement_s, 1.0)
            self._ux += (ux - self._ux) * k
            self._uy += (uy - self._uy) * k
        if c.coupure_a_s is not None and t >= c.coupure_a_s:
            return []
        self._chrono += dt
        if self._chrono + 1e-9 < 1.0 / c.cadence_hz:
            return []
        self._chrono -= 1.0 / c.cadence_hz
        angle = math.degrees(math.atan2(-self._uy, -self._ux)) + self.rng.gauss(0, c.bruit_angle_deg)
        vitesse = max(0.0, math.hypot(self._ux, self._uy) + self.rng.gauss(0, c.bruit_vitesse_ms))
        self.phrases += 1
        return [phrase_mwv(angle, vitesse)]
