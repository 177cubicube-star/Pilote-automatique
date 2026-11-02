# Décisions, souhaits et dispositions de conception — session d'exploration du 2026-11-01 au 2026-11-02

Rédigé le 2026-11-02. **Statut : PROPOSITION. Aucune décision n'est VALIDÉE dans ce dépôt.** Ce document consigne ce que Mathieu a **énoncé** pendant la session (DP-01 à DP-03), ses souhaits, et les **dispositions de conception proposées par Claude** (DISP-01 à DISP-16, **non validées par Mathieu**). Il fait autorité sur ces points pour les concepts du même jour ; il ne modifie pas `conception/architecture-pilote-proposition-2026-10-28.md`. Rapprochement avec les règles existantes du vault (L-12, D-05, D-10/G5, reprise manuelle, chien de garde) : proposé, **non fusionné**.

**Non exécuté :** aucune décision n'a été testée ; les dispositions sont des exigences à vérifier, pas des fonctions existantes.

**Rangement :** `conception/`, choix **à confirmer par Mathieu**. Versions du vault : `06 - Décisions/DEC-003`, `DEC-004`, `DEC-005` (une note par décision) ; elles restent au statut `proposee`.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).
---

## 1. Registre

| ID | Énoncé | Date | Statut |
|---|---|---|---|
| DP-01 | Le vérin linéaire est la partie commune du projet ; **Milo sera un projet distinct** si Mathieu décide de le pousser | 2026-11-01 | PROPOSÉE (énoncée par Mathieu) |
| DP-02 | **Prévoir dès la conception** l'évitement automatique de zones (niveau 3) en plus du suivi d'itinéraire OpenCPN ; implantation = chantier ultérieur ; **essais à terre mis de côté** | 2026-11-02 | PROPOSÉE (énoncée par Mathieu) |
| DP-03 | **Prévoir un mode vent** et la réception du NMEA d'une girouette-anémomètre **électronique** (donnée de plus pour la gestion de la barre) ; pas de girouette mécanique ; aucun capteur choisi | 2026-11-02 | PROPOSÉE (énoncée par Mathieu) |
| DISP-01 à DISP-10 | Dispositions pour l'évitement de zones (détail en DP-02) | 2026-11-02 | PROPOSÉE par Claude, **à décider** par Mathieu |
| DISP-11 à DISP-16 | Dispositions pour le vent (détail en DP-03) | 2026-11-02 | PROPOSÉE par Claude, **à décider** par Mathieu |

Les dispositions sont numérotées **1 à 10** et **11 à 16** dans les sections ci-dessous (DISP-nn = disposition n° nn).

## 2. Souhaits et buts exprimés par Mathieu

- **Pouvoir communiquer avec un traceur (par exemple OpenCPN) via NMEA, lac ou non.** « Option fortement souhaitée. »
- **But principal :** marquer les **contours du lac et les hauts-fonds** dans le traceur pour déclencher **une alarme et un changement de direction**. Le suivi d'itinéraire n'est pas le but premier.
- **Accord sur un point de prudence :** suivre un itinéraire ou une zone n'évite pas les obstacles, d'où l'importance du chantier « sécurité et reprise de commande ».
- **État de la session :** exploration à intérêts diversifiés ; aucun choix de plateforme, de joystick ni de dimensionnement n'est demandé ni pris.

## 3. DP-01 — Vérin commun, Milo en projet distinct

#### Contexte
Pendant l'exploration des dépôts open source (`sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`), tous les systèmes étudiés sauf Milo s'organisent autour d'un vérin linéaire. Milo est un régulateur tout-ou-rien sans retour de position, avec une mécanique propre (brevet FR3124791 à vérifier).

#### Décision (énoncée par Mathieu, 2026-11-01)
- **Le vérin linéaire est la partie commune du projet.**
- **Milo sera un projet distinct** si Mathieu décide de le pousser.

Statut dans ce dépôt : **PROPOSÉE** (énoncée par Mathieu en session d'exploration ; elle n'a pas été formalisée comme décision acceptée, ce qui lui revient).

#### Ce que cela ne décide pas
Aucun choix de plateforme (Arduino ou Raspberry Pi), de type de joystick ni de dimensionnement du vérin (course, vitesse, force). Ils dépendent de la longueur de barre, du déplacement du bateau et du type de safran, non encore fournis.

#### Liens
- Cohérent avec les notes du vault « CON-001 - Options actionneur » et « Conception_Pilote_Automatique_V0-3 » (L-12, D-05, à relire avant acceptation).
- Autres décisions de la session : DP-02 (section de ce document), DP-03 (section de ce document).
- État de la session : phase d'**exploration à intérêts diversifiés** ; aucune décision de plateforme n'est demandée.

## 4. DP-02 — Évitement de zones et interface OpenCPN

#### Contexte
Mathieu veut pouvoir marquer les **contours du lac et les hauts-fonds** dans un traceur (par exemple OpenCPN), pour que le système déclenche ensuite **une alarme et un changement de direction**. « Lac ou pas », pouvoir communiquer avec un traceur par NMEA est une **option fortement souhaitée**. Le suivi d'itinéraire n'est pas le but premier : c'est la gestion de **zones**. Développement : `conception/concept-evitement-zones-opencpn-2026-11-02.md`.

#### Décision (énoncée par Mathieu, 2026-11-02)
- **Prévoir dès la conception** la fonction d'évitement automatique de zones (niveau 3 « manœuvre automatique »), **en plus** du suivi d'itinéraire classique avec OpenCPN.
- Son **implantation** fera l'objet d'un **chantier ultérieur de recherche et de codage**. Cela ne décide ni de la plateforme, ni de l'ordre de réalisation, ni des limites de la manœuvre.
- **Les essais à terre (OpenCPN, Signal K) sont mis de côté** : « chantier à faire plus tard ». Voir `essais/zones-opencpn-20261102/README.md`.
- Mathieu a convenu que suivre un itinéraire ou une zone n'évite pas les obstacles, ce qui renforce le chantier « sécurité et reprise de commande ».

Statut dans ce dépôt : **PROPOSÉE** (énoncée par Mathieu en session d'exploration ; elle n'a pas été formalisée comme décision acceptée, ce qui lui revient).

#### Dispositions à prévoir (propositions de Claude, NON validées par Mathieu)
Pour que le niveau 3 reste possible sans être imposé. Raisons détaillées dans `conception/concept-evitement-zones-opencpn-2026-11-02.md` (section 5).

1. Une **source de position et de vitesse** (GPS) accessible à la logique qui compare le bateau aux zones.
2. Une **interface de commande externe** au pilote, acceptant des demandes de changement de cap **bornées** (angle et durée maximaux) et validées.
3. Une **règle de priorité** : toute action humaine (joystick, touche, désengagement) l'emporte sur une demande automatique.
4. Un port **NMEA 0183** réservé : entrée de route (APB), sorties (barre, cap, alarme).
5. Une **sortie d'alarme au poste de barre**, indépendante de l'ordinateur ou de la tablette.
6. Un **état d'évitement** dans la logique des modes, avec conditions d'entrée et de sortie, et journal.
7. Un **chien de garde** : si la logique de surveillance se tait ou si le GPS devient invalide, retour à un comportement sûr et alerte.
8. Un **enregistrement** des mesures et des décisions.
9. Un **adaptateur de source de zones** (OpenCPN, Signal K, fichier).
10. Choix à examiner : logique « gardien » hors du pilote (hypothèse de travail) ou dans le pilote.

Niveaux de réaction (proposition) : 1 alarme seule, 2 alarme au poste de barre, 3 manœuvre automatique limitée, avec un **mode fantôme** intermédiaire (décisions journalisées, aucune commande envoyée). Mathieu a choisi de **prévoir** le niveau 3 ; l'ordre de réalisation reste ouvert.

#### Liens
- Rapprochement avec les règles existantes (non fusionnées) : la note du vault « Conception_Pilote_Automatique_V0-3 » (L-12, D-05, D-10/G5, chien de garde) et la note du vault « Q-004 - Reprise manuelle et protections ». Les dispositions 2, 3 et 7 prolongent ces règles ; elles ne les remplacent pas.
- DP-01 (section de ce document), DP-03 (section de ce document).

#### Reste à décider
Plateforme et architecture du pilote final ; interface de commande (tête physique, joystick ; téléphone refusé comme interface principale d'après les notes antérieures) ; ordre de réalisation des niveaux et limites de la manœuvre automatique ; source des zones à privilégier (plugin OpenCPN, Signal K ou fichier).

## 5. DP-03 — Mode vent et girouette-anémomètre NMEA

#### Contexte
Dernier point de la session d'exploration du 2026-11-02, qui clôt le point « NMEA girouette (windvane) ». Détails techniques et sources : `sources-brutes/point-clos-nmea-girouette-2026-11-02.md`.

#### Décision (énoncée par Mathieu, 2026-11-02)
- La conception doit **prévoir un mode vent**.
- Le système du pilote **reçoit le signal NMEA** de la girouette-anémomètre, qui devient **une donnée de plus pour la gestion du gouvernail** (pas seulement un mode isolé).
- **Pas de girouette mécanique** (régulateur d'allure à pale) : girouette-anémomètre **électronique**.
- **Aucun capteur n'est choisi.**

Statut dans ce dépôt : **PROPOSÉE** (énoncée par Mathieu en session d'exploration ; elle n'a pas été formalisée comme décision acceptée, ce qui lui revient).

#### Dispositions proposées (propositions de Claude, NON validées par Mathieu)
11. Une **entrée NMEA 0183** pour la phrase de vent (MWV), idéalement branchée **directement au pilote** plutôt que via l'ordinateur du traceur.
12. Une **validité des données de vent** avec délai d'expiration : si le vent manque ou devient douteux, retour au mode compas et alerte.
13. Trois usages du vent à distinguer : mode vent (angle de vent), anticipation du moment de lacet (feedforward, coefficients à identifier pour ce bateau), éventuelle alarme de changement de vent plus tard.
14. Un emplacement pour une **correction de la gîte et du mouvement** du vent apparent.
15. **Pas de virement ni d'empannage automatique** par défaut (point de sécurité).
16. Une **calibration** de la girouette dans la procédure de mise en service.

(La numérotation 11 à 16 prolonge les dispositions 1 à 10 de DP-02.)

#### Liens
- la note du vault « Fenix - anticipation du vent (wind feedforward) » (autorité sur le feedforward vent de Fenix et l'issue #13).
- la note du vault « Architecture capteurs et estimation du cap », `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`.
- Rapprochement : la note du vault « Conception_Pilote_Automatique_V0-3 » (D-10/G5).

#### Reste à décider
Choix d'un capteur de vent (sortie NMEA 0183, alimentation, fixation en tête de mât, coût) ; un ou deux ports NMEA 0183 sur le pilote (traceur et girouette) ; si l'anticipation par le vent agit en mode compas.

## 6. À décider (non tranché)

- Plateforme et architecture du pilote final (Arduino ou Raspberry Pi).
- Type de vérin et dimensionnement (longueur de barre, déplacement du bateau, type de safran à fournir).
- Interface de commande (tête physique, joystick ; téléphone refusé comme interface principale d'après les notes antérieures).
- Ordre de réalisation des niveaux de réaction aux zones ; limites de la manœuvre automatique ; source des zones (plugin OpenCPN, Signal K, fichier).
- Capteur de vent (sortie NMEA 0183, alimentation, fixation en tête de mât, coût) ; un ou deux ports NMEA 0183 sur le pilote.
- Acceptation formelle de DP-01 à DP-03 (statut `proposee` dans le vault).
