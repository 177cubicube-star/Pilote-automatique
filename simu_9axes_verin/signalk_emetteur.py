"""signalk_emetteur.py : envoie l'état du banc simulé à un serveur Signal K.

LECTURE SEULE : ce module publie des mesures pour les AFFICHER (Signal K,
Node-RED, Instrument Panel). Il ne reçoit rien et ne commande rien. Dans
l'architecture DEC-014, les ordres de barre vont directement au serveur de
pypilot (port 23322), jamais par Signal K.

Transport : messages « delta » Signal K en JSON, un par paquet UDP. Côté
serveur, il faut une connexion de données de type « Signal K », sous-type
« UDP », qui écoute le même port (voir README, section Signal K). Vérifié le
2026-11-26 avec signalk-server 2.37.0 dans l'environnement de Claude.

Chemins publiés (unités SI de Signal K : radians, rad/s, ampères, mètres) :

  chemins STANDARD (ce que le pilote « croit », comme le publierait pypilot)
    navigation.headingMagnetic                  cap ESTIMÉ par la fusion
    navigation.rateOfTurn                       lacet estimé (positif vers tribord)
    navigation.attitude                         {roll, pitch, yaw} estimés
    steering.rudderAngle                        angle de barre MESURÉ (potentiomètre)
    steering.autopilot.target.headingMagnetic   consigne de cap

  chemins PROPRES AU BANC (non standard, regroupés sous « simulation. »)
    simulation.truth.headingMagnetic            cap VRAI du bateau simulé
    simulation.truth.roll                       gîte VRAIE
    simulation.truth.rudderAngle                angle de barre RÉEL (après le jeu)
    simulation.headingError                     consigne − cap vrai
    simulation.actuator.command                 commande de vitesse u (−1 à 1)
    simulation.actuator.current                 courant du moteur (A)
    simulation.actuator.position                sortie de la tige (m)

  chemins du VENT (seulement si le scénario simule du vent)
    environment.wind.angleApparent              angle MESURÉ par la girouette (négatif à bâbord)
    environment.wind.speedApparent              vitesse mesurée (m/s)
    steering.autopilot.target.windAngleApparent angle voulu en mode vent
    simulation.truth.windAngleApparent          angle apparent VRAI au pont
    simulation.truth.windDirectionTrue          direction du vent réel (d'où il vient)
    simulation.truth.windSpeedTrue              vitesse du vent réel (m/s)
    simulation.autopilot.mode                   "vent" ou "compas_secours" (texte)

HYPOTHÈSE de signe : steering.rudderAngle positif = la barre fait virer sur
tribord (convention de ce banc). La spécification Signal K lue ne précise pas
le signe ; à confronter avec ce que publie pypilot.

Stdlib seulement.
"""
from __future__ import annotations

import json
import math
import socket
from datetime import datetime, timezone

PORT_DEFAUT = 55561          # port libre choisi dans la plage 49152-65535
SOURCE_DEFAUT = "banc-simu"


def _rad(deg: float) -> float:
    return math.radians(deg)


def construire_delta(etat: dict, source: str = SOURCE_DEFAUT,
                     horodatage: datetime | None = None, exclure=()) -> dict:
    """Transforme l'état du banc (degrés, °/s) en delta Signal K (radians, SI).

    Clés attendues dans `etat` : consigne, cap_estime, cap_vrai, lacet_estime,
    gite_estimee, tangage_estime, gite_vraie, angle_barre_mesure,
    angle_barre_reel, u, courant_a, x_tige_mm."""
    quand = (horodatage or datetime.now(timezone.utc)).isoformat(timespec="milliseconds")
    quand = quand.replace("+00:00", "Z")
    cap = _rad(etat["cap_estime"] % 360.0)
    erreur = (etat["consigne"] - etat["cap_vrai"] + 180.0) % 360.0 - 180.0
    valeurs = [
        ("navigation.headingMagnetic", cap),
        ("navigation.rateOfTurn", _rad(etat["lacet_estime"])),
        ("navigation.attitude", {"roll": _rad(etat["gite_estimee"]),
                                 "pitch": _rad(etat["tangage_estime"]),
                                 "yaw": cap}),
        ("steering.rudderAngle", _rad(etat["angle_barre_mesure"])),
        ("steering.autopilot.target.headingMagnetic", _rad(etat["consigne"] % 360.0)),
        ("simulation.truth.headingMagnetic", _rad(etat["cap_vrai"] % 360.0)),
        ("simulation.truth.roll", _rad(etat["gite_vraie"])),
        ("simulation.truth.rudderAngle", _rad(etat["angle_barre_reel"])),
        ("simulation.headingError", _rad(erreur)),
        ("simulation.actuator.command", etat["u"]),
        ("simulation.actuator.current", etat["courant_a"]),
        ("simulation.actuator.position", etat["x_tige_mm"] / 1000.0),
    ]
    if etat.get("awa_vrai") is not None:
        valeurs += [("simulation.truth.windAngleApparent", _rad(etat["awa_vrai"])),
                    ("simulation.truth.windDirectionTrue", _rad(etat["twd"] % 360.0)),
                    ("simulation.truth.windSpeedTrue", etat["tws"])]
    if etat.get("awa_mesure") is not None:
        valeurs += [("environment.wind.angleApparent", _rad(etat["awa_mesure"])),
                    ("environment.wind.speedApparent", etat["aws_mesure"])]
    if etat.get("angle_voulu") is not None:
        valeurs.append(("steering.autopilot.target.windAngleApparent", _rad(etat["angle_voulu"])))
    for chemin, v in valeurs:
        nombres = v.values() if isinstance(v, dict) else (v,)
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in nombres):
            raise ValueError(f"valeur non finie pour {chemin} : {v!r}")
    if etat.get("mode") is not None:
        valeurs.append(("simulation.autopilot.mode", str(etat["mode"])))
    return {"updates": [{"$source": source, "timestamp": quand,
                         "values": [{"path": c, "value": v} for c, v in valeurs
                                    if c not in exclure]}]}


class EmetteurSignalK:
    """Envoie des deltas par UDP. `imprimer=True` : affiche au lieu d'envoyer.

    Un serveur absent ne bloque pas le banc : les erreurs d'envoi sont comptées
    (`erreurs`), jamais levées."""

    def __init__(self, hote: str = "127.0.0.1", port: int = PORT_DEFAUT,
                 source: str = SOURCE_DEFAUT, imprimer: bool = False, sortie=print):
        if not 0 < port < 65536:
            raise ValueError("port entre 1 et 65535")
        self.adresse = (hote, port)
        self.source = source
        self.imprimer = imprimer
        self.sortie = sortie
        self.envoyes = 0
        self.erreurs = 0
        self.sock = None if imprimer else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.exclure = set()      # chemins à ne plus publier (essai de panne de capteur)

    def publier(self, etat: dict) -> None:
        texte = json.dumps(construire_delta(etat, self.source, exclure=self.exclure),
                           separators=(",", ":"))
        if self.imprimer:
            self.sortie(texte)
            self.envoyes += 1
            return
        try:
            self.sock.sendto(texte.encode("utf-8"), self.adresse)
            self.envoyes += 1
        except OSError:
            self.erreurs += 1

    def fermer(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
