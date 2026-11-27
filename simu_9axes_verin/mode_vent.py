"""mode_vent.py : mode « vent apparent » (windvane électronique) du banc.

Ce que fait le mode : tenir un ANGLE DE VENT APPARENT choisi (par exemple 40°
tribord au près) au lieu d'un cap. Si le vent tourne, le bateau tourne avec lui.

Comment, en trois idées :
  1. On transforme l'angle de vent (relatif à l'étrave, très agité par le lacet)
     en DIRECTION DE VENT apparent dans le repère terrestre :
         direction = cap + angle
     Quand le bateau lacet, le cap et l'angle bougent en sens contraires et la
     direction reste calme : on peut la filtrer sans retarder la barre.
  2. On filtre cette direction (constante de temps `tau_s`).
  3. On en déduit une CONSIGNE DE CAP pour le régulateur de cap habituel :
         consigne_cap = direction_filtrée − angle_voulu
     Le PID et le gyroscope gardent donc l'amortissement du mode compas.

Sécurités (DEC-005) :
  - à l'engagement, le premier vent doit arriver dans `age_max_s` ; ensuite, un
    vent trop vieux (`age_max_s`) entraîne le retour au mode COMPAS sur la dernière
    consigne de cap, et alarme « vent perdu » (disposition 12). Le retour au mode
    vent n'est PAS automatique : il faut le redemander (proposition, à valider) ;
  - le mode ne fait jamais virer ni empanner (disposition 15) : une consigne
    d'angle à tribord garde le vent à tribord ; si le vent passe de l'autre bord,
    la barre ramène le bateau du côté voulu, elle ne change pas d'amure.

Corrections en option (disposition 14, « prévue plus tard » dans la
spécification d'anticipation ; essayée ici pour en mesurer l'intérêt) :
  - `corriger_gite`    : la girouette penchée ne voit que la part du vent
                         perpendiculaire au mât ; on divise la composante
                         latérale par cos(gîte) ;
  - `corriger_mouvement` : on retire la vitesse de la tête de mât due au roulis
                         et au tangage (gyroscope × hauteur du mât).

Amortissement assorti (`amortissement_capteur_s`). Trouvé au banc le 2026-11-26 :
la girouette amortit elle-même sa mesure ; son angle est donc EN RETARD sur le
mouvement du mât. Retirer le mouvement du mât de l'instant présent laisse une
erreur à chaque coup de roulis (au grand largue : 16° d'erreur moyenne au lieu de
3°). Le mode amortit donc la vitesse de tête de mât calculée comme la girouette
amortit sa mesure. La valeur est à relever sur la fiche du capteur ou à mesurer :
HYPOTHÈSE au banc, où on la connaît exactement. Un retard de transmission
supplémentaire (passerelle, liaison série) n'est pas modélisé.

Ce n'est PAS le mode vent de pypilot (qui a ses modes Wind et True Wind, non
portés ici). Stdlib seulement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from vent_sim import angle_et_vitesse, enrouler_180


class CorrecteurMat:
    """Corrige le vent mesuré en tête de mât de la gîte et du mouvement du mât.

    Partagé par le mode vent et l'anticipation par le vent. La vitesse de tête de
    mât (gyroscope × hauteur) est amortie comme la girouette amortit sa mesure."""

    def __init__(self, hauteur_mat_m: float = 8.5, amortissement_capteur_s: float = 0.3,
                 corriger_gite: bool = True, corriger_mouvement: bool = True):
        if hauteur_mat_m < 0 or amortissement_capteur_s < 0:
            raise ValueError("hauteur_mat_m et amortissement_capteur_s doivent être >= 0")
        self.hauteur_mat_m = hauteur_mat_m
        self.amortissement_capteur_s = amortissement_capteur_s
        self.corriger_gite = corriger_gite
        self.corriger_mouvement = corriger_mouvement
        self.v_mat = None

    def suivre(self, dt, vitesses_corps_dps):
        p, q = math.radians(vitesses_corps_dps[0]), math.radians(vitesses_corps_dps[1])
        v = (-q * self.hauteur_mat_m, p * self.hauteur_mat_m)
        if self.v_mat is None or self.amortissement_capteur_s == 0:
            self.v_mat = v
        else:
            k = min(dt / self.amortissement_capteur_s, 1.0)
            self.v_mat = tuple(a + (b - a) * k for a, b in zip(self.v_mat, v))

    def corriger(self, angle_deg, vitesse_ms, gite_deg, v_mat=None):
        """(angle, vitesse) corrigés. v_mat : vitesse de tête de mât à retirer (m/s,
        avant et tribord) ; par défaut, celle suivie par `suivre`."""
        if v_mat is None:
            v_mat = self.v_mat or (0.0, 0.0)
        a = math.radians(angle_deg)
        ux, uy = -vitesse_ms * math.cos(a), -vitesse_ms * math.sin(a)
        if self.corriger_mouvement:
            ux += v_mat[0]                     # on rajoute la vitesse du mât retirée par la mesure
            uy += v_mat[1]
        if self.corriger_gite:
            uy /= max(math.cos(math.radians(gite_deg)), 0.5)
        return angle_et_vitesse(ux, uy)


@dataclass(frozen=True)
class EtatModeVent:
    mode: str                  # "vent" ou "compas_secours"
    consigne_cap_deg: float
    angle_mesure_deg: float | None    # angle utilisé (corrigé si demandé)
    direction_filtree_deg: float | None
    alarme_vent_perdu: bool


class ModeVent:
    def __init__(self, angle_voulu_deg: float, tau_s: float = 3.0, age_max_s: float = 2.0,
                 corriger_gite: bool = True, corriger_mouvement: bool = True,
                 hauteur_mat_m: float = 8.5, amortissement_capteur_s: float = 0.3):
        if not -180.0 < angle_voulu_deg <= 180.0 or angle_voulu_deg == 0.0:
            raise ValueError("angle voulu entre -180 et 180, non nul (bâbord négatif)")
        if tau_s < 0 or age_max_s <= 0 or hauteur_mat_m < 0 or amortissement_capteur_s < 0:
            raise ValueError("tau_s >= 0, age_max_s > 0, hauteur_mat_m >= 0")
        self.angle_voulu_deg = angle_voulu_deg
        self.tau_s = tau_s
        self.age_max_s = age_max_s
        self.correcteur = CorrecteurMat(hauteur_mat_m, amortissement_capteur_s,
                                        corriger_gite, corriger_mouvement)
        self._t_mesure_traitee = None
        self.mode = "vent"
        self.direction = None             # direction filtrée (degrés, déroulée)
        self.consigne_cap = None
        self.alarme_vent_perdu = False
        self._t_engagement = None

    def changer_angle(self, angle_voulu_deg: float) -> None:
        """Nouvel angle voulu, même bord (changer de bord = virer ou empanner : jamais ici)."""
        if (angle_voulu_deg > 0) != (self.angle_voulu_deg > 0):
            raise ValueError("changement de bord refusé : le mode vent ne vire ni n'empanne")
        self.angle_voulu_deg = angle_voulu_deg

    def corriger(self, angle_deg: float, vitesse_ms: float, gite_deg: float,
                 v_mat=(0.0, 0.0)) -> float:
        """Angle corrigé. v_mat : vitesse de tête de mât (m/s, avant et tribord) à retirer."""
        return self.correcteur.corriger(angle_deg, vitesse_ms, gite_deg, v_mat)[0]

    def mettre_a_jour(self, t: float, dt: float, cap_deg: float, mesure, gite_deg: float = 0.0,
                      vitesses_corps_dps=(0.0, 0.0, 0.0)) -> EtatModeVent:
        """mesure : MesureVent valide (de RecepteurVent.vent_valide) ou None."""
        angle = None
        if self._t_engagement is None:
            self._t_engagement = t
        self.correcteur.suivre(dt, vitesses_corps_dps)
        if self.mode == "vent":
            if (mesure is None or (t - mesure.t) > self.age_max_s) and self.direction is None \
                    and t - self._t_engagement <= self.age_max_s:
                # vient d'être engagé, premier vent pas encore reçu : on tient le cap
                if self.consigne_cap is None:
                    self.consigne_cap = cap_deg
            elif mesure is None or (t - mesure.t) > self.age_max_s:
                if self.consigne_cap is None:
                    self.consigne_cap = cap_deg   # jamais eu de vent : on tient le cap actuel
                self.mode = "compas_secours"
                self.alarme_vent_perdu = True
            elif mesure.t != self._t_mesure_traitee:      # une mesure NEUVE : on l'intègre
                angle = self.correcteur.corriger(mesure.angle_deg, mesure.vitesse_ms, gite_deg)[0]
                brute = cap_deg + angle
                if self.direction is None:
                    self.direction = brute
                else:
                    dt_m = mesure.t - self._t_mesure_traitee
                    ecart = enrouler_180(brute - self.direction)
                    k = 1.0 if self.tau_s == 0 else min(dt_m / self.tau_s, 1.0)
                    self.direction += ecart * k
                self._t_mesure_traitee = mesure.t
                self.consigne_cap = (self.direction - self.angle_voulu_deg) % 360.0
        return EtatModeVent(self.mode, self.consigne_cap, angle,
                            None if self.direction is None else self.direction % 360.0,
                            self.alarme_vent_perdu)

    def reengager(self) -> None:
        """Demande explicite de revenir au mode vent après un secours."""
        self.mode = "vent"
        self.alarme_vent_perdu = False
        self.direction = None
        self._t_engagement = None
        self._t_mesure_traitee = None
