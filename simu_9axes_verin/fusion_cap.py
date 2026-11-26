"""fusion_cap.py : estimation du cap, de la gîte et du tangage à partir des 9 axes.

Deux filtres, même interface (`mettre_a_jour(mesure, dt, reference)`) :
  - FusionCap     : filtre complémentaire simple, sur les angles (ci-dessous) ;
  - FusionMahony  : filtre de Mahony, sur un quaternion (voir sa classe).
Les deux acceptent une RÉFÉRENCE DE GÎTE externe (`ReferenceGite`) qui remplace
l'accéléromètre de la centrale comme référence de verticale.

Le filtre complémentaire : un filtre COMPLÉMENTAIRE simple, pour que le banc ait un cap
« estimé » réaliste (bruité, en retard, sensible aux défauts du magnétomètre)
à donner aux régulateurs. Ce n'est PAS la fusion de pypilot (qui a la sienne,
non portée ici) : les chiffres de précision obtenus avec ce filtre ne disent
rien de la précision qu'aura pypilot.

Principe, en trois idées :
  - le gyroscope est précis à court terme mais dérive : on l'INTÈGRE ;
  - l'accéléromètre donne la verticale (gîte, tangage) et le magnétomètre le
    nord : justes en moyenne, bruités et perturbés à court terme ;
  - on corrige doucement l'intégration du gyroscope vers ces références, avec
    une constante de temps (tau) : grand tau = cap lisse mais lent à se corriger.
Un terme intégral estime en plus le biais du gyroscope en lacet.

Repère corps : x avant, y tribord, z bas. Cap : 0 = nord magnétique, 90 = est.
Gîte positive = bateau penché sur tribord. Stdlib seulement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from icm20948_lecteur import MesureIMU
from icm20948_sim import G


def enrouler_180(a: float) -> float:
    """Ramène un angle (°) dans [-180, 180)."""
    return (a + 180.0) % 360.0 - 180.0


def inclinaison_par_accel(f):
    """Gîte et tangage (rad) depuis la force spécifique mesurée (repère corps)."""
    fx, fy, fz = f
    gite = math.atan2(-fy, -fz)
    tangage = math.atan2(fx, math.hypot(fy, fz))
    return gite, tangage


def cap_compense(m, gite: float, tangage: float) -> float:
    """Cap magnétique (rad) compensé de la gîte et du tangage."""
    mx, my, mz = m
    sg, cg = math.sin(gite), math.cos(gite)
    st, ct = math.sin(tangage), math.cos(tangage)
    xh = mx * ct + my * sg * st + mz * cg * st
    yh = my * cg - mz * sg
    return math.atan2(-yh, xh)


@dataclass(frozen=True)
class EstimationCap:
    cap_deg: float            # [0, 360)
    taux_lacet_dps: float     # vitesse de variation du cap, biais estimé retiré
    gite_deg: float
    tangage_deg: float


@dataclass(frozen=True)
class ReferenceGite:
    """Gîte et tangage fournis par une autre source que l'accéléromètre de la centrale.

    exacte = True : la valeur est prise telle quelle (sert à la « gîte parfaite »,
                    borne haute du gain possible) ;
    exacte = False : elle remplace l'accéléromètre comme référence lente.
    force : force spécifique mesurée par cette source (m/s², repère corps), si elle
            en a une ; le filtre de Mahony s'en sert pour juger de sa fiabilité."""
    gite_rad: float
    tangage_rad: float
    exacte: bool = False
    force: tuple | None = None


def _ref_angles(m: MesureIMU, reference: ReferenceGite | None):
    if reference is None:
        return inclinaison_par_accel(m.accel_ms2)
    return reference.gite_rad, reference.tangage_rad


class FusionCap:
    nom = "complementaire"

    def __init__(self, tau_cap_s: float = 3.0, tau_inclinaison_s: float = 2.0,
                 ki_biais: float = 0.01, declinaison_deg: float = 0.0):
        if tau_cap_s <= 0 or tau_inclinaison_s <= 0 or ki_biais < 0:
            raise ValueError("constantes de temps > 0 et ki_biais >= 0")
        self.tau_cap_s = tau_cap_s
        self.tau_inclinaison_s = tau_inclinaison_s
        self.ki_biais = ki_biais
        self.declinaison_deg = declinaison_deg
        self.initialisee = False
        self.gite = self.tangage = self.cap = 0.0      # radians
        self.biais_lacet = 0.0                         # rad/s
        self.taux_lacet = 0.0                          # rad/s

    def mettre_a_jour(self, m: MesureIMU, dt: float,
                      reference: ReferenceGite | None = None) -> EstimationCap | None:
        """Retourne None tant que la première mesure magnétique n'est pas arrivée."""
        g_acc, t_acc = _ref_angles(m, reference)
        if not self.initialisee:
            if m.mag_ut is None:
                return None
            self.gite, self.tangage = g_acc, t_acc
            self.cap = cap_compense(m.mag_ut, g_acc, t_acc)
            self.initialisee = True
            return self._estimation()

        p, q, r = (math.radians(w) for w in m.gyro_dps)
        sg, cg = math.sin(self.gite), math.cos(self.gite)
        ct = max(math.cos(self.tangage), 1e-3)
        d_gite = p + (q * sg + r * cg) * math.tan(self.tangage)
        d_tangage = q * cg - r * sg
        d_cap = (q * sg + r * cg) / ct - self.biais_lacet

        if reference is not None and reference.exacte:
            self.gite, self.tangage = g_acc, t_acc
        else:
            a_incl = min(dt / self.tau_inclinaison_s, 1.0)
            self.gite += d_gite * dt + (g_acc - self.gite) * a_incl
            self.tangage += d_tangage * dt + (t_acc - self.tangage) * a_incl

        self.cap += d_cap * dt
        if m.mag_ut is not None:
            ecart = math.radians(enrouler_180(math.degrees(
                cap_compense(m.mag_ut, self.gite, self.tangage) - self.cap)))
            self.cap += ecart * min(dt / self.tau_cap_s, 1.0)
            self.biais_lacet -= self.ki_biais * ecart * dt
        self.taux_lacet = d_cap
        return self._estimation()

    def _estimation(self) -> EstimationCap:
        cap = (math.degrees(self.cap) + self.declinaison_deg) % 360.0
        return EstimationCap(cap, math.degrees(self.taux_lacet),
                             math.degrees(self.gite), math.degrees(self.tangage))


# ============================================================== Mahony
def _q_mult(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def _q_norm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q)


def _q_euler(q):
    """Quaternion (corps -> terre) vers gîte, tangage, cap (rad), ordre cap-tangage-gîte."""
    w, x, y, z = q
    gite = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    tangage = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    cap = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return gite, tangage, cap


def _euler_q(gite, tangage, cap):
    cg, sg = math.cos(gite / 2), math.sin(gite / 2)
    ct, st = math.cos(tangage / 2), math.sin(tangage / 2)
    cc, sc = math.cos(cap / 2), math.sin(cap / 2)
    return (cc * ct * cg + sc * st * sg,
            cc * ct * sg - sc * st * cg,
            cc * st * cg + sc * ct * sg,
            sc * ct * cg - cc * st * sg)


def _troisieme_ligne(q):
    """3e ligne de la matrice corps -> terre = axe « bas » terrestre vu du corps."""
    w, x, y, z = q
    return (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y))


def _vectoriel(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


ZONE_BIAIS_RAD = math.radians(5.0)   # n'apprendre le biais que sur de petits écarts


class FusionMahony:
    """Filtre de Mahony (R. Mahony et al., 2008), sur un quaternion.

    L'idée, en clair : on fait tourner une orientation estimée avec le gyroscope,
    puis on la « tire » doucement vers ce que disent l'accéléromètre (le bas) et
    le magnétomètre (le nord). L'écart entre le bas mesuré et le bas estimé est
    un produit vectoriel : il dit directement autour de quel axe tourner pour se
    corriger. Une part intégrale (ki) accumule cet écart : c'est l'estimation du
    BIAIS du gyroscope, sur les trois axes (le filtre complémentaire ne l'estime
    qu'en lacet).

    Ajouts pour un bateau secoué, chacun débrayable :
      - pondération : moins on croit l'accéléromètre que la norme de la force
        mesurée s'écarte de 1 g (la vague accélère le bateau) ;
      - le biais n'est appris que sur de petits écarts (< 5°) : après une grosse
        erreur (démarrage, choc), l'intégrale ne se « charge » pas ;
      - compensation centripète : en virage, l'accéléromètre sent v·r vers
        l'intérieur ; connaissant la vitesse (GPS), on la retire ;
      - le magnétomètre ne corrige QUE le cap, autour de l'axe vertical, pour ne
        pas fausser la gîte quand le champ est perturbé.

    Gains par défaut : kp_acc = 0,25 (≈ 4 s) est le meilleur compromis trouvé au
    banc SIMULÉ du 2026-11-26 (balayage de 0,05 à 2) ; il dépend des
    accélérations et de la dérive du gyroscope supposées. À revoir sur données réelles.
    """
    nom = "mahony"

    def __init__(self, kp_acc: float = 0.25, ki_acc: float = 0.01,
                 kp_mag: float = 0.3, ki_mag: float = 0.005,
                 seuil_ponderation_g: float = 0.1, vitesse_ms: float | None = None,
                 declinaison_deg: float = 0.0):
        for nom_, v in (("kp_acc", kp_acc), ("ki_acc", ki_acc), ("kp_mag", kp_mag),
                        ("ki_mag", ki_mag)):
            if not math.isfinite(v) or v < 0:
                raise ValueError(f"{nom_} doit être >= 0")
        if seuil_ponderation_g < 0:
            raise ValueError("seuil_ponderation_g doit être >= 0 (0 = pas de pondération)")
        self.kp_acc, self.ki_acc = kp_acc, ki_acc
        self.kp_mag, self.ki_mag = kp_mag, ki_mag
        self.seuil_ponderation_g = seuil_ponderation_g
        self.vitesse_ms = vitesse_ms
        self.declinaison_deg = declinaison_deg
        self.q = (1.0, 0.0, 0.0, 0.0)
        self.biais = [0.0, 0.0, 0.0]          # rad/s, repère corps
        self.initialisee = False
        self.taux_lacet = 0.0
        self.poids_acc = 1.0                  # dernier poids donné à la verticale mesurée

    def _verticale_mesuree(self, m: MesureIMU, reference, d_cap_rad):
        """Direction de la force spécifique mesurée, et son poids (0 à 1)."""
        if reference is not None and reference.force is None:
            g, t = reference.gite_rad, reference.tangage_rad    # source sans force : angles
            return (math.sin(t), -math.sin(g) * math.cos(t), -math.cos(g) * math.cos(t)), 1.0
        f = list(reference.force if reference is not None else m.accel_ms2)
        if self.vitesse_ms is not None:
            f[1] -= self.vitesse_ms * d_cap_rad
        n = math.sqrt(f[0] ** 2 + f[1] ** 2 + f[2] ** 2)
        if n < 1e-6:
            return (0.0, 0.0, -1.0), 0.0
        poids = 1.0
        if self.seuil_ponderation_g > 0:
            poids = max(0.0, 1.0 - abs(n - G) / (self.seuil_ponderation_g * G))
        return (f[0] / n, f[1] / n, f[2] / n), poids

    def mettre_a_jour(self, m: MesureIMU, dt: float,
                      reference: ReferenceGite | None = None) -> EstimationCap | None:
        if not self.initialisee:
            if m.mag_ut is None:
                return None
            g, t = _ref_angles(m, reference)
            self.q = _euler_q(g, t, cap_compense(m.mag_ut, g, t))
            self.initialisee = True
            return self._estimation()

        w = [math.radians(v) - b for v, b in zip(m.gyro_dps, self.biais)]
        correction = [0.0, 0.0, 0.0]

        if not (reference is not None and reference.exacte):
            g0, t0, _ = _q_euler(self.q)          # vitesse de variation du CAP (pas r du corps)
            d_cap = (w[1] * math.sin(g0) + w[2] * math.cos(g0)) / max(math.cos(t0), 1e-3)
            v_mes, poids = self._verticale_mesuree(m, reference, d_cap)
            self.poids_acc = poids
            bas = _troisieme_ligne(self.q)
            v_est = (-bas[0], -bas[1], -bas[2])                 # force attendue au repos
            e = _vectoriel(v_mes, v_est)
            apprendre = math.sqrt(e[0] ** 2 + e[1] ** 2 + e[2] ** 2) < ZONE_BIAIS_RAD
            for k in range(3):
                correction[k] += self.kp_acc * poids * e[k]
                if apprendre:
                    self.biais[k] -= self.ki_acc * poids * e[k] * dt

        if m.mag_ut is not None:
            g, t, c = _q_euler(self.q)
            ecart = math.radians(enrouler_180(math.degrees(cap_compense(m.mag_ut, g, t) - c)))
            bas = _troisieme_ligne(self.q)                      # tourner autour de la verticale
            for k in range(3):
                correction[k] += self.kp_mag * ecart * bas[k]
                if abs(ecart) < ZONE_BIAIS_RAD:
                    self.biais[k] -= self.ki_mag * ecart * bas[k] * dt

        omega = [w[k] + correction[k] for k in range(3)]
        dq = _q_mult(self.q, (0.0, omega[0], omega[1], omega[2]))
        self.q = _q_norm(tuple(self.q[k] + 0.5 * dq[k] * dt for k in range(4)))

        g, t, c = _q_euler(self.q)
        if reference is not None and reference.exacte:          # gîte imposée, cap gardé
            g, t = reference.gite_rad, reference.tangage_rad
            self.q = _euler_q(g, t, c)
        self.taux_lacet = (w[1] * math.sin(g) + w[2] * math.cos(g)) / max(math.cos(t), 1e-3)
        return self._estimation()

    def _estimation(self) -> EstimationCap:
        g, t, c = _q_euler(self.q)
        return EstimationCap((math.degrees(c) + self.declinaison_deg) % 360.0,
                             math.degrees(self.taux_lacet), math.degrees(g), math.degrees(t))


FUSIONS = {FusionCap.nom: FusionCap, FusionMahony.nom: FusionMahony}


def construire_fusion(nom: str = "complementaire", **params):
    if nom not in FUSIONS:
        raise ValueError(f"fusion inconnue {nom!r} ; possibles : {', '.join(FUSIONS)}")
    try:
        return FUSIONS[nom](**params)
    except TypeError as erreur:
        raise ValueError(f"paramètres de fusion {nom} invalides : {erreur}") from None
