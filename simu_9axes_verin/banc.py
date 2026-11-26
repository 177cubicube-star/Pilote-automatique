"""banc.py : la boucle complète, de la vague jusqu'au vérin.

À chaque pas de 10 ms (100 Hz, la cadence du magnétomètre) :

  bateau ──(force, rotations, champ)──> puce ICM-20948 simulée
     ^                                       │ octets dans les registres
     │                                       v
     │                         faux bus I2C ──> lecteur Python (le vrai code)
     │                                       │ m/s², °/s, µT
     │                                       v
     │                                  fusion (cap, lacet, gîte)
     │                                       │ toutes les 50 ms (20 Hz)
     │                                       v
  angle réel <── vérin simulé <── u ── régulateur (PID ou pypilot)
                    │
                    └── potentiomètre ──> angle mesuré, rendu au régulateur

Tout ce qui sort d'ici est SIMULÉ : bateau, vérin, bruits et vagues sont des
hypothèses (voir chaque module). Les chiffres servent à COMPARER des réglages
entre eux et à trouver les pièges, pas à prédire le comportement en mer.

Indicateurs (calculés sur le cap VRAI, pas sur le cap estimé) :
  erreur_rms / p95 / max   : écart de cap « en route », hors des 30 s (60 s
                             pour aimant_non_calibre) qui suivent un
                             changement de consigne
  ecart_estimation_rms     : cap estimé − cap vrai (qualité de la chaîne de mesure)
  erreur_gite_rms          : gîte estimée − gîte vraie (la cause principale des
                             erreurs de cap : voir README, « Source de gîte »)
  depassement, temps_reponse : après chaque changement de consigne d'au moins 5°
                             (temps pour entrer dans ±2° et y rester)
  parcours_mm_min, inversions_min : usure du vérin
  energie_wh_h             : énergie du MOTEUR seulement (pas l'électronique)
  verdict                  : p95 ≤ 4° « dans la cible » ; ≤ 5° « dégradé » ;
                             sinon « hors cible » (cible ±2 à 4°, ±5° dégradé,
                             DEC du 2026-11 ; mesurer la cible par le p95 est
                             une HYPOTHÈSE de lecture)
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field, replace

from bateau_sim import Bateau, ConfigBateau, ConfigPerturbations, Rafale
from capteur_gite_sim import SOURCES_GITE, InclinometreSim, reference_parfaite
from fusion_cap import FUSIONS, construire_fusion, enrouler_180
from icm20948_lecteur import ErreurCapteur, LecteurICM20948
from icm20948_sim import ConfigBruit, FauxBusI2C, PuceICM20948
from regulateurs import EntreeRegulateur, construire_regulateur
from verin_moteur_sim import ConfigVerin, Verin

DT_PHYSIQUE = 0.01
RODAGE_S = 60.0
PERIODE_REGULATION = 0.05
FENETRE_APRES_CONSIGNE_S = 30.0
BANDE_REPONSE_DEG = 2.0


@dataclass(frozen=True)
class Scenario:
    nom: str
    description: str
    duree_s: float
    consignes: tuple = ((0.0, 0.0),)           # (instant, cap) : marches successives
    perturbations: ConfigPerturbations = ConfigPerturbations()
    debut_mesure_s: float = 20.0
    fer_dur_non_compense_ut: tuple = (0.0, 0.0, 0.0)
    taux_erreur_i2c: float = 0.0
    verin: dict = field(default_factory=dict)  # remplace des valeurs de ConfigVerin
    detache_a_s: float | None = None
    cap_initial_deg: float = 0.0
    fenetre_apres_consigne_s: float = FENETRE_APRES_CONSIGNE_S

    def consigne_a(self, t: float) -> float:
        c = self.consignes[0][1]
        for instant, cap in self.consignes:
            if t >= instant:
                c = cap
        return c


VAGUES = ConfigPerturbations(vagues_lacet_deg=4.0, vagues_roulis_deg=6.0,
                             vagues_tangage_deg=3.0, vagues_pilonnement_ms2=1.0,
                             vagues_embardee_ms2=0.5,   # HYPOTHÈSE la plus influente : à mesurer

                             periode_vagues_s=3.0, barre_ardente_deg=2.0)

SCENARIOS = {s.nom: s for s in (
    Scenario("calme_pas20", "Eau plate, changements de cap de 20° puis -20°", 130.0,
             consignes=((0, 0.0), (10, 20.0), (70, 0.0)), debut_mesure_s=10.0,
             perturbations=ConfigPerturbations(barre_ardente_deg=2.0)),
    Scenario("vagues", "Clapot de lac (lacet, roulis, tangage), cap fixe", 180.0,
             perturbations=VAGUES),
    Scenario("rafales", "Rafales qui font gîter de 15° ; la gîte fait remonter au vent", 180.0,
             perturbations=replace(VAGUES, gite_base_deg=8.0, k_gite_lacet=0.15,
                                   rafales=tuple(Rafale(t0, 12.0, 15.0)
                                                 for t0 in (40, 80, 120, 160)))),
    Scenario("aimant_non_calibre", "Fer dur de 2,5 µT non compensé, caps 0/90/180 "
             "(teste la chaîne de mesure, pas le réglage)", 200.0,
             consignes=((0, 0.0), (60, 90.0), (130, 180.0)), fenetre_apres_consigne_s=60.0,
             perturbations=replace(VAGUES, vagues_lacet_deg=2.0),
             fer_dur_non_compense_ut=(2.0, -1.5, 0.0)),
    Scenario("i2c_perturbe", "Vagues + 5 % des transactions I2C en erreur", 180.0,
             perturbations=VAGUES, taux_erreur_i2c=0.05),
    Scenario("verin_lent", "Vagues avec un vérin deux fois plus lent (15 mm/s)", 180.0,
             perturbations=VAGUES, verin={"vitesse_max_mm_s": 15.0}),
    Scenario("verin_detache", "Vagues ; la barre se détache du vérin à 60 s", 150.0,
             perturbations=VAGUES, detache_a_s=60.0),
)}

# « aimant_non_calibre » et « verin_detache » éprouvent la chaîne de mesure et la
# détection de pannes, pas le réglage : on les lance à part (--scenarios).
SCENARIOS_DEFAUT = ("calme_pas20", "vagues", "rafales", "i2c_perturbe", "verin_lent")

# Clés du dictionnaire passé à l'observateur (degrés, °/s, A, mm, secondes de simulation)
ETAT_OBSERVATEUR = ("t", "consigne", "cap_vrai", "cap_estime", "lacet_vrai", "lacet_estime",
                    "gite_vraie", "gite_estimee", "tangage_estime", "u", "angle_barre_reel",
                    "angle_barre_mesure", "x_tige_mm", "courant_a")

COLONNES_JOURNAL = ("t", "consigne", "cap_vrai", "cap_estime", "lacet_vrai", "lacet_estime",
                    "gite_vraie", "gite_estimee", "u", "angle_barre_reel", "angle_barre_mesure",
                    "x_tige_mm", "courant_a")


def _percentile(valeurs, q):
    if not valeurs:
        return float("nan")
    tri = sorted(valeurs)
    return tri[max(0, math.ceil(q * len(tri)) - 1)]


def executer(scenario: Scenario, reglage: dict, graine: int = 1,
             chemin_journal: str | None = None,
             cfg_bateau: ConfigBateau = ConfigBateau(),
             fusion: str = "complementaire", source_gite: str = "imu",
             params_fusion: dict | None = None,
             params_inclinometre: dict | None = None,
             bruit_imu: ConfigBruit = ConfigBruit(),
             rodage_s: float = RODAGE_S,
             observateur=None) -> dict:
    """Joue un scénario avec un réglage ; retourne les indicateurs.

    fusion      : « complementaire » (défaut) ou « mahony »
    source_gite : « imu » (défaut), « inclinometre » ou « parfaite »
    Pour Mahony, la compensation centripète utilise par défaut la vitesse du
    bateau simulé, comme si le GPS la donnait exactement (hypothèse) ;
    params_fusion = {"vitesse_ms": None} la coupe.
    bruit_imu   : défauts de la centrale (biais tirés au hasard par graine).
    rodage_s    : durée pendant laquelle la centrale et la fusion tournent au QUAI,
                  bateau immobile, avant le départ (comme un pilote allumé avant
                  de larguer) : la fusion a le temps d'apprendre les biais du
                  gyroscope, et les indicateurs ne mesurent pas ce démarrage.
    observateur : fonction appelée à chaque pas de régulation (20 Hz) avec un
                  dictionnaire d'état (voir ETAT_OBSERVATEUR) ; sert à publier
                  vers Signal K ou à suivre le banc en temps réel. Ne modifie rien."""
    if source_gite not in SOURCES_GITE:
        raise ValueError(f"source de gîte inconnue {source_gite!r} ; possibles : {', '.join(SOURCES_GITE)}")
    if fusion not in FUSIONS:
        raise ValueError(f"fusion inconnue {fusion!r} ; possibles : {', '.join(FUSIONS)}")
    params_f = dict(params_fusion or {})
    if fusion == "mahony":
        params_f.setdefault("vitesse_ms", cfg_bateau.vitesse_ms)
    regulateur = construire_regulateur(reglage)
    bateau = Bateau(cfg_bateau, scenario.perturbations, graine, scenario.cap_initial_deg)
    verin = Verin(replace(ConfigVerin(), **scenario.verin), graine + 1)
    puce = PuceICM20948(bruit_imu, graine=graine + 2)
    bus = FauxBusI2C(puce, graine=graine + 3)
    lecteur = LecteurICM20948(bus, attente=lambda s: None)
    lecteur.demarrer()                      # démarrage sans erreurs, puis bus perturbé
    bus.taux_erreur = scenario.taux_erreur_i2c
    filtre = construire_fusion(fusion, **params_f)
    inclinometre = (InclinometreSim(graine=graine + 4, **(params_inclinometre or {}))
                    if source_gite == "inclinometre" else None)

    # ---- rodage au quai : bateau immobile, mêmes capteurs, même fusion
    quai = Bateau(cfg_bateau, ConfigPerturbations(), graine, scenario.cap_initial_deg)
    f_q, w_q, c_q = quai.mesures_physiques()
    c_q = tuple(c_q[k] + scenario.fer_dur_non_compense_ut[k] for k in range(3))
    dt_q = 0.0
    for i in range(int(round(rodage_s / DT_PHYSIQUE))):
        puce.mettre_a_jour(f_q, w_q, c_q, 20.0, DT_PHYSIQUE)
        ref_q = None
        if inclinometre is not None:
            ref_q = inclinometre.lire(f_q, DT_PHYSIQUE)
        elif source_gite == "parfaite":
            ref_q = reference_parfaite(quai.gite, quai.tangage)
        dt_q += DT_PHYSIQUE
        try:
            filtre.mettre_a_jour(lecteur.lire(-rodage_s + i * DT_PHYSIQUE), dt_q, ref_q)
            dt_q = 0.0
        except ErreurCapteur:
            pass

    n = int(round(scenario.duree_s / DT_PHYSIQUE))
    pas_regul = int(round(PERIODE_REGULATION / DT_PHYSIQUE))
    u, est = 0.0, None
    dt_fusion = 0.0
    lectures_ratees = 0
    erreurs_route, ecarts_est, ecarts_gite, saturations, nb_regul = [], [], [], 0, 0
    changements = [(t0, c) for (t0, c), (_, c_prec)
                   in zip(scenario.consignes[1:], scenario.consignes[:-1])
                   if abs(enrouler_180(c - c_prec)) >= 5.0]
    suivi_pas = [{"t0": t0, "cible": c, "dep": c - scenario.consigne_a(t0 - 1e-6),
                  "max_au_dela": 0.0, "entree": None} for t0, c in changements]
    journal = None
    if chemin_journal:
        fichier = open(chemin_journal, "w", newline="", encoding="utf-8")
        journal = csv.writer(fichier)
        journal.writerow(COLONNES_JOURNAL)

    try:
        for i in range(n):
            t = i * DT_PHYSIQUE
            if scenario.detache_a_s is not None and t >= scenario.detache_a_s:
                verin.detache = True

            bateau.pas(verin.angle_barre_deg(), DT_PHYSIQUE)
            force, rotations, champ = bateau.mesures_physiques()
            champ = tuple(champ[k] + scenario.fer_dur_non_compense_ut[k] for k in range(3))
            puce.mettre_a_jour(force, rotations, champ, 20.0, DT_PHYSIQUE)

            reference = None
            if inclinometre is not None:
                reference = inclinometre.lire(force, DT_PHYSIQUE)
            elif source_gite == "parfaite":
                reference = reference_parfaite(bateau.gite, bateau.tangage)

            dt_fusion += DT_PHYSIQUE
            try:
                mesure = lecteur.lire(t)
                nouvelle = filtre.mettre_a_jour(mesure, dt_fusion, reference)
                dt_fusion = 0.0
                if nouvelle is not None:
                    est = nouvelle
            except ErreurCapteur:
                lectures_ratees += 1          # on garde l'estimation précédente

            consigne = scenario.consigne_a(t)
            if i % pas_regul == 0 and est is not None:
                angle_mes = verin.angle_mesure_deg()
                u = regulateur.calculer(EntreeRegulateur(est.cap_deg, est.taux_lacet_dps,
                                                         consigne, angle_mes),
                                        PERIODE_REGULATION)
                nb_regul += 1
                saturations += abs(u) >= 0.99
                if observateur is not None:
                    observateur({"t": t, "consigne": consigne, "cap_vrai": bateau.cap,
                                 "cap_estime": est.cap_deg, "lacet_vrai": bateau.r,
                                 "lacet_estime": est.taux_lacet_dps, "gite_vraie": bateau.gite,
                                 "gite_estimee": est.gite_deg, "tangage_estime": est.tangage_deg,
                                 "u": u, "angle_barre_reel": verin.angle_barre_deg(),
                                 "angle_barre_mesure": angle_mes, "x_tige_mm": verin.x_tige,
                                 "courant_a": verin.courant})
                if journal:
                    journal.writerow([f"{t:.2f}", f"{consigne:.1f}", f"{bateau.cap:.2f}",
                                      f"{est.cap_deg:.2f}", f"{bateau.r:.3f}",
                                      f"{est.taux_lacet_dps:.3f}", f"{bateau.gite:.2f}",
                                      f"{est.gite_deg:.2f}", f"{u:.3f}",
                                      f"{verin.angle_barre_deg():.2f}", f"{angle_mes:.2f}",
                                      f"{verin.x_tige:.1f}", f"{verin.courant:.2f}"])
            verin.pas(u, DT_PHYSIQUE)

            # ---------------------------------------------------- indicateurs
            err = enrouler_180(consigne - bateau.cap)
            if est is not None and t >= 5.0:
                ecarts_est.append(enrouler_180(est.cap_deg - bateau.cap))
                ecarts_gite.append(est.gite_deg - bateau.gite)
            dernier_chgt = max([t0 for t0, _ in changements if t0 <= t], default=-1e9)
            if t >= scenario.debut_mesure_s and t - dernier_chgt >= scenario.fenetre_apres_consigne_s:
                erreurs_route.append(err)
            for s in suivi_pas:
                if t < s["t0"]:
                    continue
                fin = min([t0 for t0, _ in changements if t0 > s["t0"]], default=scenario.duree_s)
                if t >= fin:
                    continue
                au_dela = -err * math.copysign(1.0, s["dep"])   # >0 : on a dépassé la cible
                s["max_au_dela"] = max(s["max_au_dela"], au_dela)
                if abs(err) <= BANDE_REPONSE_DEG:
                    if s["entree"] is None:
                        s["entree"] = t
                else:
                    s["entree"] = None
    finally:
        if journal:
            fichier.close()

    duree_min = scenario.duree_s / 60.0
    abs_route = [abs(e) for e in erreurs_route]
    p95 = _percentile(abs_route, 0.95)
    reponses = [(s["entree"] - s["t0"]) if s["entree"] is not None else float("inf")
                for s in suivi_pas]
    verdict = ("dans la cible" if p95 <= 4.0 else "dégradé" if p95 <= 5.0 else "hors cible")
    rms = (lambda l: math.sqrt(sum(e * e for e in l) / len(l)) if l else float("nan"))
    return {
        "scenario": scenario.nom,
        "graine": graine,
        "fusion": fusion,
        "source_gite": source_gite,
        "erreur_rms_deg": math.sqrt(sum(e * e for e in erreurs_route) / len(erreurs_route))
        if erreurs_route else float("nan"),
        "erreur_p95_deg": p95,
        "erreur_max_deg": max(abs_route, default=float("nan")),
        "ecart_estimation_rms_deg": rms(ecarts_est),
        "erreur_gite_rms_deg": rms(ecarts_gite),
        "depassement_max_deg": max((s["max_au_dela"] for s in suivi_pas), default=float("nan")),
        "temps_reponse_max_s": max(reponses, default=float("nan")),
        "parcours_mm_min": verin.parcours_mm / duree_min,
        "inversions_min": verin.inversions / duree_min,
        "energie_wh_h": verin.energie_j / 3600.0 / (scenario.duree_s / 3600.0),
        "surintensites": verin.surintensites,
        "pct_saturation": 100.0 * saturations / nb_regul if nb_regul else float("nan"),
        "temps_en_butee_s": verin.temps_en_butee_s,
        "lectures_ratees": lectures_ratees,
        "erreurs_bus": lecteur.erreurs_bus,
        "verdict": verdict,
    }
