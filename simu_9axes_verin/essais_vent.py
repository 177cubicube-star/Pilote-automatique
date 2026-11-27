#!/usr/bin/env python3
"""essais_vent.py : compare des réglages du MODE VENT APPARENT sur les scénarios de vent.

Exemples (depuis ce dossier) :

  python essais_vent.py                                  # variantes de base, 3 graines
  python essais_vent.py --scenarios vent_arriere --graines 1,2,3,4,5
  python essais_vent.py --params-mode-vent "{\\"tau_s\\": 8}"   # ajoute une variante à soi

Indicateurs :
  angle rms / p95 : écart entre l'angle de vent apparent VRAI (au pont) et l'angle voulu,
                    pendant que le mode vent est actif ;
  mm/min, inv/min : travail du vérin ;
  bord            : passages du vent de l'autre côté du bateau (virement ou empannage
                    involontaire) — doit rester à 0 ;
  secours, alarme : secondes passées en secours compas, instant de l'alarme « vent perdu ».

Tout est SIMULÉ (vent, girouette, mât, bateau : hypothèses). Stdlib seulement.
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

VARIANTES = {
    "sans_correction": {"corriger_gite": False, "corriger_mouvement": False},
    "correction_sans_amortissement_assorti": {"amortissement_capteur_s": 0.0},
    "defaut": {},
    "filtre_6s": {"tau_s": 6.0},
    "filtre_10s": {"tau_s": 10.0},
}
COLONNES = (("awa_rms_deg", "angle rms°", "{:9.2f}"), ("awa_p95_deg", "angle p95°", "{:9.2f}"),
            ("parcours_mm_min", "mm/min", "{:6.0f}"), ("inversions_min", "inv/min", "{:7.1f}"),
            ("passages_de_bord", "bord", "{:4.1f}"), ("temps_secours_s", "secours s", "{:9.0f}"),
            ("alarme_vent_perdu_s", "alarme s", "{:8.1f}"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Essais du mode vent apparent (SIMULÉ).")
    ap.add_argument("--scenarios", default=",".join(banc.SCENARIOS_VENT))
    ap.add_argument("--variantes", default=",".join(VARIANTES),
                    help="parmi : " + ", ".join(VARIANTES))
    ap.add_argument("--params-mode-vent", help="JSON : une variante de plus, nommée « perso »")
    ap.add_argument("--reglage", default="pid_moyen")
    ap.add_argument("--gains", default=os.path.join(ICI, "gains_pid.json"))
    ap.add_argument("--fusion", default="mahony", choices=sorted(banc.FUSIONS))
    ap.add_argument("--graines", default="1,2,3")
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats"))
    args = ap.parse_args(argv)

    with open(args.gains, encoding="utf-8") as f:
        reglages = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    if args.reglage not in reglages:
        ap.error(f"réglage inconnu ; possibles : {', '.join(reglages)}")
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    hors = [s for s in scenarios if s not in banc.SCENARIOS or banc.SCENARIOS[s].mode_vent is None]
    if hors:
        ap.error(f"pas des scénarios de mode vent : {', '.join(hors)} ; possibles : "
                 + ", ".join(banc.SCENARIOS_VENT))
    variantes = {}
    for v in (x.strip() for x in args.variantes.split(",") if x.strip()):
        if v not in VARIANTES:
            ap.error(f"variante inconnue {v!r}")
        variantes[v] = VARIANTES[v]
    if args.params_mode_vent:
        try:
            variantes["perso"] = json.loads(args.params_mode_vent)
        except json.JSONDecodeError as e:
            ap.error(f"JSON invalide : {e}")
    try:
        graines = [int(g) for g in args.graines.split(",") if g.strip()]
    except ValueError:
        ap.error("--graines : entiers séparés par des virgules")

    os.makedirs(args.sortie, exist_ok=True)
    lignes = []
    print("SIMULÉ — vent, girouette, mât et bateau hypothétiques ; comparer, pas prédire.\n")
    for nom in scenarios:
        scn = banc.SCENARIOS[nom]
        print(f"=== {nom} : {scn.description} (graines {args.graines})")
        print(f"  {'variante':40s}" + " ".join(f"{t:>{len(g.format(0.0))}s}" for _, t, g in COLONNES))
        for nom_v, params in variantes.items():
            try:
                rs = [banc.executer(scn, reglages[args.reglage], g, fusion=args.fusion,
                                    params_mode_vent=params) for g in graines]
            except (TypeError, ValueError) as e:
                print(f"  {nom_v} : refusé — {e}", file=sys.stderr)
                return 2
            moy = {k: sum(r[k] for r in rs) / len(rs) for k, _, _ in COLONNES}
            print(f"  {nom_v:40s}" + " ".join(
                ("—".rjust(len(g.format(0.0))) if math.isnan(moy[c]) else g.format(moy[c]))
                for c, _, g in COLONNES))
            lignes.append({"scenario": nom, "variante": nom_v, "params": json.dumps(params), **moy})
        print()
    chemin = os.path.join(args.sortie, f"essais_vent_{datetime.now():%Y%m%d-%H%M%S}.csv")
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    print(f"Résultats : {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
