"""bateau_sim.py : bateau simulé (lacet, gîte, tangage) et perturbations.

Modèle de lacet de NOMOTO du premier ordre : le bateau répond à l'angle de
barre avec un gain K (vitesse de rotation obtenue par degré de barre) et un
retard T (temps pour prendre cette vitesse).

    T · dr/dt + r = K · (angle_barre + perturbation)      r = vitesse de lacet

VALEURS PAR DÉFAUT = HYPOTHÈSES : T = 2,26 s et K = 0,19 /s sont celles du
bateau de 12 m des simulations du 2026-10-28 (dossier `simulations/`), PAS le
Catalina Capri 22. Elles sont gardées pour que les résultats restent
comparables. À remplacer par des valeurs identifiées sur le Capri 22 (essai de
virage à barre fixe, saison prochaine).

Gîte et tangage : oscillateurs amortis du second ordre poussés par le vent et
les vagues. Accélérations vues par la centrale : virage (v·r), pilonnement et
embardée des vagues (dans le repère TERRESTRE), et bras de levier (la centrale
est au-dessus du centre de rotation, le roulis la balance). Ce sont elles qui
trompent l'accéléromètre sur la verticale. La gîte agit sur le cap via `k_gite_lacet` : c'est la tendance d'un
voilier gîté à remonter au vent (piste B du concept d'anticipation).

Conventions : cap en degrés, 0 = nord, croît vers l'est (tribord).
Angle de barre positif = le bateau vire sur TRIBORD (le cap augmente).
Gîte positive = penché sur tribord. Repère corps : x avant, y tribord, z bas.
Stdlib seulement.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

G = 9.80665


@dataclass(frozen=True)
class ConfigBateau:
    T_s: float = 2.26                  # HYPOTHÈSE (bateau 12 m des simulations 2026-10-28)
    K_par_s: float = 0.19              # HYPOTHÈSE
    vitesse_ms: float = 2.5            # ≈ 4,9 nœuds, pour l'accélération centripète
    periode_roulis_s: float = 3.0      # HYPOTHÈSE
    amortissement_roulis: float = 0.5   # HYPOTHÈSE ; 0,15 jusqu'au 2026-11-26 : le roulis entrait en
                                        # résonance avec les vagues (±29° dans « vagues ») ; à mesurer à bord
    periode_tangage_s: float = 2.0     # HYPOTHÈSE
    amortissement_tangage: float = 0.25
    champ_total_ut: float = 53.0       # ordre de grandeur pour le sud du Québec, à vérifier (modèle WMM)
    inclinaison_mag_deg: float = 69.0  # idem
    position_imu_m: tuple = (0.0, 0.0, -0.3)   # HYPOTHÈSE : centrale 0,3 m AU-DESSUS du centre de
                                               # rotation (x avant, y tribord, z bas)


@dataclass(frozen=True)
class Rafale:
    debut_s: float
    duree_s: float
    gite_deg: float                    # gîte AJOUTÉE au plus fort de la rafale
    montee_s: float = 2.0


@dataclass(frozen=True)
class ConfigPerturbations:
    barre_ardente_deg: float = 0.0     # déséquilibre constant, en degrés de barre équivalents
    gite_base_deg: float = 0.0
    k_gite_lacet: float = 0.0          # degrés de barre équivalents par degré de gîte ;
                                       # k > 0 : le bateau gîté remonte au vent (gîte sur
                                       # tribord = vent de bâbord = il vire vers bâbord)
    rafales: tuple = ()
    vagues_lacet_deg: float = 0.0      # amplitude caractéristique, en degrés de barre équivalents
    vagues_roulis_deg: float = 0.0
    vagues_tangage_deg: float = 0.0
    vagues_pilonnement_ms2: float = 0.0   # accélération verticale (verticale TERRESTRE)
    vagues_embardee_ms2: float = 0.0      # accélération latérale (horizontale terrestre, travers)
    periode_vagues_s: float = 3.0
    composantes: int = 5


class _Houle:
    """Somme de sinusoïdes de périodes et phases tirées au hasard (graine fixe)."""

    def __init__(self, amplitude: float, periode: float, n: int, rng: random.Random):
        self.termes = []
        if amplitude == 0 or n <= 0:
            return
        a = amplitude / math.sqrt(n)
        for _ in range(n):
            w = 2 * math.pi / (periode * rng.uniform(0.7, 1.3))
            self.termes.append((a, w, rng.uniform(0, 2 * math.pi)))

    def __call__(self, t: float) -> float:
        return sum(a * math.sin(w * t + ph) for a, w, ph in self.termes)


def _profil_rafale(r: Rafale, t: float) -> float:
    if t <= r.debut_s or t >= r.debut_s + r.duree_s:
        return 0.0
    dans = t - r.debut_s
    reste = r.debut_s + r.duree_s - t
    return r.gite_deg * min(1.0, dans / r.montee_s, reste / r.montee_s)


def ned_vers_corps(v, gite, tangage, cap):
    """Vecteur du repère terrestre (nord, est, bas) vers le repère corps. Angles en rad."""
    x, y, z = v
    cc, sc = math.cos(cap), math.sin(cap)
    x1, y1, z1 = cc * x + sc * y, -sc * x + cc * y, z
    ct, st = math.cos(tangage), math.sin(tangage)
    x2, y2, z2 = ct * x1 - st * z1, y1, st * x1 + ct * z1
    cg, sg = math.cos(gite), math.sin(gite)
    return x2, cg * y2 + sg * z2, -sg * y2 + cg * z2


class Bateau:
    def __init__(self, cfg: ConfigBateau = ConfigBateau(),
                 pert: ConfigPerturbations = ConfigPerturbations(),
                 graine: int = 0, cap_initial_deg: float = 0.0):
        self.cfg = cfg
        self.pert = pert
        rng = random.Random(graine)
        n, per = pert.composantes, pert.periode_vagues_s
        self._v_lacet = _Houle(pert.vagues_lacet_deg, per, n, rng)
        self._v_roulis = _Houle(pert.vagues_roulis_deg, per, n, rng)
        self._v_tangage = _Houle(pert.vagues_tangage_deg, per, n, rng)
        self._v_pilon = _Houle(pert.vagues_pilonnement_ms2, per, n, rng)
        self._v_embardee = _Houle(pert.vagues_embardee_ms2, per, n, random.Random(graine + 7919))
        self.t = 0.0
        self.cap = cap_initial_deg % 360.0
        self.r = 0.0                                   # °/s
        self.gite = self.d_gite = 0.0
        self.tangage = self.d_tangage = 0.0
        self.perturbation_deg = 0.0
        self.gite_vent_deg = 0.0                       # gîte due au vent, fixée de l'extérieur
        self.perturbation_externe_deg = 0.0            # couple de lacet venu de la voilure (voilure_sim)
        self.vitesse_ms = cfg.vitesse_ms               # vitesse du bateau (variable avec une polaire)
        self._omega = (0.0, 0.0, 0.0)                  # rad/s, repère corps
        self._d_omega = (0.0, 0.0, 0.0)                # rad/s², repère corps

    def gite_visee(self, t: float) -> float:
        p = self.pert
        return (p.gite_base_deg + self.gite_vent_deg
                + sum(_profil_rafale(r, t) for r in p.rafales) + self._v_roulis(t))

    def pas(self, angle_barre_deg: float, dt: float) -> None:
        c, p = self.cfg, self.pert
        # signe corrigé le 2026-11-26 : avant, la gîte faisait ABATTRE le bateau
        self.perturbation_deg = (p.barre_ardente_deg - p.k_gite_lacet * self.gite
                                 + self._v_lacet(self.t) + self.perturbation_externe_deg)
        # Nomoto selon la vitesse (f = 1 à la vitesse de référence : identique au banc v3) :
        # le safran pousse en vitesse², le bateau répond plus vite quand il va plus vite
        f = self.vitesse_ms / c.vitesse_ms
        self.r += (c.K_par_s * (f * f * angle_barre_deg + self.perturbation_deg) - self.r) * f / c.T_s * dt
        self.cap = (self.cap + self.r * dt) % 360.0

        w = 2 * math.pi / c.periode_roulis_s
        acc = w * w * (self.gite_visee(self.t) - self.gite) - 2 * c.amortissement_roulis * w * self.d_gite
        self.d_gite += acc * dt
        self.gite += self.d_gite * dt

        w = 2 * math.pi / c.periode_tangage_s
        acc = w * w * (self._v_tangage(self.t) - self.tangage) - 2 * c.amortissement_tangage * w * self.d_tangage
        self.d_tangage += acc * dt
        self.tangage += self.d_tangage * dt
        self.t += dt
        omega = self._vitesses_corps()
        self._d_omega = tuple((a - b) / dt for a, b in zip(omega, self._omega))
        self._omega = omega

    def vitesses_corps_dps(self):
        return tuple(math.degrees(w) for w in self._omega)

    def _vitesses_corps(self):
        """Vitesses de rotation (rad/s) dans le repère corps, depuis les dérivées des angles."""
        g, th = math.radians(self.gite), math.radians(self.tangage)
        dg, dth, dps = (math.radians(a) for a in (self.d_gite, self.d_tangage, self.r))
        sg, cg, st, ct = math.sin(g), math.cos(g), math.sin(th), math.cos(th)
        return (dg - dps * st, dth * cg + dps * ct * sg, -dth * sg + dps * ct * cg)

    def mesures_physiques(self):
        """Ce que « voit » une centrale idéale placée à `position_imu_m` du centre de rotation.

        Retourne (force spécifique m/s², vitesses angulaires °/s, champ magnétique µT),
        tout dans le repère corps."""
        g, th, ps = (math.radians(a) for a in (self.gite, self.tangage, self.cap))
        dps = math.radians(self.r)
        p, q, r = self._vitesses_corps()
        gravite = ned_vers_corps((0.0, 0.0, G), g, th, ps)
        # vagues : pilonnement (vertical) et embardée (latérale), horizontales/verticales TERRESTRES
        cote = (ps + math.pi / 2)
        vagues = ned_vers_corps((self._v_embardee(self.t) * math.cos(cote),
                                 self._v_embardee(self.t) * math.sin(cote),
                                 self._v_pilon(self.t)), g, th, ps)
        # bras de levier : la centrale n'est pas au centre de rotation
        w, dw, rp = (p, q, r), self._d_omega, self.cfg.position_imu_m
        wxr = (w[1] * rp[2] - w[2] * rp[1], w[2] * rp[0] - w[0] * rp[2], w[0] * rp[1] - w[1] * rp[0])
        levier = tuple(
            (dw[1] * rp[2] - dw[2] * rp[1]) + (w[1] * wxr[2] - w[2] * wxr[1]) if k == 0 else
            (dw[2] * rp[0] - dw[0] * rp[2]) + (w[2] * wxr[0] - w[0] * wxr[2]) if k == 1 else
            (dw[0] * rp[1] - dw[1] * rp[0]) + (w[0] * wxr[1] - w[1] * wxr[0])
            for k in range(3))
        cinematique = (vagues[0] + levier[0],
                       self.vitesse_ms * dps + vagues[1] + levier[1],
                       vagues[2] + levier[2])
        force = tuple(cinematique[k] - gravite[k] for k in range(3))
        inc = math.radians(self.cfg.inclinaison_mag_deg)
        champ_ned = (self.cfg.champ_total_ut * math.cos(inc), 0.0,
                     self.cfg.champ_total_ut * math.sin(inc))
        champ = ned_vers_corps(champ_ned, g, th, ps)
        return force, tuple(math.degrees(w) for w in (p, q, r)), champ
