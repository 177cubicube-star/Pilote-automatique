#!/usr/bin/env python3
"""essais_pid.py : compare plusieurs réglages de barre sur plusieurs scénarios.

Exemples (depuis ce dossier) :

  # tout : préréglages de gains_pid.json × scénarios par défaut, graine 1
  python essais_pid.py

  # trois réglages, deux scénarios, trois graines (moyenne), avec journaux CSV
  python essais_pid.py --reglages pid_doux,pid_moyen,pypilot_defaut ^
                       --scenarios vagues,rafales --graines 1,2,3 --journal

  # mon propre fichier de gains
  python essais_pid.py --gains mes_gains.json

  # voir la liste des scénarios
  python essais_pid.py --liste

  # comparer les filtres et les sources de gîte (avec un réglage fixe)
  python essais_pid.py --reglages pid_moyen --scenarios vagues,rafales ^
                       --fusions complementaire,mahony --sources-gite imu,inclinometre,parfaite

  # changer un gain du filtre de Mahony
  python essais_pid.py --fusions mahony --params-fusion "{\"kp_acc\": 0.2}"

Sorties : un tableau par scénario à l'écran (classé par erreur p95), et un CSV
`resultats/essais_pid_AAAAMMJJ-HHMMSS.csv` avec tous les indicateurs.
Avec --journal : un CSV par passage (20 lignes par seconde), lisible dans un
tableur ou Node-RED, pour regarder cap, barre et vérin dans le temps.

Tout est SIMULÉ (bateau, vérin, bruits : hypothèses). Les chiffres comparent des
réglages entre eux ; ils ne prédisent pas le comportement sur le Capri 22.
Stdlib seulement.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from datetime import datetime

ICI = os.path.dirname(os.path.abspath(__file__))
if ICI not in sys.path:                 # fonctionne aussi avec « python -I »
    sys.path.insert(0, ICI)

import banc  # noqa: E402

COLONNES = (
    ("erreur_p95_deg", "p95°", "{:5.2f}"),
    ("erreur_rms_deg", "rms°", "{:5.2f}"),
    ("erreur_max_deg", "max°", "{:5.1f}"),
    ("depassement_max_deg", "dép.°", "{:5.1f}"),
    ("temps_reponse_max_s", "rép.s", "{:5.1f}"),
    ("ecart_estimation_rms_deg", "est.°", "{:5.2f}"),
    ("erreur_gite_rms_deg", "gîte°", "{:5.2f}"),
    ("parcours_mm_min", "mm/min", "{:6.0f}"),
    ("inversions_min", "inv/min", "{:6.1f}"),
    ("energie_wh_h", "Wh/h", "{:5.2f}"),
    ("pct_saturation", "sat%", "{:5.1f}"),
)


def charger_reglages(chemin: str) -> dict:
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)
    return {nom: r for nom, r in donnees.items() if not nom.startswith("_")}


def moyenne(resultats: list[dict]) -> dict:
    sortie = dict(resultats[0])
    for cle, val in resultats[0].items():
        if isinstance(val, (int, float)) and cle != "graine":
            vals = [r[cle] for r in resultats]
            sortie[cle] = sum(vals) / len(vals)
    p95 = sortie["erreur_p95_deg"]
    sortie["verdict"] = ("dans la cible" if p95 <= 4.0 else "dégradé" if p95 <= 5.0
                         else "hors cible")
    sortie["graine"] = "+".join(str(r["graine"]) for r in resultats)
    return sortie


def fmt(gabarit: str, val) -> str:
    if isinstance(val, float) and math.isnan(val):
        return "—".rjust(len(gabarit.format(0.0)))
    if isinstance(val, float) and math.isinf(val):
        return "jamais".rjust(len(gabarit.format(0.0)))
    return gabarit.format(val)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compare des réglages de barre (SIMULÉ).")
    ap.add_argument("--gains", default=os.path.join(ICI, "gains_pid.json"))
    ap.add_argument("--reglages", help="noms séparés par des virgules (défaut : tous)")
    ap.add_argument("--scenarios", help="noms séparés par des virgules (défaut : "
                    + ",".join(banc.SCENARIOS_DEFAUT) + ")")
    ap.add_argument("--graines", default="1", help="ex. 1,2,3 : moyenne sur plusieurs tirages")
    ap.add_argument("--fusions", default="complementaire",
                    help="complementaire, mahony, ou les deux séparés par une virgule")
    ap.add_argument("--sources-gite", default="imu",
                    help="imu, inclinometre, parfaite (plusieurs : séparées par des virgules)")
    ap.add_argument("--params-fusion", help='JSON, ex. {"kp_acc": 0.3, "vitesse_ms": null}')
    ap.add_argument("--params-inclinometre", help='JSON, ex. {"tau_filtre_s": 1.0}')
    ap.add_argument("--rodage-s", type=float, default=banc.RODAGE_S,
                    help="secondes au quai, bateau immobile, avant chaque passage (défaut 60)")
    ap.add_argument("--accel-calibre", action="store_true",
                    help="accéléromètre calibré : biais de 2 mg au lieu de 10 mg (hypothèses)")
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats"))
    ap.add_argument("--journal", action="store_true", help="écrit un CSV par passage")
    ap.add_argument("--liste", action="store_true", help="liste les scénarios et sort")
    args = ap.parse_args(argv)

    if args.liste:
        for s in banc.SCENARIOS.values():
            defaut = "" if s.nom in banc.SCENARIOS_DEFAUT else "  (hors défaut)"
            print(f"{s.nom:20s} {s.duree_s:5.0f} s  {s.description}{defaut}")
        return 0

    reglages = charger_reglages(args.gains)
    if args.reglages:
        noms = [n.strip() for n in args.reglages.split(",") if n.strip()]
        inconnus = [n for n in noms if n not in reglages]
        if inconnus:
            ap.error(f"réglages inconnus : {', '.join(inconnus)} ; disponibles : {', '.join(reglages)}")
        reglages = {n: reglages[n] for n in noms}
    noms_scn = ([n.strip() for n in args.scenarios.split(",") if n.strip()]
                if args.scenarios else list(banc.SCENARIOS_DEFAUT))
    inconnus = [n for n in noms_scn if n not in banc.SCENARIOS]
    if inconnus:
        ap.error(f"scénarios inconnus : {', '.join(inconnus)} ; voir --liste")
    try:
        graines = [int(g) for g in args.graines.split(",") if g.strip()]
    except ValueError:
        ap.error("--graines : entiers séparés par des virgules")
    if not graines:
        ap.error("--graines est vide")

    fusions = [f.strip() for f in args.fusions.split(",") if f.strip()]
    sources = [g.strip() for g in args.sources_gite.split(",") if g.strip()]
    inconnus = [f for f in fusions if f not in banc.FUSIONS] + \
               [g for g in sources if g not in banc.SOURCES_GITE]
    if inconnus or not fusions or not sources:
        ap.error(f"--fusions ({', '.join(banc.FUSIONS)}) ou --sources-gite "
                 f"({', '.join(banc.SOURCES_GITE)}) invalides : {', '.join(inconnus) or 'liste vide'}")
    try:
        params_fusion = json.loads(args.params_fusion) if args.params_fusion else None
        params_incl = json.loads(args.params_inclinometre) if args.params_inclinometre else None
    except json.JSONDecodeError as erreur:
        ap.error(f"JSON invalide : {erreur}")
    bruit_imu = (banc.ConfigBruit(ecart_type_biais_accel_g=0.002) if args.accel_calibre
                 else banc.ConfigBruit())
    combinaisons = [(f, g) for f in fusions for g in sources]
    plusieurs = len(combinaisons) > 1

    os.makedirs(args.sortie, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    lignes = []
    debut = time.monotonic()
    print("SIMULÉ — bateau, vérin et bruits hypothétiques ; comparer, pas prédire."
          + (" Accéléromètre CALIBRÉ (biais 2 mg)." if args.accel_calibre else "") + "\n")
    for nom_scn in noms_scn:
        scn = banc.SCENARIOS[nom_scn]
        print(f"=== {nom_scn} : {scn.description} ({scn.duree_s:.0f} s, graines {args.graines})")
        resultats = []
        for nom_reg, reglage in reglages.items():
            for fusion, source in combinaisons:
                etiquette = f"{nom_reg} | {fusion} | {source}" if plusieurs else nom_reg
                suffixe = f"_{fusion}_{source}" if plusieurs else ""
                parGraine = []
                for g in graines:
                    journal = (os.path.join(args.sortie, f"journal_{horodatage}_{nom_scn}_{nom_reg}{suffixe}_g{g}.csv")
                               if args.journal else None)
                    try:
                        parGraine.append(banc.executer(
                            scn, reglage, g, journal, fusion=fusion, source_gite=source,
                            params_fusion=params_fusion, params_inclinometre=params_incl,
                            bruit_imu=bruit_imu, rodage_s=args.rodage_s))
                    except ValueError as erreur:
                        print(f"  {etiquette} : refusé — {erreur}", file=sys.stderr)
                        return 2
                r = moyenne(parGraine)
                r["reglage"] = nom_reg
                r["etiquette"] = etiquette
                resultats.append(r)
        resultats.sort(key=lambda r: (math.isnan(r["erreur_p95_deg"]), r["erreur_p95_deg"]))
        largeur = max(28, max(len(r["etiquette"]) for r in resultats))
        entete = f"  {'réglage':{largeur}s}" + " ".join(f"{t:>{len(g.format(0.0))}s}" for _, t, g in COLONNES)
        print(entete + "  verdict")
        for r in resultats:
            print(f"  {r['etiquette']:{largeur}s}"
                  + " ".join(fmt(g, r[c]) for c, _, g in COLONNES)
                  + f"  {r['verdict']}"
                  + (f"  [lectures ratées {r['lectures_ratees']:.0f}]" if r["lectures_ratees"] else "")
                  + (f"  [surintensités {r['surintensites']:.0f}]" if r["surintensites"] else ""))
        print()
        lignes.extend(resultats)

    chemin = os.path.join(args.sortie, f"essais_pid_{horodatage}.csv")
    cles = ["reglage", "fusion", "source_gite"] + [
        k for k in lignes[0] if k not in ("reglage", "fusion", "source_gite", "etiquette")]
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cles, extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)
    print("Légende : p95/rms/max = écart de cap en route ; dép. = dépassement après un "
          "changement de cap ; rép. = temps pour tenir ±2° ;\n"
          "          est. = erreur du cap ESTIMÉ ; gîte° = erreur de la gîte estimée ;\n"
          "          mm/min et inv/min = usure du vérin ; "
          "Wh/h = énergie du moteur ; sat% = commande à fond.")
    print(f"Résultats : {chemin}  ({time.monotonic() - debut:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
