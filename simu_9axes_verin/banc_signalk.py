#!/usr/bin/env python3
"""banc_signalk.py : fait tourner le banc en TEMPS RÉEL et le publie dans Signal K.

À quoi ça sert : regarder le pilote simulé « vivre » dans les outils du bateau
(Data Browser et Instrument Panel de Signal K, Node-RED) avant d'avoir le
matériel, et préparer les écrans et les flux Node-RED sur les mêmes chemins que
publiera pypilot. LECTURE SEULE : rien ne revient de Signal K vers la barre.

Exemples (depuis ce dossier) :

  # voir les messages sans serveur (5 premières secondes)
  python banc_signalk.py --imprimer --duree 5 --vitesse 0

  # publier vers Signal K sur ce PC, en temps réel, scénario vagues
  python banc_signalk.py --scenario vagues --reglage pid_moyen --fusion mahony

  # dix minutes, deux fois plus vite que le réel, en boucle jusqu'à Ctrl+C
  python banc_signalk.py --scenario rafales --duree 600 --vitesse 2 --boucle

Côté Signal K : ajouter une connexion de données « Signal K », sous-type UDP,
port 55561 (voir README). Tout est SIMULÉ.
Stdlib seulement.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import replace

ICI = os.path.dirname(os.path.abspath(__file__))
if ICI not in sys.path:                 # fonctionne aussi avec « python -I »
    sys.path.insert(0, ICI)

import banc  # noqa: E402
from signalk_emetteur import PORT_DEFAUT, SOURCE_DEFAUT, EmetteurSignalK  # noqa: E402


class Cadence:
    """Publie au plus `frequence` fois par seconde (de simulation) et, si vitesse > 0,
    attend pour que 1 s simulée dure 1/vitesse s réelle."""

    def __init__(self, emetteur, frequence_hz: float, vitesse: float,
                 horloge=time.monotonic, dormir=time.sleep):
        if frequence_hz <= 0 or vitesse < 0:
            raise ValueError("fréquence > 0 et vitesse >= 0")
        self.emetteur = emetteur
        self.periode = 1.0 / frequence_hz
        self.vitesse = vitesse
        self.horloge = horloge
        self.dormir = dormir
        self.prochaine = None
        self.depart = None
        self.retard_max_s = 0.0

    couper_cap_a = None

    def __call__(self, etat: dict) -> None:
        t = etat["t"]
        if self.couper_cap_a is not None and t >= self.couper_cap_a:
            self.emetteur.exclure.add("navigation.headingMagnetic")
        if self.prochaine is not None and t + 1e-9 < self.prochaine:
            return
        if self.prochaine is None:
            self.prochaine, self.depart = t, self.horloge() - (t / self.vitesse if self.vitesse else 0)
        self.prochaine += self.periode
        if self.vitesse:
            attente = self.depart + t / self.vitesse - self.horloge()
            if attente > 0:
                self.dormir(attente)
            else:
                self.retard_max_s = max(self.retard_max_s, -attente)
        self.emetteur.publier(etat)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Banc simulé en temps réel vers Signal K (lecture seule).")
    ap.add_argument("--scenario", default="vagues", help="voir : python essais_pid.py --liste")
    ap.add_argument("--reglage", default="pid_moyen", help="un nom de gains_pid.json")
    ap.add_argument("--gains", default=os.path.join(ICI, "gains_pid.json"))
    ap.add_argument("--fusion", default="mahony", choices=sorted(banc.FUSIONS))
    ap.add_argument("--source-gite", default="imu", choices=banc.SOURCES_GITE)
    ap.add_argument("--accel-calibre", action="store_true")
    ap.add_argument("--duree", type=float, help="secondes simulées (défaut : celle du scénario)")
    ap.add_argument("--graine", type=int, default=1)
    ap.add_argument("--vitesse", type=float, default=1.0,
                    help="1 = temps réel, 2 = deux fois plus vite, 0 = aussi vite que possible")
    ap.add_argument("--frequence", type=float, default=5.0, help="messages par seconde simulée (défaut 5)")
    ap.add_argument("--hote", default="127.0.0.1", help="ordinateur du serveur Signal K")
    ap.add_argument("--port", type=int, default=PORT_DEFAUT)
    ap.add_argument("--source", default=SOURCE_DEFAUT, help="nom de la source affiché dans Signal K")
    ap.add_argument("--imprimer", action="store_true", help="affiche les messages au lieu de les envoyer")
    ap.add_argument("--boucle", action="store_true", help="recommence (graine suivante) jusqu'à Ctrl+C")
    ap.add_argument("--couper-cap-a", type=float, metavar="S",
                    help="cesse de publier navigation.headingMagnetic à partir de S secondes "
                         "simulées (essai de l'alarme « cap absent »)")
    args = ap.parse_args(argv)

    if args.scenario not in banc.SCENARIOS:
        ap.error(f"scénario inconnu ; possibles : {', '.join(banc.SCENARIOS)}")
    with open(args.gains, encoding="utf-8") as f:
        reglages = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    if args.reglage not in reglages:
        ap.error(f"réglage inconnu ; possibles : {', '.join(reglages)}")
    scn = banc.SCENARIOS[args.scenario]
    if args.duree:
        if args.duree <= 0:
            ap.error("--duree doit être > 0")
        scn = replace(scn, duree_s=args.duree)
    bruit = (banc.ConfigBruit(ecart_type_biais_accel_g=0.002) if args.accel_calibre
             else banc.ConfigBruit())

    emetteur = EmetteurSignalK(args.hote, args.port, args.source, imprimer=args.imprimer,
                               sortie=lambda x: print(x, flush=True))
    cible = "affichage seulement" if args.imprimer else f"UDP {args.hote}:{args.port}"
    if not args.imprimer:
        print(f"SIMULÉ — {scn.nom} / {args.reglage} / {args.fusion} / gîte {args.source_gite} "
              f"→ {cible}, {args.frequence:g} messages/s, vitesse ×{args.vitesse:g}. Arrêt : Ctrl+C")
    graine = args.graine
    try:
        while True:
            cadence = Cadence(emetteur, args.frequence, args.vitesse)
            cadence.couper_cap_a = args.couper_cap_a
            emetteur.exclure.clear()
            r = banc.executer(scn, reglages[args.reglage], graine, fusion=args.fusion,
                              source_gite=args.source_gite, bruit_imu=bruit, observateur=cadence)
            if not args.imprimer:
                p95 = ("n/d (moins de 20 s mesurées)" if r["erreur_p95_deg"] != r["erreur_p95_deg"]
                       else f"{r['erreur_p95_deg']:.2f}°")
                print(f"  graine {graine} : p95 {p95}, {emetteur.envoyes} messages envoyés, "
                      f"{emetteur.erreurs} erreurs d'envoi"
                      + (f", retard max {cadence.retard_max_s:.2f} s" if cadence.retard_max_s > 0.05 else ""))
            if not args.boucle:
                break
            graine += 1
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        emetteur.fermer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
