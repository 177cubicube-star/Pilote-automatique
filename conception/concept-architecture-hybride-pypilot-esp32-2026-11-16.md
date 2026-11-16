
# CON-008 — Architecture hybride : pypilot, façade ESP32 et contrôle moteur séparé

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `05 - Concepts/CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé.md` (type `concept`, statut `retenu`). **Retenu comme architecture de départ par la décision DEC-014, acceptée par Mathieu le 2026-11-16** (copie : `decision-architecture-DEC-014-2026-11-16.md`). Copie mise à jour le même jour. Les noms entre « » désignent des notes du vault.

Note de concept. **Retenu le 2026-11-16 comme architecture de départ** par « DEC-014 - Architecture de départ - pypilot hybride, Fenix en repli », avec trois amendements et Fenix en repli. Rien n'est encore testé sur du matériel. Le texte ci-dessous reste celui du concept ; en cas d'écart, la décision fait foi.

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

Dépôts GitHub qui correspondent à cette architecture. Les adresses viennent des notes du vault, sauf les deux dépôts Signal K / Node-RED, vérifiés en ligne le 2026-11-16. Cette liste n'ajoute aucune décision.

**Cœur de l'architecture**

| Dépôt | Rôle |
|---|---|
| [pypilot/pypilot](https://github.com/pypilot/pypilot) | Le cerveau : cap, régulation, modes vent et route. Contient aussi `motor.ino` (`arduino/motor/`), le micrologiciel du contrôle moteur, et dans `hat/` une **télécommande ESP32 en MicroPython** (écran, 7 touches, liaison Wi-Fi seulement) |
| [pypilot/pypilot_schematics](https://github.com/pypilot/pypilot_schematics) | Schémas KiCad des cartes de pypilot. Contient `hbridge_controller`, une carte moteur à fabriquer soi-même (utile pour D-06), et les contrôleurs de moyenne et de forte puissance |
| [pypilot/workbook](https://github.com/pypilot/workbook) | Guide pas à pas de pypilot (installation, câblage du Nano, lecture de `motor.ino`). Dernier commit en juin 2021 : utile, mais daté |
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
| [marcobergman/pypilot_ray](https://github.com/marcobergman/pypilot_ray) | pypilot dans un boîtier Raymarine ST2000 : six touches, un avertisseur et un voyant branchés directement sur les broches du Raspberry Pi, pilotés par un script Python (`ray.py`) qui est un client de pypilot. Utile pour la conversion des ST, et comme modèle de panneau local sans ESP32 |
| [SignalK/signalk-autopilot](https://github.com/SignalK/signalk-autopilot) | Commande, depuis Signal K, des pilotes Raymarine (NMEA 2000, SeaTalk 1) et Simrad. **Ne gère pas pypilot.** Utile seulement comme modèle de chemins de commande |

**Relecture du 2026-11-16.** Les dépôts ci-dessus ont été clonés et lus (pypilot 0.71, commit `5b7b8b0`). Les constats tirés du code sont dans « DEC-014 - Architecture de départ - pypilot hybride, Fenix en repli », section « Preuves ». Rien n'a été essayé.

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
- **Anticipation par le vent** : aucune n'a été trouvée dans la documentation de pypilot (seulement les modes vent apparent et vent réel). Un script sera créé (« DEC-005 - Prévoir un mode vent et une girouette-anémomètre NMEA », option C ; spécification : « CON-009 - Script d'anticipation de la barre par le vent (spécification) »). **Piste pour le point d'injection** *(lue dans le code le 2026-11-16, non essayée)* : pypilot charge automatiquement chaque fichier Python du dossier `pilots/`, et le pilote `basic` tient en une cinquantaine de lignes. Un pilote dérivé de `basic`, avec un terme de vent ajouté à la commande, injecterait la correction sans modifier le cœur de pypilot. Reste inconnu : le comportement réel, à essayer d'abord dans le banc SailSim.
- Machine qui héberge Signal K et Node-RED : Raspberry Pi 4 ou 5 sous OpenPlotter (pypilot, Signal K et Node-RED ensemble, consommation plus élevée), ou Raspberry Pi Zero sous TinyPilot pour pypilot seul, avec Node-RED sur une autre machine (par exemple le PC au banc) pendant le prototype. *Hypothèse non mesurée :* le Pi Zero sous TinyPilot serait trop limité pour les trois ensemble.

## Essais nécessaires

1. Fixer les trois interfaces : façade ↔ pypilot, pypilot ↔ moteur (protocole existant de `motor.ino`), façade ↔ NMEA 2000 (liste des PGN, par exemple 127250 pour le cap et 130306 pour le vent).
2. Développer la façade contre le pypilot simulé du banc SailSim (essais Q1, « Plan_execution_pilote_Capri22_V0-5 »). *Hypothèse :* faisable sans bateau ni vérin.
3. Banc matériel : Raspberry Pi Zero + Nano `motor.ino` + vérin linéaire.

## Issue

**Retenu.** « DEC-014 - Architecture de départ - pypilot hybride, Fenix en repli », acceptée par Mathieu le 2026-11-16. Trois amendements à ce concept :
1. la liaison façade ↔ cerveau est filaire au socle (l'inconnue « Wi-Fi ou série » est tranchée) ;
2. un quatrième bloc, « manœuvres et supervision », tourne sur le Raspberry Pi comme client de pypilot ;
3. le point d'entrée du NMEA 2000 (façade ou carte CAN sur le Raspberry Pi) n'est pas fixé : il se décide avec la machine hôte, par l'essai 1.

Fenix reste le repli ; les conditions de retour sont dans la décision.
