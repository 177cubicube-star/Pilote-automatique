#!/usr/bin/env python3
"""generer_flux_nodered.py : fabrique le flux Node-RED de l'alarme d'écart de cap.

    python generer_flux_nodered.py            # écrit flux_alarme_ecart_cap.json
    python generer_flux_nodered.py --verifier # dit si le fichier JSON est à jour

Le code de l'alarme vient de `alarme_ecart_cap.js` (source unique, testée par
`node --test test_alarme_ecart_cap.js`). Ce script le recopie dans le bloc
« fonction » du flux, avec les réglages en variables d'environnement du bloc
(onglet « Setup » dans Node-RED) : on peut changer seuil et temporisation sans
toucher au code.

Blocs utilisés : ceux de Signal K pour Node-RED (`@signalk/node-red-embedded`,
vérifiés dans la version 2.21.0) et les blocs de base de Node-RED.
Stdlib seulement.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SOURCE_JS = os.path.join(ICI, "alarme_ecart_cap.js")
SORTIE = os.path.join(ICI, "flux_alarme_ecart_cap.json")

# (nom de la variable du bloc, clé du réglage, valeur par défaut)
REGLAGES = (
    ("SEUIL_DEG", "seuil_deg", 20),
    ("TEMPORISATION_S", "temporisation_s", 20),
    ("HYSTERESIS_DEG", "hysteresis_deg", 5),
    ("RETOUR_S", "retour_s", 5),
    ("MANOEUVRE_DEG", "manoeuvre_deg", 5),
    ("MANOEUVRE_MAX_S", "manoeuvre_max_s", 120),
    ("DONNEES_MAX_S", "donnees_max_s", 3),
    ("CONSIGNE_MAX_S", "consigne_max_s", 5),
)

CHEMINS = {
    "navigation.headingMagnetic": "cap",
    "steering.autopilot.target.headingMagnetic": "consigne",
    "steering.autopilot.engaged": "engage",
}

APPEL = """
// ---- appel depuis Node-RED (généré) ----
const lire = (nom, defaut) => {
  const v = env.get(nom);
  return (v === undefined || v === null || v === '') ? defaut : Number(v);
};
let alarme = context.get('alarme');
if (!alarme) {
  try {
    alarme = creerAlarmeEcartCap({
%s
    });
  } catch (erreur) {
    node.status({ fill: 'red', shape: 'ring', text: String(erreur.message || erreur) });
    node.error(erreur, msg);
    return null;
  }
  context.set('alarme', alarme);
}
const t = Date.now() / 1000;
let sorties;
if (msg.topic === 'navigation.headingMagnetic') sorties = alarme.cap(msg.payload, t);
else if (msg.topic === 'steering.autopilot.target.headingMagnetic') sorties = alarme.consigne(msg.payload, t);
else if (msg.topic === 'steering.autopilot.engaged') sorties = alarme.engage(msg.payload, t);
else sorties = alarme.tic(t);
const e = alarme.etat();
node.status(e.alarme ? { fill: 'red', shape: 'dot', text: 'ALARME écart de cap' }
          : e.absence ? { fill: 'red', shape: 'ring', text: 'cap absent' }
          : e.inhibe_jusqua !== null ? { fill: 'blue', shape: 'dot', text: 'manœuvre' }
          : e.debut_depassement !== null ? { fill: 'yellow', shape: 'dot', text: 'au-delà du seuil' }
          : { fill: 'green', shape: 'dot', text: 'veille' });
if (!sorties.length) return null;
return [sorties.map((n) => ({ topic: n.path, payload: Object.assign({ $source: 'alarme-ecart-cap' }, n) }))];
"""


def construire_flux() -> list:
    with open(SOURCE_JS, encoding="utf-8") as f:
        source = f.read()
    lignes = ",\n".join(f"      {cle}: lire('{nom}', {defaut})" for nom, cle, defaut in REGLAGES)
    code = ("// GÉNÉRÉ par generer_flux_nodered.py depuis alarme_ecart_cap.js : "
            "ne pas modifier ici.\n" + source + APPEL % lignes)
    onglet = "a1a1a1a1a1a1a101"
    fonction = "a1a1a1a1a1a1a110"
    notif = "a1a1a1a1a1a1a120"
    debug = "a1a1a1a1a1a1a130"
    noeuds = [{
        "id": onglet, "type": "tab", "label": "Alarme écart de cap (banc)", "disabled": False,
        "info": ("Alarme d'écart de cap du socle, PROTOTYPE sur le banc simulé.\n"
                 "Lit le cap et la consigne dans Signal K, publie des notifications "
                 "(notifications.steering.autopilot.heading ; notifications.navigation.headingMagnetic "
                 "si le cap manque). Ne commande rien.\n"
                 "Réglages : double-clic sur le bloc « Alarme écart de cap », onglet Setup.\n"
                 "Code généré depuis simu_9axes_verin/nodered/alarme_ecart_cap.js."),
    }]
    for i, (chemin, nom) in enumerate(CHEMINS.items()):
        noeuds.append({
            "id": f"a1a1a1a1a1a1a10{i + 2}", "type": "signalk-subscribe", "z": onglet,
            "name": {"cap": "Cap (estimé)", "consigne": "Consigne de cap",
                     "engage": "Pilote engagé (si publié)"}[nom],
            "mode": "sendAll", "flatten": True, "context": "vessels.self", "path": chemin,
            "source": "", "period": "200", "x": 170, "y": 80 + 60 * i, "wires": [[fonction]],
        })
    noeuds += [
        {"id": "a1a1a1a1a1a1a105", "type": "inject", "z": onglet, "name": "Tic 1 s",
         "props": [{"p": "topic", "vt": "str"}], "repeat": "1", "crontab": "", "once": True,
         "onceDelay": "1", "topic": "tic", "x": 150, "y": 260, "wires": [[fonction]]},
        {"id": fonction, "type": "function", "z": onglet, "name": "Alarme écart de cap",
         "func": code, "outputs": 1, "timeout": 0, "noerr": 0, "initialize": "",
         "finalize": "", "libs": [],
         "env": [{"name": nom, "value": str(defaut), "type": "num"} for nom, _, defaut in REGLAGES],
         "x": 450, "y": 170, "wires": [[notif, debug]]},
        {"id": notif, "type": "signalk-send-notification", "z": onglet,
         "name": "Notification Signal K", "path": "", "state": "alarm", "message": "",
         "visual": True, "sound": True, "source": "", "x": 730, "y": 140, "wires": []},
        {"id": debug, "type": "debug", "z": onglet, "name": "Journal des alarmes",
         "active": True, "tosidebar": True, "console": False, "tostatus": False,
         "complete": "payload", "targetType": "msg", "x": 730, "y": 200, "wires": []},
    ]
    return noeuds


def texte_flux() -> str:
    return json.dumps(construire_flux(), ensure_ascii=False, indent=1) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verifier", action="store_true")
    args = ap.parse_args(argv)
    attendu = texte_flux()
    if args.verifier:
        actuel = open(SORTIE, encoding="utf-8").read() if os.path.exists(SORTIE) else ""
        if actuel == attendu:
            print("flux_alarme_ecart_cap.json est à jour.")
            return 0
        print("flux_alarme_ecart_cap.json n'est PAS à jour : relancer sans --verifier.")
        return 1
    with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
        f.write(attendu)
    print(f"Écrit : {SORTIE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
