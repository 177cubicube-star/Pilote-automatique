"""anticipation_vent.py : anticipation de la barre par le vent (CON-009), apprise sur 10 minutes.

L'idée, en clair
----------------
Quand le vent forcit, le bateau gîte davantage et cherche à remonter au vent. Le
régulateur de cap ne le corrige qu'APRÈS l'écart. Or, en régime établi, le pilote
tient un angle de barre qui dépend du vent : c'est la « barre habituelle » pour ce
vent. Le script l'apprend en continu, puis, dès que le vent change, il calcule la
barre qu'il faudra tenir et prépare la différence.

  1. Vent filtré sur 1 s (CON-009). Mesure du vent : angle et vitesse apparents,
     CORRIGÉS de la gîte et du mouvement du mât par l'appelant (`CorrecteurMat`).
     Écart à CON-009, qui prévoyait cette correction « plus tard » : au banc, sans
     elle, la vitesse du vent saute à chaque coup de roulis et le modèle n'apprend
     rien (2026-11-26).
  2. Apprentissage : une fois par seconde, si le bateau est en régime établi
     (lacet, écart de cap et variation du vent faibles), on garde le point
     (angle de barre mesuré, vitesse² du vent) dans la tranche d'angle de vent
     courante. Les points de plus de 10 minutes sont oubliés.
  3. Modèle par tranche d'angle du vent DE BASE (moyenne lente) : une bascule
     passagère ne fait pas changer de modèle. Moindres carrés :
         barre_habituelle = a + b × vitesse² [+ c × vitesse² × (angle − angle moyen)]
     (b joue le rôle de k_air × Cn(angle) × gain de la formule de Fenix ; le terme
     en c, option `modele_angle`, apprend l'effet de l'angle à partir des
     oscillations naturelles du vent dans la fenêtre, s'il a assez varié).
     Pas de modèle tant qu'il manque des points ou de la variation de vent.
  4. Correction : on compare le vent présent au vent « de base » (moyenne lente
     sur 60 s) et on prépare l'écart de barre correspondant :
         correction = barre(vent présent) − barre(vent de base),  bornée à ±10°.
     Le terme intégral du régulateur tient la partie lente ; l'anticipation ne
     porte que sur le changement.

Garde-fous (CON-009, actifs même en mode fantôme) : vent trop vieux, valeur hors
plage, saut brutal, vent trop faible (hystérésis 0,6/0,4 m/s), modèle
insuffisant, veille → correction à 0 avec le motif.

MODE FANTÔME : ce module CALCULE. Il n'envoie rien. C'est l'appelant qui décide
d'appliquer ou non la correction ; au banc, une variante « active » existe pour
mesurer le gain possible, dans le simulateur seulement (pas la version 2 de
CON-009, qui demande la décision explicite de Mathieu).

Stdlib seulement.
"""
from __future__ import annotations

import csv
import json
import math
from collections import deque
from dataclasses import dataclass, fields

COLONNES_JOURNAL = (
    "t", "age_vent_s", "angle_brut_deg", "vitesse_brute_ms", "angle_filtre_deg",
    "vitesse_filtree_ms", "cap_deg", "engage", "angle_barre_mesure_deg", "tranche",
    "points", "pente", "ordonnee", "pente_angle", "vitesse2_presente", "vitesse2_base",
    "barre_prevue_deg", "correction_deg", "etat", "motif")


@dataclass(frozen=True)
class ConfigAnticipation:
    """Toutes les constantes viennent du fichier JSON (pas de valeur par défaut ici)."""
    fenetre_s: float
    periode_echantillon_s: float
    filtre_vent_s: float
    base_lente_s: float
    largeur_tranche_deg: float
    points_min: int
    ecart_type_min_x: float
    regime_lacet_max_dps: float
    regime_ecart_cap_max_deg: float
    regime_variation_vent_max_ms2: float
    borne_deg: float
    seuil_marche_ms: float
    seuil_arret_ms: float
    age_max_s: float
    vitesse_max_plausible_ms: float
    saut_max_ms: float
    modele_angle: bool
    ecart_type_min_angle_deg: float

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, bool):
                continue
            if not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ValueError(f"{f.name} doit être un nombre >= 0 (reçu {v!r})")
        if self.seuil_arret_ms > self.seuil_marche_ms:
            raise ValueError("seuil_arret_ms doit être <= seuil_marche_ms")
        if self.largeur_tranche_deg <= 0 or self.periode_echantillon_s <= 0 or self.fenetre_s <= 0:
            raise ValueError("largeur de tranche, période et fenêtre doivent être > 0")


def charger_config(chemin: str, **remplacements) -> ConfigAnticipation:
    with open(chemin, encoding="utf-8") as f:
        brut = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    brut.update(remplacements)
    noms = {f.name for f in fields(ConfigAnticipation)}
    inconnus = set(brut) - noms
    manquants = noms - set(brut)
    if inconnus or manquants:
        raise ValueError(f"configuration : inconnus {sorted(inconnus)}, manquants {sorted(manquants)}")
    return ConfigAnticipation(**brut)


@dataclass(frozen=True)
class EtatAnticipation:
    correction_deg: float       # 0 si coupée
    barre_prevue_deg: float     # barre habituelle prévue pour le vent présent (nan sans modèle)
    etat: str                   # "calculee", "coupee"
    motif: str                  # "" ou la raison de la coupure
    tranche: int | None
    points: int
    pente: float


class AnticipationVent:
    def __init__(self, cfg: ConfigAnticipation, chemin_journal: str | None = None):
        self.cfg = cfg
        self.points = {}                # tranche -> deque de (t, x = vitesse², barre, angle)
        self._cache = {}                # tranche -> modèle, vidé à chaque nouvel échantillon
        self.angle_f = self.vitesse_f = None
        self.x_base = None
        self.angle_base = None          # angle du vent de base : choisit la tranche du modèle
        self._t_echantillon = None
        self._vitesse_prec = None
        self._marche = False
        self._fichier = None
        self._journal = None
        if chemin_journal:
            self._fichier = open(chemin_journal, "w", newline="", encoding="utf-8")
            self._journal = csv.writer(self._fichier)
            self._journal.writerow(COLONNES_JOURNAL)

    # ------------------------------------------------------------ modèle
    def tranche(self, angle_deg: float) -> int:
        return int(math.floor(angle_deg / self.cfg.largeur_tranche_deg))

    def modele(self, tranche: int):
        """(ordonnée a, pente b, nombre de points) ou None si non identifiable."""
        if tranche not in self._cache:
            self._cache[tranche] = self._calculer_modele(tranche)
        return self._cache[tranche]

    def _calculer_modele(self, tranche: int):
        """Modèle (a, b, n, c, angle_ref) : barre = a + b·x + c·x·(angle − angle_ref).
        c = 0 si `modele_angle` est faux ou si l'angle n'a pas assez varié."""
        pts = self.points.get(tranche)
        if not pts or len(pts) < self.cfg.points_min:
            return None
        n = len(pts)
        mx = sum(p[1] for p in pts) / n
        my = sum(p[2] for p in pts) / n
        sxx = sum((p[1] - mx) ** 2 for p in pts)
        if math.sqrt(sxx / n) < self.cfg.ecart_type_min_x:
            return None
        ma = sum(p[3] for p in pts) / n
        ecart_angle = math.sqrt(sum((p[3] - ma) ** 2 for p in pts) / n)
        if self.cfg.modele_angle and ecart_angle >= self.cfg.ecart_type_min_angle_deg:
            z = [p[1] * (p[3] - ma) for p in pts]          # second régresseur : x · écart d'angle
            mz = sum(z) / n
            szz = sum((zi - mz) ** 2 for zi in z)
            sxz = sum((p[1] - mx) * (zi - mz) for p, zi in zip(pts, z))
            sxy = sum((p[1] - mx) * (p[2] - my) for p in pts)
            szy = sum((zi - mz) * (p[2] - my) for p, zi in zip(pts, z))
            det = sxx * szz - sxz * sxz
            if det > 1e-9 * sxx * szz:
                b = (sxy * szz - szy * sxz) / det
                cc = (szy * sxx - sxy * sxz) / det
                return my - b * mx - cc * mz, b, n, cc, ma
        b = sum((p[1] - mx) * (p[2] - my) for p in pts) / sxx
        return my - b * mx, b, n, 0.0, ma

    @staticmethod
    def _barre(mod, x, angle):
        a, b, _n, cc, ma = mod
        return a + b * x + cc * x * (angle - ma)

    def _apprendre(self, t, tranche, x, barre, angle):
        d = self.points.setdefault(tranche, deque())
        d.append((t, x, barre, angle))

    def _oublier(self, t):
        for d in self.points.values():
            while d and d[0][0] < t - self.cfg.fenetre_s:
                d.popleft()

    # ------------------------------------------------------------- un pas
    def mettre_a_jour(self, t: float, dt: float, mesure, angle_barre_deg: float,
                      taux_lacet_dps: float, ecart_cap_deg: float, cap_deg: float,
                      engage: bool = True) -> EtatAnticipation:
        c = self.cfg
        motif, age = "", float("nan")
        brut_a = brut_v = float("nan")
        if mesure is None:
            motif = "vent_absent"
        else:
            age = t - mesure.t
            brut_a, brut_v = mesure.angle_deg, mesure.vitesse_ms
            if age > c.age_max_s:
                motif = "vent_trop_vieux"
            elif not (math.isfinite(brut_v) and 0 <= brut_v <= c.vitesse_max_plausible_ms
                      and -180.0 <= brut_a <= 180.0):
                motif = "hors_plage"
            elif self.vitesse_f is not None and abs(brut_v - self.vitesse_f) > c.saut_max_ms:
                motif = "saut_brutal"

        if not motif:                      # filtre de 1 s (sur le vecteur, pour l'angle)
            k = 1.0 if self.vitesse_f is None or c.filtre_vent_s == 0 else min(dt / c.filtre_vent_s, 1.0)
            a = math.radians(brut_a)
            if self.vitesse_f is None:
                ux, uy = math.cos(a) * brut_v, math.sin(a) * brut_v
            else:
                fa = math.radians(self.angle_f)
                ux = self.vitesse_f * math.cos(fa) + (brut_v * math.cos(a) - self.vitesse_f * math.cos(fa)) * k
                uy = self.vitesse_f * math.sin(fa) + (brut_v * math.sin(a) - self.vitesse_f * math.sin(fa)) * k
            self.vitesse_f = math.hypot(ux, uy)
            self.angle_f = math.degrees(math.atan2(uy, ux))

        x = None if self.vitesse_f is None else self.vitesse_f ** 2
        if x is not None and not motif:
            kb = min(dt / c.base_lente_s, 1.0) if c.base_lente_s > 0 else 1.0
            self.x_base = x if self.x_base is None else self.x_base + (x - self.x_base) * kb
            self.angle_base = (self.angle_f if self.angle_base is None else
                               self.angle_base + ((self.angle_f - self.angle_base + 180) % 360 - 180) * kb)

        # hystérésis de mise en marche sur la vitesse du vent
        if self.vitesse_f is not None and not motif:
            if self._marche and self.vitesse_f < c.seuil_arret_ms:
                self._marche = False
            elif not self._marche and self.vitesse_f >= c.seuil_marche_ms:
                self._marche = True

        # apprentissage, une fois par période, en régime établi seulement ; la tranche est
        # celle du vent de BASE : une bascule passagère ne fait pas sortir du modèle appris
        tr = None if self.angle_base is None else self.tranche(self.angle_base)
        if self._t_echantillon is None or t - self._t_echantillon >= c.periode_echantillon_s:
            if not motif and tr is not None and engage:
                variation = (0.0 if self._vitesse_prec is None or self._t_echantillon is None
                             else abs(self.vitesse_f - self._vitesse_prec) / (t - self._t_echantillon))
                if (abs(taux_lacet_dps) <= c.regime_lacet_max_dps
                        and abs(ecart_cap_deg) <= c.regime_ecart_cap_max_deg
                        and variation <= c.regime_variation_vent_max_ms2):
                    self._apprendre(t, tr, x, angle_barre_deg, self.angle_f)
            self._vitesse_prec = self.vitesse_f
            self._t_echantillon = t
            self._oublier(t)
            self._cache.clear()

        mod = self.modele(tr) if tr is not None else None
        barre_prevue = (float("nan") if mod is None or x is None
                        else self._barre(mod, x, self.angle_f))
        correction = 0.0
        if not motif:
            if not self._marche:
                motif = "vent_faible"
            elif mod is None:
                motif = "modele_insuffisant"
            elif not engage:
                motif = "veille"
            else:
                brute = barre_prevue - self._barre(mod, self.x_base, self.angle_base)
                correction = max(-c.borne_deg, min(c.borne_deg, brute))
        etat = EtatAnticipation(correction, barre_prevue, "calculee" if not motif else "coupee",
                                motif, tr, 0 if mod is None else mod[2],
                                float("nan") if mod is None else mod[1])
        if self._journal:
            self._journal.writerow([
                f"{t:.2f}", f"{age:.2f}", f"{brut_a:.1f}", f"{brut_v:.2f}",
                "" if self.angle_f is None else f"{self.angle_f:.1f}",
                "" if self.vitesse_f is None else f"{self.vitesse_f:.2f}", f"{cap_deg:.1f}",
                int(engage), f"{angle_barre_deg:.2f}", "" if tr is None else tr, etat.points,
                "" if mod is None else f"{mod[1]:.4f}", "" if mod is None else f"{mod[0]:.3f}",
                "" if mod is None else f"{mod[3]:.5f}",
                "" if x is None else f"{x:.2f}", "" if self.x_base is None else f"{self.x_base:.2f}",
                "" if math.isnan(barre_prevue) else f"{barre_prevue:.2f}", f"{correction:.3f}",
                etat.etat, motif])
        return etat

    def fermer(self):
        if self._fichier:
            self._fichier.close()
            self._fichier = None
