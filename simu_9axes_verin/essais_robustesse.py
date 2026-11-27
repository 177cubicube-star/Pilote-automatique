#!/usr/bin/env python3
"""essais_robustesse.py : un algorithme doit tenir sur PLUSIEURS bateaux plausibles.

Étape 1 du travail en profondeur (2026-11-26) : le banc honnête. Chaque profil de
`voilure_sim.PROFILS` a une physique qui DIFFÈRE de ce que supposent les
algorithmes (table de gîte irrégulière, retard, ardeur qui grandit avec la gîte,
couple des voiles, vitesse qui suit le vent). Le profil « reference » redonne
exactement le banc v3 : c'est le contrôle.

Exemples (depuis ce dossier) :
  python essais_robustesse.py                       # matrice complète (une dizaine de minutes)
  python essais_robustesse.py --profils reference,tout --variantes fantome,active --graines 1

Pour chaque profil × réglage × variante : écart de cap p95 sur tout l'essai,
écart maximal pendant les 4 renforcements, changement de barre réellement tenu,
erreur de la barre prévue (mode fantôme), course du vérin. En bas : le PIRE cas
sur tous les profils, qui compte plus que la moyenne.

Tout est SIMULÉ ; les profils sont plausibles, pas mesurés. Stdlib seulement.
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
from voilure_sim import PROFILS  # noqa: E402

VARIANTES = {"fantome": ("fantome", None), "active": ("active", None),
             "active_angle": ("active", {"modele_angle": True})}
COLONNES = (("erreur_p95_deg", "p95°", "{:5.2f}"), ("renfort_erreur_max_deg", "rafale max°", "{:11.2f}"),
            ("renfort_variation_barre_deg", "Δbarre°", "{:7.2f}"), ("prevision_erreur_deg", "prévision°", "{:10.2f}"),
            ("parcours_mm_min", "vérin", "{:5.0f}"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Matrice de robustesse sur profils de voiliers (SIMULÉ).")
    ap.add_argument("--profils", default=",".join(PROFILS))
    ap.add_argument("--reglages", default="pid_moyen,pid_moyen_sans_zone_i")
    ap.add_argument("--variantes", default="fantome,active", help="parmi : " + ", ".join(VARIANTES))
    ap.add_argument("--scenario", default="renfort_compas")
    ap.add_argument("--gains", default=os.path.join(ICI, "gains_pid.json"))
    ap.add_argument("--graines", default="1,2,3")
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats"))
    args = ap.parse_args(argv)

    with open(args.gains, encoding="utf-8") as f:
        tous = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    liste = lambda txt: [x.strip() for x in txt.split(",") if x.strip()]
    profils, reglages, variantes = liste(args.profils), liste(args.reglages), liste(args.variantes)
    if any(p not in PROFILS for p in profils):
        ap.error("profil inconnu ; possibles : " + ", ".join(PROFILS))
    if any(r not in tous for r in reglages):
        ap.error("réglage inconnu ; possibles : " + ", ".join(tous))
    if any(v not in VARIANTES for v in variantes):
        ap.error("variante inconnue ; possibles : " + ", ".join(VARIANTES))
    scn = banc.SCENARIOS.get(args.scenario)
    if scn is None or scn.vent is None:
        ap.error("scénario avec vent requis (par exemple renfort_compas)")
    graines = [int(g) for g in liste(args.graines)]

    os.makedirs(args.sortie, exist_ok=True)
    lignes = []
    print(f"SIMULÉ — scénario {scn.nom}, graines {args.graines}. Profils plausibles, pas mesurés.\n")
    entete = f"  {'réglage':24s} {'variante':13s}" + " ".join(f"{t:>{len(g.format(0.0))}s}" for _, t, g in COLONNES)
    for p in profils:
        print(f"=== {p} : {PROFILS[p].description}")
        print(entete)
        for r in reglages:
            for v in variantes:
                mode, params = VARIANTES[v]
                rs = [banc.executer(scn, tous[r], g, fusion="mahony", voilier=p, anticipation=mode,
                                    params_anticipation=params) for g in graines]
                moy = {k: sum(x.get(k, float("nan")) for x in rs) / len(rs) for k, _, _ in COLONNES}
                print(f"  {r:24s} {v:13s}" + " ".join(
                    ("—".rjust(len(g.format(0.0))) if math.isnan(moy[c]) else g.format(moy[c]))
                    for c, _, g in COLONNES))
                lignes.append({"profil": p, "reglage": r, "variante": v, **moy})
        print()
    print("=== Pire cas sur les profils (le plus grand écart p95 et en rafale)")
    print(f"  {'réglage':24s} {'variante':13s}{'p95° pire':>10s}{'profil':>22s}{'rafale max° pire':>18s}{'profil':>22s}")
    for r in reglages:
        for v in variantes:
            sel = [x for x in lignes if x["reglage"] == r and x["variante"] == v]
            a = max(sel, key=lambda x: x["erreur_p95_deg"])
            b = max(sel, key=lambda x: x["renfort_erreur_max_deg"])
            print(f"  {r:24s} {v:13s}{a['erreur_p95_deg']:10.2f}{a['profil']:>22s}"
                  f"{b['renfort_erreur_max_deg']:18.2f}{b['profil']:>22s}")
    chemin = os.path.join(args.sortie, f"essais_robustesse_{datetime.now():%Y%m%d-%H%M%S}.csv")
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    print(f"\nRésultats : {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
