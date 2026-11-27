#!/usr/bin/env python3
"""essais_anticipation.py : le vent forcit et tourne — que vaut l'anticipation apprise sur 10 min ?

Chaque scénario : 10 minutes de navigation normale (le script apprend la « barre
habituelle » selon le vent), puis 4 séquences où le vent forcit de 35 % en
tournant (620, 700, 780 et 860 s).

Variantes comparées :
  aucune          pas d'anticipation
  fantome         CON-009 version 1 : calcule et journalise, n'agit PAS (doit donner
                  exactement les mêmes chiffres que « aucune »)
  active          la correction s'ajoute à l'angle de barre voulu — AU BANC SEULEMENT
  active_angle    idem, le modèle apprend aussi l'effet de l'angle du vent

Exemples (depuis ce dossier) :
  python essais_anticipation.py
  python essais_anticipation.py --scenarios renfort_compas_ardent --graines 1,2,3,4,5
  python essais_anticipation.py --scenarios renfort_compas --journal     # journal CON-009

Indicateurs (moyenne sur les 4 séquences) :
  écart max / rms   pendant chaque séquence et les 20 s qui suivent : cap en mode
                    compas, angle de vent en mode vent ;
  Δbarre            changement de barre réellement tenu entre avant et le palier ;
  prévision         écart entre la barre prévue en fin de montée et celle tenue au
                    palier (qualité de la préparation) ;
  vérin             course moyenne du vérin sur tout l'essai.

Tout est SIMULÉ. Le modèle appris a la même forme que la physique du simulateur :
le banc montre donc le MEILLEUR cas. Stdlib seulement.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime

ICI = os.path.dirname(os.path.abspath(__file__))
if ICI not in sys.path:
    sys.path.insert(0, ICI)

import banc  # noqa: E402

VARIANTES = {"aucune": ("aucune", None), "fantome": ("fantome", None),
             "active": ("active", None), "active_angle": ("active", {"modele_angle": True})}
COLONNES = (("renfort_erreur_max_deg", "écart max°", "{:9.2f}"), ("renfort_erreur_rms_deg", "rms°", "{:5.2f}"),
            ("renfort_variation_barre_deg", "Δbarre°", "{:7.2f}"), ("prevision_erreur_deg", "prévision°", "{:9.2f}"),
            ("parcours_mm_min", "vérin mm/min", "{:12.0f}"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Essais de l'anticipation par le vent (SIMULÉ).")
    ap.add_argument("--scenarios", default=",".join(banc.SCENARIOS_RENFORTS))
    ap.add_argument("--variantes", default=",".join(VARIANTES), help="parmi : " + ", ".join(VARIANTES))
    ap.add_argument("--reglage", default="pid_moyen")
    ap.add_argument("--gains", default=os.path.join(ICI, "gains_pid.json"))
    ap.add_argument("--graines", default="1,2,3")
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats"))
    ap.add_argument("--journal", action="store_true",
                    help="écrit le journal CON-009 de chaque passage fantôme (une ligne par cycle)")
    args = ap.parse_args(argv)

    with open(args.gains, encoding="utf-8") as f:
        reglages = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    if args.reglage not in reglages:
        ap.error(f"réglage inconnu ; possibles : {', '.join(reglages)}")
    scenarios = [x.strip() for x in args.scenarios.split(",") if x.strip()]
    hors = [x for x in scenarios if x not in banc.SCENARIOS or not banc.SCENARIOS[x].vent
            or not banc.SCENARIOS[x].vent.renforcements]
    if hors:
        ap.error(f"pas des scénarios de renforcement : {', '.join(hors)} ; possibles : "
                 + ", ".join(banc.SCENARIOS_RENFORTS))
    variantes = [v.strip() for v in args.variantes.split(",") if v.strip()]
    if any(v not in VARIANTES for v in variantes):
        ap.error("variante inconnue ; possibles : " + ", ".join(VARIANTES))
    try:
        graines = [int(g) for g in args.graines.split(",") if g.strip()]
    except ValueError:
        ap.error("--graines : entiers séparés par des virgules")

    os.makedirs(args.sortie, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    lignes = []
    print("SIMULÉ — le modèle appris a la forme de la physique du banc : meilleur cas.\n")
    for nom in scenarios:
        scn = banc.SCENARIOS[nom]
        print(f"=== {nom} : {scn.description} (graines {args.graines})")
        print(f"  {'variante':14s}" + " ".join(f"{t:>{len(g.format(0.0))}s}" for _, t, g in COLONNES))
        for v in variantes:
            mode, params = VARIANTES[v]
            rs = []
            for g in graines:
                journal = (os.path.join(args.sortie, f"journal_anticipation_{horodatage}_{nom}_g{g}.csv")
                           if args.journal and v == "fantome" else None)
                rs.append(banc.executer(scn, reglages[args.reglage], g, fusion="mahony",
                                        anticipation=mode, params_anticipation=params,
                                        chemin_journal_anticipation=journal))
            moy = {k: sum(r.get(k, float("nan")) for r in rs) / len(rs) for k, _, _ in COLONNES}
            print(f"  {v:14s}" + " ".join(("—".rjust(len(g.format(0.0))) if math.isnan(moy[c])
                                            else g.format(moy[c])) for c, _, g in COLONNES))
            lignes.append({"scenario": nom, "variante": v, **moy,
                           "modele_pret_s": sum(r.get("modele_pret_s", float("nan")) for r in rs) / len(rs)})
        print()
    chemin = os.path.join(args.sortie, f"essais_anticipation_{horodatage}.csv")
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    print(f"Résultats : {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
