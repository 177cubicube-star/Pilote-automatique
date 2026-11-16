# DEC-014 — Architecture de départ : pypilot hybride, Fenix en repli

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `06 - Décisions/DEC-014 - Architecture de départ - pypilot hybride, Fenix en repli.md` (type `decision`, statut `acceptee`). **ACCEPTÉE par Mathieu le 2026-11-16.** Non exécuté : rien n'est testé sur du matériel. Les noms entre « » désignent des notes du vault.

## Contexte
« Q-008 - Calculateur et architecture de commande » demande quel calculateur fait tourner le pilote. Deux notes portent les options : « CON-002 - Options calculateur et systèmes de pilotage intégrés » (veille de septembre 2026) et « CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé » (orientation de Mathieu du 2026-11-16, registre R-42). Le recap du 2026-11-16 demande de comparer les deux, de décider, puis de réviser le plan d'exécution en V0-6.

**Constat de cadrage.** CON-002 n'est pas une architecture concurrente. C'est un catalogue de trois familles : acheter un système intégré, concevoir sur microcontrôleur, reprendre pypilot. CON-008 combine deux de ses lignes (Raspberry Pi Zero pour reprendre pypilot, ESP32 comme interface et passerelle). Le concurrent réel est **Fenix**, inscrit au registre D-01 de « Conception_Pilote_Automatique_V0-3 ».

**Changement de périmètre à connaître.** V0.3 liait le choix de la base de code (D-01) et du contrat moteur (D-02) aux portes G3 et G4, donc à une comparaison par essais entre pypilot et Fenix. Le lot Q2 (Fenix en simulation) n'a pas été fait. Cette décision choisit sans cette comparaison. **L'accepter, c'est donc trancher deux lignes du registre V0.3 d'un coup : D-01 et D-02.**

## Options et critères

| Famille | Position proposée | Raison |
|---|---|---|
| Système intégré du commerce (CON-002, A) | Écartée | Système fermé : ni séquences programmables ni anticipation (« DEC-007 - Périmètre fonctionnel du pilote et étapes de réalisation ») ; hors enveloppe de « Q-007 - Usage prioritaire, budget et moyens » |
| Conception propre sur microcontrôleur (CON-002, B : STM32, i.MX RT, Pixhawk) | Écartée comme base | Toute la régulation serait à écrire ; aucun essai ne l'appuie |
| Fenix sur Arduino Mega (D-01) | **Repli** | Jamais essayé dans le banc ; exige un retour de position ; tête de commande à construire |
| Tout pypilot avec son HAT (CON-008, alternative A) | Écartée | Façade non libre, NMEA 2000 indirect ; disponibilité du HAT douteuse (voir Preuves) |
| Tout ESP32 (CON-008, alternative B) | Écartée | pypilot ne tourne pas sur microcontrôleur ; régulation à écrire ou à porter |
| **pypilot hybride (CON-008)** | **Retenue comme départ** | Seule option dont le logiciel réel a tourné dans le banc |

Critères : couvrir le Cahier des besoins ; garder la veille physique indépendante de tout logiciel ; s'appuyer sur une preuve plutôt que sur une préférence ; rester réversible.

## Preuves
- **Essai simulé** (« EXP-005 - Q1 pypilot réel dans SailSim (simulation) ») : le vrai pypilot tient le cap à 0,77° en moyenne avec un vérin idéal, et à 1,67–1,80° avec sa couche servo aux réglages par défaut. Limites : cycle limite d'environ ±3°, un seul scénario calme, profil `default` qui n'est pas le Capri 22, **aucun verdict GO/STOP consigné pour Q1**.
- **Fenix** : aucun essai équivalent (Q2 non réalisé).
- **Commandes de pypilot** *(forum OpenMarine, réponses de l'auteur, 2024 ; non essayé ici)* : barre à un angle donné par `servo.position_command`, pilote en veille (`ap.enabled = False`) ; déplacement manuel par `servo.command` (−1 à +1). Un utilisateur du même fil signale que `servo.position_command` ne déplaçait pas la position chez lui : **à vérifier au banc**. Sources : [fil 4591](https://forum.openmarine.net/showthread.php?tid=4591), [fil 5090](https://forum.openmarine.net/printthread.php?tid=5090).
- **Lecture du code de pypilot** *(version 0.71, commit `5b7b8b0` du 2026-11-16 ; lu, non essayé ; le banc Q1 est figé sur `fdff88f`, à revérifier à ce commit)* :
  - **Arrêt si le cerveau tombe.** `motor.ino` débraye après environ 0,6 s sans commande (compteur à 50 Hz, seuil de 30), et aussi quand son chien de garde se déclenche.
  - **Cycle limite de Q1.** `servo.speed.min` et `servo.speed.max` valent tous deux 100 % par défaut, et sont réglables. Cela confirme l'explication d'EXP-005.
  - **Follow-up et barre bloquée.** `servo.position_command` a sa propre boucle (gains `servo.position.p`, `.i`, `.d`) et s'arrête à moins de 1° de la cible. Elle n'agit que si le retour de barre est valide : le potentiomètre du vérin est donc obligatoire pour ces modes.
  - **Virement.** `ap.tack` existe (délai, angle, vitesse, direction). L'empannage et les séquences programmables n'existent pas.
  - **Protections.** Courant maximal par défaut de 4,5 A côté pypilot (`servo.max_current`), 20 A dans `motor.ino` avant réglage ; seuils de température du contrôleur et du moteur à 60 °C par défaut ; deux entrées de défaut pour les fins de course ; sortie d'embrayage.
  - **Commande par Signal K.** pypilot n'accepte par Signal K que quatre commandes : cap magnétique, cap vrai, mode, engagé. Les commandes de barre (`servo.command`, `servo.position_command`) passent seulement par son propre serveur (port 23322).
  - **Pilotes enfichables.** Chaque fichier du dossier `pilots/` est chargé automatiquement ; `basic` calcule la commande à partir des gains P, D, DD, PR et FF.
- **Dépôts voisins** *(lus le 2026-11-16)* :
  - `pypilot_ray` : touches, avertisseur et voyant sur les broches du Raspberry Pi, et un script client de pypilot (`ray.py`) qui envoie `ap.enabled`, `ap.heading_command` et `servo.command`. C'est un exemple existant du bloc « manœuvres et supervision ».
  - `pypilot/hat` : télécommande ESP32 en MicroPython, en Wi-Fi seulement.
  - `signalk-autopilot` : ne gère pas pypilot.
  - Bibliothèque NMEA 2000 de ttlappalainen : exemples « NMEA 2000 vers NMEA 0183 » et « WindMonitor » ; plages de messages propriétaires prévues (65280 à 65535, 126720, 130816 à 131071).
- **HAT pypilot** *(un seul message de forum, 2025, à vérifier)* : un membre écrit qu'il n'est plus disponible ([fil 6274](https://forum.openmarine.net/printthread.php?tid=6274)).
- **Signal K et machine hôte** : la documentation d'installation de Signal K recommande un Raspberry Pi 4 ou 5 ; un utilisateur rapporte une installation sur Pi Zero 2 W non terminée après 14 heures. Les cartes CAN pour Raspberry Pi figurent parmi les passerelles NMEA 2000 prises en charge ([FAQ Signal K](https://github.com/SignalK/signalk-server/wiki/FAQ:-Frequently-Asked-Questions)).
- **Réponses de Mathieu, 2026-11-16** :
  - sortir la comparaison avec Fenix du chemin critique : « 1- oui » ;
  - finalité : « pas pour commercialisation. produit fini = j'ai quelque chose qui a l'air pro et hyper fonctionnel ».

## Choix accepté
**L'architecture de départ du pilote est CON-008** : pypilot sur Raspberry Pi (cerveau), micrologiciel `motor.ino` sur ATmega328P (contrôle moteur), façade ESP32 (écran, touches). **Fenix reste le repli.** Trois amendements à CON-008 :

1. **Liaison façade ↔ cerveau filaire au socle.** Le Wi-Fi reste réservé à la tablette, au mobile et au PC. Raison : la règle 1 du « Cahier des besoins du pilote » (la veille reprend la main sans liaison sans fil) et « DEC-010 - Ordre de réalisation du socle - panneau local et arrêt matériel d'abord ». La coupure matérielle de la puissance reste hors de tout processeur (« Entrées-sorties du socle », section 7).
2. **Un quatrième bloc est nommé : manœuvres et supervision.** Il porte les séquences programmables, l'homme à la mer, le retour au cap précédent, les alarmes et l'arbitrage des commandes simultanées (boutons contre tablette, DEC-007). C'est un client de pypilot hébergé sur le Raspberry Pi, et non un programme de la façade. Node-RED le prototype (« DEC-006 - Démarche de réalisation, ordre du projet et outil de prototype ») ; sa forme finale n'est pas décidée.
3. **Le point d'entrée du NMEA 2000 n'est pas fixé ici.** Deux voies restent ouvertes : par la façade ESP32 (comme l'écrit CON-008), ou par une carte CAN sur le Raspberry Pi avec Signal K. Le choix se fera par l'essai 1 de CON-008. Il n'est pas urgent : DEC-010 place les liaisons NMEA après le panneau local.
   **Argument pour la carte CAN sur le Raspberry Pi** *(revue du 2026-11-16)* : l'accéléromètre de proue, la bôme et la cellule de charge arrivent par le NMEA 2000, et c'est le bloc « manœuvres et supervision », sur le Raspberry Pi, qui s'en sert. Si le réseau entre par la façade, ces données doivent retraverser la liaison façade ↔ cerveau : il faut un relais à écrire, la façade devient un point de panne pour des données qu'elle n'utilise pas, et un retard s'ajoute (*hypothèse :* faible sur une liaison filaire, à mesurer avant de s'en servir pour l'anticipation). La voie par la façade garde un avantage : elle n'impose pas Signal K sur le Raspberry Pi (voir « Machine hôte »).

## Acceptation
Acceptée par Mathieu le 2026-11-16 (« accepté pour dec014 »), après deux relectures le même jour (lecture des dépôts de référence, puis revue en cinq points).

**Verdict de Q1, donné avec l'acceptation :** « go avec reserve ». Q1 est donc **GO avec réserves** comme preuve pour cette décision. Les réserves sont les limites écrites dans « EXP-005 - Q1 pypilot réel dans SailSim (simulation) » : simulation seulement, un seul scénario calme, profil `default` qui n'est pas le Capri 22, banc partiel, cycle limite d'environ ±3° avec les réglages par défaut.

## Conséquences
- **Registre D-xx de V0.3.** D-01 (base de code) : pypilot. D-02 (contrat contrôleur → moteur) : vitesse native de pypilot ; la position passe par `servo.position_command`. D-03, D-06, D-07, D-08 et D-11 restent ouverts ; le pilote `basic` de pypilot sert de point de départ.
- **Plan d'exécution V0-6.** Le lot Q2 (Fenix en simulation) quitte le chemin critique et devient un lot de repli. Ordre proposé, à fixer dans la V0-6 : banc matériel (Raspberry Pi, Nano `motor.ino`, vérin) avec l'arrêt matériel et le panneau local, puis les liaisons. M1 reste indépendant.
- **Retour de position : exigence nouvelle.** Le follow-up et la barre bloquée sont au socle (DEC-007) et exigent, dans pypilot, un retour de barre valide. **Le vérin doit donc avoir un retour de position, ou la barre un capteur séparé.** « DEC-009 - Gabarit de bateau et exigences minimales du vérin » ne le demande pas : à y ajouter, ou à porter par la réponse à « Q-005 - Retour de position ». Sans retour, cap compas, vent et non-follow-up fonctionnent quand même.
- **Limite de courant.** Le défaut de pypilot est de 4,5 A (`servo.max_current`, réglable jusqu'à 50 A). Un vérin d'au moins 100 lbf peut demander davantage : réglage à faire au banc avec le vérin retenu (lot M2), pas un obstacle.
- **Machine hôte : liée à l'amendement 3.** pypilot et un bloc de manœuvres écrit en Python tiennent sur un Raspberry Pi Zero 2 (TinyPilot le prend en charge ; `pypilot_ray` fonctionne ainsi). Mais Signal K, Node-RED et une carte CAN lue par Signal K demandent en pratique un Pi 4 ou 5. Si Signal K reste dans le système final (carte CAN sur le Pi, zones, OpenCPN), **le Pi Zero 2 devient peu réaliste** et la consommation monte, ce qui pèse sur « Q-006 - Alimentation et autonomie ». *Hypothèse à mesurer :* quelques watts de plus en continu. Le Pi Zero 2 ne reste crédible que si Signal K et Node-RED servent seulement au prototype, sur une autre machine.
- **Trois façons de réaliser le panneau local** (« DEC-010 - Ordre de réalisation du socle - panneau local et arrêt matériel d'abord ») :
  1. touches, avertisseur et voyant sur les broches du Raspberry Pi, comme `pypilot_ray` : aucune liaison à perdre et peu de code, mais pas d'écran, et le Raspberry Pi doit être près du poste de barre, ce qui contraint l'emplacement de l'IMU ;
  2. télécommande ESP32 de pypilot telle quelle : écran et menus existants, mais Wi-Fi seulement, ce qui contredit l'amendement 1 ;
  3. façade ESP32 filaire sur mesure : la cible de cette décision, entièrement à écrire.

  **Proposition pour la V0-6 :** commencer au banc par la façon 1, pour valider le panneau et l'arrêt matériel sans attendre la façade, puis passer à la façon 3. Cela change l'ordre des travaux, pas l'architecture.
- **Séquences et Node-RED.** Les séquences de barre devront parler directement au serveur de pypilot, et non passer par Signal K (voir Preuves).
- **Anticipation par le vent.** Piste de point d'injection : un pilote dérivé de `basic` (voir CON-008 et « CON-009 - Script d'anticipation de la barre par le vent (spécification) »).
- **Notes liées.** CON-008 est passé à `retenu` et renvoie ici ; CON-002 a reçu son issue ; Q-008 pointe vers cette décision et reste ouverte pour la machine hôte et le point d'entrée du NMEA 2000.
- **Licence.** pypilot est sous GPLv3. Le projet n'est pas destiné à la commercialisation (réponse de Mathieu ci-dessus) : aucune action prévue.
- **Restent à décider :** la machine hôte et le point d'entrée du NMEA 2000 (à décider ensemble), la place de Signal K dans le système final, le capteur de retour de position, le driver moteur, le point d'injection de l'anticipation (« CON-009 - Script d'anticipation de la barre par le vent (spécification) »).

## Conditions de réexamen
Revenir à Fenix, ou rouvrir la comparaison, si l'un de ces constats est fait au banc ou en navigation :
- le cycle limite de la couche servo ne descend pas sous la cible de « DEC-013 - Précision de cap visée » avec le vérin réel ;
- le temps de démarrage ou la consommation du Raspberry Pi sont incompatibles avec « Q-006 - Alimentation et autonomie » ;
- `servo.position_command` ne permet pas le follow-up, la barre bloquée et les séquences (plausible à la lecture du code, à condition d'avoir un retour de barre ; reste à essayer) ;
- l'ICM-20948 n'est pas lue de façon fiable par pypilot (« DEC-011 - IMU 9 axes - ICM-20948 »).

« DEC-011 - IMU 9 axes - ICM-20948 » conserve déjà la compatibilité avec Fenix.
