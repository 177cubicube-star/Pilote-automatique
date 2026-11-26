"""regulateurs.py : les lois de barre à comparer.

Tous les régulateurs ont la même forme :
    u = regulateur.calculer(entree, dt)
avec `entree` = cap estimé, vitesse de lacet estimée, consigne, angle de barre
MESURÉ (potentiomètre), et `u` ∈ [-1, 1] = commande de vitesse du vérin,
celle que recevrait le contrôle moteur. Ils sont appelés à 20 Hz (cadence de pypilot).

Deux familles :

1. `pid_position` — PID « en cascade », à la manière de Fenix :
     boucle extérieure  : erreur de cap -> ANGLE de barre voulu
         angle = Kp·erreur + Ki·∫erreur − Kd·vitesse_de_lacet
       (le terme D utilise le gyroscope plutôt que de dériver le cap : moins de
        bruit, et pas de coup de barre quand on change la consigne) ;
     boucle intérieure : écart d'angle -> vitesse du vérin, avec une BANDE MORTE
       et une hystérésis pour que le vérin ne « chasse » pas sans arrêt.
   Anti-emballement de l'intégrale : bornée à ±i_max_deg, gelée quand l'angle
   voulu est déjà en limite, et (option `zone_integrale_deg`) gelée tant que
   l'erreur dépasse cette zone : pendant un grand changement de cap, l'intégrale
   ne se « charge » pas, ce qui évite le dépassement qu'on voit sinon.

2. `pypilot_basic` — portage du pilote `basic` de pypilot 0.71 et du mécanisme
   « période » de `Servo.do_command`, repris tel quel de
   `simulations/pypilot_sim.py` (archive du 2026-10-30, non importée pour ne pas
   la modifier). La commande est directement une VITESSE de servo :
       cmd = P·err + D·lacet + DD·accél_lacet + PR·√|err| + FF·variation_consigne
   Terme I du vrai pilote : NON porté (absent du portage d'origine).
   Ce n'est pas pypilot qui tourne : c'est une lecture de son code.

Convention : u > 0 fait sortir la tige = angle positif = cap qui augmente.
Erreur de cap = consigne − cap, ramenée dans [-180, 180).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def enrouler_180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def _borner(x: float, lim: float) -> float:
    return max(-lim, min(lim, x))


@dataclass(frozen=True)
class EntreeRegulateur:
    cap_deg: float
    taux_lacet_dps: float
    consigne_deg: float
    angle_barre_deg: float      # mesuré par le potentiomètre


class RegulateurPIDPosition:
    type_ = "pid_position"

    def __init__(self, kp: float = 1.2, ki: float = 0.03, kd: float = 2.0,
                 i_max_deg: float = 8.0, angle_max_deg: float = 25.0,
                 ecart_max_deg: float = 30.0, kp_position: float = 0.25,
                 bande_morte_deg: float = 0.5, tau_filtre_d_s: float = 0.0,
                 zone_integrale_deg: float | None = None):
        for nom, v in (("kp", kp), ("ki", ki), ("kd", kd), ("i_max_deg", i_max_deg),
                       ("kp_position", kp_position), ("bande_morte_deg", bande_morte_deg),
                       ("tau_filtre_d_s", tau_filtre_d_s)):
            if not math.isfinite(v) or v < 0:
                raise ValueError(f"{nom} doit être un nombre >= 0 (reçu {v!r})")
        if angle_max_deg <= 0 or ecart_max_deg <= 0:
            raise ValueError("angle_max_deg et ecart_max_deg doivent être > 0")
        if zone_integrale_deg is not None and not zone_integrale_deg > 0:
            raise ValueError("zone_integrale_deg doit être > 0, ou None (toujours intégrer)")
        self.kp, self.ki, self.kd = kp, ki, kd
        self.i_max_deg = i_max_deg
        self.angle_max_deg = angle_max_deg
        self.ecart_max_deg = ecart_max_deg
        self.kp_position = kp_position
        self.bande_morte_deg = bande_morte_deg
        self.tau_filtre_d_s = tau_filtre_d_s
        self.zone_integrale_deg = zone_integrale_deg
        self.integrale = 0.0          # en degrés de barre (déjà multipliée par ki)
        self.lacet_filtre = 0.0
        self._en_mouvement = False
        self.dernier = {}

    def calculer(self, e: EntreeRegulateur, dt: float) -> float:
        err = _borner(enrouler_180(e.consigne_deg - e.cap_deg), self.ecart_max_deg)
        if self.tau_filtre_d_s > 0:
            self.lacet_filtre += (e.taux_lacet_dps - self.lacet_filtre) * min(dt / self.tau_filtre_d_s, 1.0)
        else:
            self.lacet_filtre = e.taux_lacet_dps
        p = self.kp * err
        d = -self.kd * self.lacet_filtre
        brut = p + self.integrale + d
        sature = abs(brut) >= self.angle_max_deg and _signe(err) == _signe(brut)
        hors_zone = (self.zone_integrale_deg is not None
                     and abs(err) > self.zone_integrale_deg)
        if not sature and not hors_zone:               # anti-emballement
            self.integrale = _borner(self.integrale + self.ki * err * dt, self.i_max_deg)
        voulu = _borner(p + self.integrale + d, self.angle_max_deg)

        ecart = voulu - e.angle_barre_deg
        # hystérésis : on démarre au-delà de la bande morte, on s'arrête à sa moitié
        seuil = self.bande_morte_deg / 2 if self._en_mouvement else self.bande_morte_deg
        if abs(ecart) <= seuil:
            u, self._en_mouvement = 0.0, False
        else:
            u, self._en_mouvement = _borner(self.kp_position * ecart, 1.0), True
        self.dernier = {"erreur": err, "p": p, "i": self.integrale, "d": d,
                        "angle_voulu": voulu}
        return u


def _signe(x: float) -> int:
    return (x > 0) - (x < 0)


class _ServoPypilot:
    """Port de Servo.do_command (branche « période »), copié de simulations/pypilot_sim.py."""

    def __init__(self, periode=0.4, vmin=1.0, vmax=1.0):
        self.period, self.smin, self.smax = periode, vmin, vmax
        self.windup = 0.0
        self.windup_change = 0.0
        self.speed = 0.0

    def command(self, cmd, t, dt):
        speed = cmd
        if not speed:
            self.speed = 0.0
            return 0.0
        max_speed = self.smax
        min_speed = min(self.smin, max_speed)
        period = max(self.period, 2 * dt)
        self.windup += (speed - self.speed) * dt
        if abs(self.windup) > period * min_speed / 1.5:
            if abs(speed) < min_speed:
                speed = min_speed if self.windup > 0 else -min_speed
        else:
            speed = 0.0
        max_windup = 1.5 * period
        if abs(self.windup) > max_windup:
            self.windup = max_windup * _signe(self.windup)
        last_speed = self.speed
        if speed or last_speed:
            m = speed * last_speed
            if m <= 0:
                if t - self.windup_change < self.period:
                    if last_speed > 0:
                        speed = min_speed
                    elif last_speed < 0:
                        speed = -min_speed
                    else:
                        speed = 0.0
                else:
                    self.windup_change = t
                    if m < 0:
                        speed = 0.0
        speed = max(-max_speed, min(max_speed, speed))
        self.speed = speed
        return speed


class RegulateurPypilotBasic:
    type_ = "pypilot_basic"

    def __init__(self, P: float = 0.003, D: float = 0.09, DD: float = 0.075,
                 PR: float = 0.005, FF: float = 0.6, periode_s: float = 0.4,
                 vitesse_min: float = 1.0, vitesse_max: float = 1.0, filtres: bool = True):
        if not 0 < vitesse_max <= 1 or not 0 <= vitesse_min <= 1:
            raise ValueError("vitesse_min et vitesse_max entre 0 et 1")
        self.P, self.D, self.DD, self.PR, self.FF = P, D, DD, PR, FF
        self.filtres = filtres
        self.servo = _ServoPypilot(periode_s, vitesse_min, vitesse_max)
        self.t = 0.0
        self.cap_lp = None
        self.lacet_lp = self.acc_lp = 0.0
        self.lacet_prec = 0.0
        self.consigne_prec = None
        self.var_consigne = 0.0
        self.dernier = {}

    def calculer(self, e: EntreeRegulateur, dt: float) -> float:
        if self.cap_lp is None:
            self.cap_lp = e.cap_deg
            self.consigne_prec = e.consigne_deg
            self.lacet_prec = e.taux_lacet_dps
        acc_brute = (e.taux_lacet_dps - self.lacet_prec) / dt
        self.lacet_prec = e.taux_lacet_dps
        if self.filtres:                         # constantes de boatimu.py : .2 / .2 / .1
            self.cap_lp += 0.2 * enrouler_180(e.cap_deg - self.cap_lp)
            self.lacet_lp = 0.2 * e.taux_lacet_dps + 0.8 * self.lacet_lp
            self.acc_lp = 0.1 * acc_brute + 0.9 * self.acc_lp
        else:
            self.cap_lp, self.lacet_lp, self.acc_lp = e.cap_deg, e.taux_lacet_dps, acc_brute
        err = _borner(enrouler_180(self.cap_lp - e.consigne_deg), 30.0)   # signe de pypilot
        diff = -enrouler_180(e.consigne_deg - self.consigne_prec)
        self.var_consigne = 0.9 * self.var_consigne + 0.1 * diff
        self.consigne_prec = e.consigne_deg
        pr = math.sqrt(abs(err)) * _signe(err)
        cmd = (self.P * err + self.D * self.lacet_lp + self.DD * self.acc_lp
               + self.PR * pr + self.FF * self.var_consigne)
        vitesse = self.servo.command(cmd, self.t, dt)
        self.t += dt
        self.dernier = {"erreur": -err, "cmd_pypilot": cmd}
        return -vitesse                          # pypilot : positif fait BAISSER le cap


TYPES = {RegulateurPIDPosition.type_: RegulateurPIDPosition,
         RegulateurPypilotBasic.type_: RegulateurPypilotBasic}


def construire_regulateur(reglage: dict):
    """Crée un régulateur depuis un dictionnaire (une entrée de gains_pid.json).

    Les clés qui commencent par « _ » sont des commentaires. Une clé inconnue est
    une ERREUR (une faute de frappe ne doit pas passer en silence)."""
    params = {k: v for k, v in reglage.items() if not k.startswith("_")}
    type_ = params.pop("type", None)
    if type_ not in TYPES:
        raise ValueError(f"type inconnu {type_!r} ; possibles : {', '.join(TYPES)}")
    try:
        return TYPES[type_](**params)
    except TypeError as erreur:
        raise ValueError(f"réglage {type_} invalide : {erreur}") from None
