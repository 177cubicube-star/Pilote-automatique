
# CON-008 — Architecture hybride : pypilot, façade ESP32 et contrôle moteur séparé

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `05 - Concepts/CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé.md` (type `concept`, statut `exploratoire`). C'est une **orientation**, pas une décision : aucune DEC ne l'accepte. Copie mise à jour le même jour : ajout de la section « Dépôts de référence ». Les noms entre « » désignent des notes du vault.

Note de concept. Rien n'est testé, rien n'est choisi. Mathieu a dit **pencher** pour cette architecture le 2026-11-16. C'est une orientation, pas une décision : aucune note DEC ne l'accepte.

## Provenance et relations

- Session du 2026-11-16 (Claude Project « pilote automatic »). L'idée est née en préparant la conversion des ST1000+/ST2000+, puis Mathieu l'a ramenée au pilote principal.
- Ordre de travail reconfirmé le même jour : le pilote est d'abord construit avec le vérin linéaire ; l'adaptation au ST vient ensuite (décision L-12 du 2026-10-30, voir « Journal de mise en place »).
- Question concernée : « Q-008 - Calculateur et architecture de commande ». Options déjà repérées : « CON-002 - Options calculateur et systèmes de pilotage intégrés ».
- Ordre convenu le 2026-11-06 : établir d'abord « grille-capacites-pilote », puis choisir le calculateur. Cette note **ne court-circuite pas** cet ordre ; elle ajoute une candidate.
- Références : « six-projets-pilotes-barre-detail », « Dépôts open source de pilotes - validation et analyse technique », « Interface moteur et boutons - carte Q218 ST1000+ ST2000+ ».

## Problème

Il faut un calculateur et une interface pour le pilote principal (vérin linéaire), avec une option NMEA 2000. Mathieu veut aussi pouvoir réutiliser le même système plus tard pour convertir un ST1000+/ST2000+, ou pour commander tout autre vérin.

## Solution candidate

Trois blocs séparés :

1. **Cerveau : pypilot** sur Raspberry Pi (TinyPilot ou OpenPlotter), gardé tel quel. Il calcule le cap et la régulation, suit une route (phrases APB) et gère le mode vent (NMEA 0183 ou Signal K).
2. **Contrôle moteur : micrologiciel `motor.ino` de pypilot** sur ATmega328P (Arduino Nano). Il mesure le courant, la tension et deux températures (contrôleur et moteur). Il a une entrée d'angle de barre, deux entrées de fin de course et un chien de garde.
3. **Façade : ESP32**, qui porte l'écran, les touches et une passerelle NMEA 2000 (au socle, avec une entrée NMEA 0183, choix de Mathieu du 2026-11-16) (bibliothèque ttlappalainen avec un émetteur-récepteur CAN externe). Elle parle à pypilot par son interface réseau, avec des commandes du type `ap.heading_command=180`.

**Outil de prototype : Node-RED intégré à Signal K** *(confirmé par Mathieu le 2026-11-16, dans la ligne de la décision du 2026-11-07 sur Node-RED)*. Raison rappelée par Mathieu : la facilité de tester. Le serveur Signal K dispose d'un module officiel (`signalk-node-red`) qui embarque Node-RED, sans installation séparée, avec des blocs Signal K prêts à l'emploi. Des scripts Python restent possibles pour des essais automatisés précis. Cela ne décide pas si Node-RED reste dans le système final.

**Raison donnée par Mathieu :** une même architecture sert à n'importe quel type de pilote ou de commande de vérin linéaire. C'est un « 2 pour 1 ».

| Brique | Pilote principal (vérin linéaire) | Conversion ST (plus tard) |
|---|---|---|
| Cerveau pypilot | Identique | Identique |
| IMU | Identique | Identique |
| Façade ESP32 | Tête de commande séparée | Intégrée au boîtier ST |
| `motor.ino` | Potentiomètre du vérin sur l'entrée d'angle de barre | Sans retour de position, fins de course à ajouter |

## Dépôts de référence *(ajout du 2026-11-16, à la demande de Mathieu)*

Dépôts GitHub qui correspondent à cette architecture. Les adresses viennent des notes du vault, sauf les deux dépôts Signal K / Node-RED, vérifiés en ligne le 2026-11-16. Cette liste n'ajoute aucune décision : l'architecture reste une orientation.

**Cœur de l'architecture**

| Dépôt | Rôle |
|---|---|
| [pypilot/pypilot](https://github.com/pypilot/pypilot) | Le cerveau : cap, régulation, modes vent et route. Contient aussi `motor.ino` (`arduino/motor/`), le micrologiciel du contrôle moteur |
| [pypilot/pypilot_schematics](https://github.com/pypilot/pypilot_schematics) | Schémas de la carte moteur de pypilot |
| [pypilot/workbook](https://github.com/pypilot/workbook) | Documentation de pypilot |
| [ttlappalainen/NMEA2000](https://github.com/ttlappalainen/NMEA2000) | Bibliothèque NMEA 2000 pour la façade ESP32 et les nœuds de capteurs |
| [SignalK/signalk-node-red](https://github.com/SignalK/signalk-node-red) | Module du serveur Signal K qui embarque Node-RED (outil de prototype, DEC-006) |
| [SignalK/node-red-embedded](https://github.com/SignalK/node-red-embedded) | Les blocs Signal K utilisables dans ce Node-RED embarqué |

**Banc de simulation**

| Dépôt | Rôle |
|---|---|
| [herostrat/sailsim](https://github.com/herostrat/sailsim) | Simulateur SailSim des essais Q0 et Q1 (« EXP-002 - Qualification Q0 SailSim (run001) », « EXP-005 - Q1 pypilot réel dans SailSim (simulation) ») |

**Références et repli**

| Dépôt | Rôle |
|---|---|
| [spascual90/Fenix](https://github.com/spascual90/Fenix) | Référence à vérin linéaire, repli possible, source de l'anticipation par le vent (« CON-009 - Script d'anticipation de la barre par le vent (spécification) », issue #13) |
| [spascual90/Fenix-User-Handbook](https://github.com/spascual90/Fenix-User-Handbook) | Manuel de Fenix |
| [marcobergman/pypilot_ray](https://github.com/marcobergman/pypilot_ray) | pypilot dans un boîtier Raymarine : utile pour la conversion des ST |
| [SignalK/signalk-autopilot](https://github.com/SignalK/signalk-autopilot) | Commande d'un pilote depuis Signal K |

Les autres dépôts étudiés (YAAAP, Plot Device, KastB, Jack Edwards, Milo, SimplePilot) restent dans « six-projets-pilotes-barre-detail » et « Dépôts open source de pilotes - validation et analyse technique ».

## Alternatives

- **A — Tout pypilot** : Raspberry Pi + `motor.ino` + pypilot_hat (écran et boutons). Le NMEA 2000 passe par Signal K et une carte CAN. Plus simple, mais la façade n'est pas libre et le NMEA 2000 reste indirect.
- **B — Tout ESP32** : un seul microcontrôleur fait le cerveau, l'écran et le NMEA 2000. Compact, mais la régulation est à écrire ou à porter : pypilot ne tourne pas sur un microcontrôleur (constat de son auteur sur l'ESP8266), et Fenix tourne sur Mega et suppose un capteur de position.
- **Fenix** reste une référence étudiée (« SRC-001 - Fenix code source »).

## Critères

- Couvrir les capacités retenues dans « grille-capacites-pilote ».
- Rester sûr si un des trois processeurs tombe : le moteur s'arrête, l'alarme est visible.
- Consommation compatible avec le budget énergétique (« Q-006 - Alimentation et autonomie »).
- **Facilité d'adaptation future au ST** (garde-fou proposé, non exigé) : contrôle moteur qui fonctionne avec ou sans retour de position, entrées de fin de course, mesure du courant réglable pour un petit moteur, tête de commande séparée du contrôle moteur.

## Inconnues

- Liaison façade ↔ pypilot : Wi-Fi (plus simple) ou série filaire (plus robuste) ?
- Comportement en cas de perte du Raspberry Pi ou de la façade, et temps de démarrage du Raspberry Pi (non mesuré).
- Consommation réelle : environ 0,9 à 1,4 W pour le calculateur pypilot selon « six-projets-pilotes-barre-detail » (calcul, avant les pertes du convertisseur).
- Réglage du courant maximal de `motor.ino` : la valeur par défaut lue dans le code est de 20 A, la bonne valeur pour chaque moteur reste à déterminer.
- Ce que la façade ESP32 apporte réellement face à pypilot_hat : NMEA 2000 natif, écran au choix, intégration dans un boîtier.
- Effet du positionnement de l'IMU près des aimants du moteur (hypothèse à vérifier).
- **Anticipation par le vent** : aucune n'a été trouvée dans la documentation de pypilot (seulement les modes vent apparent et vent réel). Un script sera créé (« DEC-005 - Prévoir un mode vent et une girouette-anémomètre NMEA », option C ; spécification : « CON-009 - Script d'anticipation de la barre par le vent (spécification) »). Inconnue : le point d'injection dans pypilot, car une correction de barre ne se transmet pas proprement par la consigne de cap ; une modification de pypilot pourrait être nécessaire.
- Machine qui héberge Signal K et Node-RED : Raspberry Pi 4 ou 5 sous OpenPlotter (pypilot, Signal K et Node-RED ensemble, consommation plus élevée), ou Raspberry Pi Zero sous TinyPilot pour pypilot seul, avec Node-RED sur une autre machine (par exemple le PC au banc) pendant le prototype. *Hypothèse non mesurée :* le Pi Zero sous TinyPilot serait trop limité pour les trois ensemble.

## Essais nécessaires

1. Fixer les trois interfaces : façade ↔ pypilot, pypilot ↔ moteur (protocole existant de `motor.ino`), façade ↔ NMEA 2000 (liste des PGN, par exemple 127250 pour le cap et 130306 pour le vent).
2. Développer la façade contre le pypilot simulé du banc SailSim (essais Q1, « Plan_execution_pilote_Capri22_V0-5 »). *Hypothèse :* faisable sans bateau ni vérin.
3. Banc matériel : Raspberry Pi Zero + Nano `motor.ino` + vérin linéaire.

## Issue

**Décision proposée le 2026-11-16 :** « DEC-014 - Architecture de départ - pypilot hybride, Fenix en repli ». Elle retiendrait ce concept comme architecture de départ, avec trois amendements : liaison façade ↔ cerveau filaire, quatrième bloc « manœuvres et supervision » sur le Raspberry Pi, point d'entrée du NMEA 2000 laissé à l'essai 1. Tant qu'elle n'est pas acceptée, le statut reste `exploratoire` et la propriété `decision` reste vide.

Non tranchée. Si le concept est retenu, renseigner `decision` avec le lien vers une décision acceptée. S'il est écarté, écrire ici la raison.
