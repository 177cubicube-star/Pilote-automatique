# Fenix vs pypilot — rapport de la discussion (régulation, vérin, montage)

Rédigé le 2026-10-28 à partir d'une discussion avec Mathieu. Cette fiche **consigne** ce qui a été lu, calculé et
simulé ; elle ne tranche rien. Le plan de test correspondant est dans
`pilote-fenix-vs-pypilot-plan-de-tests-2026-10-28.md` (même dossier).

**Non exécuté sur du vrai matériel ni avec le vrai firmware :** rien n'a été compilé, téléversé ni essayé sur le bateau.
Les dépôts ont été lus (clones superficiels), jamais lancés. Les « résultats » ci-dessous viennent de deux
**simulations Python écrites pour l'occasion**, qui sont des portages de ma lecture du code — pas le code d'origine.

Légende (celle du projet, plus une entrée) :
**CONFIRMÉ** = lu dans le code ou fourni par Mathieu · **SIMULÉ** = résultat d'un de mes modèles Python (valable seulement
dans les limites du § 8) · **INFÉRENCE** = déduit de ce qui a été lu · **HYPOTHÈSE** = valeur supposée, non vérifiée ·
**À VÉRIFIER** = question ouverte.

---

## 1. Ce que Mathieu cherchait

1. Cloner et analyser Fenix et pypilot, et comprendre leurs différences **fondamentales** et **techniques**.
2. Détailler le calcul de barre de Fenix (`PID_ext::Compute`) et le passage « erreur de cap → commande servo »
   de pypilot (`servo.py`).
3. Simuler la régulation de chacun pour tester les points douteux (surtout le « facteur de vitesse » de Fenix).
4. Comprendre l'aspect **vitesse du vérin** de pypilot et voir s'il peut s'intégrer à Fenix.
5. Vérifier ce que cela donne avec son vérin et son montage réels.

Conclusion de Mathieu en fin de séance : la discussion lui donne bien l'information générale recherchée ; aucune
décision de conception n'a été demandée ni prise.

## 2. Sources lues

| Dépôt | Commit lu | Date du commit | Remarque |
|---|---|---|---|
| `spascual90/Fenix` | `b8410e50fa19` | 2026-10-23 | clone superficiel |
| `pypilot/pypilot` | `fdff88ffe59c` | 2026-10-07 | clone superficiel, version 0.71 |

Fichiers Fenix lus : `Fenix.ino`, `Autopilot.cpp/.h`, `ActuatorManager.cpp/.h`, `ActuatorController.cpp/.h`,
`libraries_ext/PID_v1_ext.cpp/.h`, `OnlineNomotoIdentifier.cpp`, `FossenReferenceModel.h`, `WavePassiveObserver.h`,
`WindFeedforward.h`, `Fenix_config.h`, `BT.h`, `BT.cpp`, `IF_NMEA.cpp`.
Fichiers pypilot lus : `autopilot.py`, `pilots/*.py` (dont `basic.py`), `servo.py`, `boatimu.py`, `server.py`, `values.py`,
`sensors.py`, `rudder.py`, `arduino/motor/*`.

## 3. Différences fondamentales

| Axe | Fenix | pypilot |
|---|---|---|
| Plateforme | Arduino (Mega 2560 / Uno R4 WiFi), C++, **un seul fil d'exécution** | Raspberry Pi, Python, **plusieurs processus** autour d'un serveur de valeurs (TCP 23322) |
| Type de commande | **Position** de barre : le PID calcule un angle cible, le vérin y est ramené grâce au potentiomètre | **Vitesse** de barre : la commande est une vitesse envoyée au servo (forme dite « de vitesse », velocity form) |
| Capteur de cap | IMU ICM-20948, filtre Mahony dans le firmware | IMU via RTIMULib (fusion de Kalman, type 1), calibration automatique |
| Réglage | Modèle de bateau (Nomoto T, K) **identifié en ligne** (RLS), modèle de référence de Fossen, observateur de vagues, anticipation du vent | Gains **empiriques** (P, D, DD, PR, FF), pas de modèle de bateau dans le pilote `basic` ; pilotes `basic`, `absolute`, `wind` actifs |
| Interfaces | Application Bluetooth (Virtuino), NMEA, PEMC | SignalK, NMEA, gpsd, interface web |
| Moteur | Pilote PWM + DIR (Cytron MD10C recommandé dans le projet) | Firmware `motor.ino`, série avec CRC8, surveillance courant / tension / température |

Les entrées de ce tableau sont **CONFIRMÉES** par lecture du code, sauf la mention du driver Cytron, qui vient de
`fenix-imu-actionneur-lecture-2026-10-28.md`.

## 4. Fenix — `PID_ext::Compute`

**CONFIRMÉ** (lecture) :

- Gains par défaut : Kp 3,5 / Ki 0,1 / Kd 3,0 ; sens inversé (REVERSE) ; échantillonnage 100 ms.
- Unités de barre : dixièmes de degré ; `maxRudder` = 350 (soit ±35°).
- Protections : anti-windup (anti-emballement de l'intégrale), intégrale activée seulement près de la cible, dérivée filtrée
  (passe-bas).
- **Facteur de vitesse** `factor` : Kp et Ki sont multipliés par `factor²`, Kd est divisé par `factor`, et la limite de
  sortie est multipliée par `min(factor², 1)`.
- Ce facteur est **plafonné** par `fmin(factor, abs(outMax / (kp × MAX_PID_TURN)))`. Aux gains par défaut ce plafond vaut
  **1,0** : le facteur ne dépasse donc jamais 1.
- Nomoto par défaut : T = 2,26 s, K = 0,19 (voilier de 12 m, d'après les valeurs par défaut du code). Avec la vitesse :
  Teff = T / f, Keff = K · f.

**Correction d'une affirmation antérieure.** Une première explication affirmait que « le gain augmente avec la vitesse ».
C'était faux : j'avais oublié le plafond ci-dessus. En réalité le facteur ne fait que **réduire** les gains à basse vitesse.

**À VÉRIFIER** : que la dérivée du code est bien celle que j'ai portée (filtre « tel que codé » : kd réel 0,06 au lieu
de 0,30 dans ma simulation de contrôle ; voir S3).

## 5. pypilot — du cap au servo

**CONFIRMÉ** (lecture de `basic.py` et `servo.py`) :

- Pilote `basic` : commande = P·erreur + D·vitesse de rotation + DD·accélération de rotation + PR·signe·√|erreur|
  + FF·variation de consigne. Gains par défaut : P 0,003, D 0,09, DD 0,075, PR 0,005, FF 0,6.
- Erreur limitée à ±30° ; filtres 0,2 / 0,2 / 0,1 ; boucle à 20 Hz par défaut.
- **INFÉRENCE** : comme la commande est une vitesse, le terme P agit comme un intégrateur, D comme un proportionnel, DD comme
  une dérivée.
- `servo.py`, mécanisme « période / windup » : le servo ne suit pas la vitesse demandée en continu. Il accumule la
  demande ; quand l'accumulation dépasse un seuil, il lance une impulsion d'au moins `period` (0,4 s par défaut) à une
  vitesse entre `speed.min` et `speed.max` (**100 % pour les deux par défaut**). Résultat : des impulsions à pleine
  vitesse, d'une durée minimale de 0,4 s.
- Polynôme caractéristique de la boucle (servo idéal) :
  `T s³ + (1 + K·V·DD) s² + K·V·D s + K·V·P = 0`, où V est la vitesse du vérin en °/s de barre.

## 6. Résultats de simulation — Fenix (script `fenix_pid_sim.py`)

Modèle : bateau de Nomoto (T = 2,26 s, K = 0,19), PID porté de `PID_ext::Compute`, vérin simulé à 7 °/s.
Validation S0 : le banc reproduit la théorie linéaire (système suramorti, aucun dépassement).

**SIMULÉ** :

| Point testé | Résultat |
|---|---|
| Facteur de vitesse tel que codé (S1, écart de 5°) | À basse vitesse la régulation est **plus lente et plus oscillante** que sans facteur : à f = 0,4, dépassement 67,9 % (contre 45,5 % sans facteur) et retour sous 1° en plus de 600 s (contre 154 s) |
| Variante « inverse » (gains divisés par f², hypothèse) | Meilleur comportement à basse vitesse (retour sous 1° en 38 s à f = 0,4), mais barre beaucoup plus active (238 °/min) |
| Kp au-delà de 3,5 (S2) | Le plafond fait **baisser** le Kp effectif (12,25 / Kp) et réduit la limite de barre : à Kp = 5, limite 17,1° ; à Kp = 10, limite 4,3° |
| Dérivée précédente (S3) | La variable `_kdContrib_prev` n'est jamais mise à jour dans le code, mais l'effet dans mon modèle est négligeable (écart de cap RMS 1,24° contre 1,30°) |
| Bande morte (S4) | Implémentée comme un **décalage** : cap final décalé de +0,50° pour une bande morte de 0,5° (+0,00° sans). L'appel `calcDeadband` est en commentaire dans le code lu |

**À VÉRIFIER** : tout ceci décrit mon modèle. Le bon test est de rejouer ces cas avec le firmware réel en mode `SHIP_SIM` /
`VIRTUAL_ACTUATOR` (définis dans `Fenix_config.h`, lignes 81–82, actuellement en commentaire) ou de demander à l'auteur.

## 7. Résultats de simulation — pypilot (script `pypilot_sim.py`)

Même bateau, pilote `basic` aux gains par défaut, servo « réel » (portage de `do_command`) ou « idéal ». V = 7 °/s sauf
indication. Validation S0 : la simulation du servo idéal reproduit la théorie linéaire exacte.

**SIMULÉ** :

| Point testé | Résultat |
|---|---|
| Servo idéal vs servo réel (S1, f = 1,0) | Idéal : dépassement 9,1 %, retour sous 1° en 25 s, écart de cap RMS 0,05°. Réel : dépassement 29,7 %, retour sous 1° en ~594 s, RMS 0,56° |
| Taille de l'impulsion (« quantum ») | ≈ 3,0° de barre aux réglages par défaut (V × période = 7 × 0,4) ; le cap oscille en permanence (cycle limite) |
| Sensibilité à la vitesse du vérin V (S2, servo réel) | V = 3 : 22,0 % ; V = 7 : 29,7 % ; V = 12 : 54,8 % ; V = 20 : 73,8 %. Les gains ne sont **pas normalisés** par V |
| Réglage du servo (S3) | Période 0,1 s / `speed.min` 30 % : impulsion 0,27°, RMS 0,07°. Période 0,4 s / 100 % : impulsion 3,02°, RMS 0,56° |
| Aucune variation des gains avec la vitesse du bateau | Servo idéal : dépassement 38,0 % → 2,8 % quand f passe de 0,4 à 1,6. Servo réel : 30 à 46 % |
| Anticipation FF (S4, +20°) | Dépassement 6,3 % avec FF = 0,6 contre 11,4 % avec FF = 0 |

## 8. Limites des simulations

- **HYPOTHÈSE** : vitesse du vérin V = 7 °/s (voir § 10 : le calcul avec le montage de Mathieu donne 5,6 à 7,4 °/s,
  donc cette hypothèse est proche).
- **HYPOTHÈSE** : bateau de 12 m (T = 2,26 s, K = 0,19 par défaut dans Fenix). Le voilier de Mathieu (Catalina Capri 22)
  est plus petit et probablement plus réactif ; les valeurs de T et K sont **inconnues**.
- Bruit de cap supposé (0,2°) et de vitesse de rotation (0,1°/s) : valeurs de ma main, non mesurées.
- Pas de vagues, pas de limitation de vitesse du firmware, pas de jeu mécanique, servo parfaitement calibré.
- Le servo « réel » de pypilot est mon portage de `do_command` ; il ne tient pas compte du firmware `motor.ino`.
- Côté Fenix, le vérin est simulé sans les rampes ni les paliers de vitesse du vrai code (les simulations Fenix ne
  testent que la loi de commande, avec un vérin idéal à bande d'arrêt de 0,7° sauf mention S1/S4 ; **valeur corrigée au § 14.2** : le code suggère plutôt ≈ 0,3°).

## 9. Vérin : ce que fait déjà Fenix, et pistes

**CONFIRMÉ** (lecture de `ActuatorManager.cpp`, `ActuatorController.cpp`, `Fenix_config.h`) :

- Pilotage PWM (`analogWrite`, 0–255) + direction. `SPEED_CRUISE` = 255.
- Choix de la vitesse selon l'écart de barre : grand écart → 255 ; petit écart et vérin déjà en mouvement → 255/3
  (≈ 85) ; petit écart et vérin à l'arrêt → il reste arrêté (seuil de redémarrage).
- Rampes : la vitesse change de 5 par appel (accélération et freinage) ; sous 5, elle est mise à 0.
- Le code appelle `setSpeed(new_speed, true)` (mode « immédiat ») : le filtre interne de `setSpeed` est contourné.

**À VÉRIFIER** : la fréquence d'appel de `controlActuator` (conditionne la durée réelle des rampes) et le PWM minimum
auquel le vérin démarre.

Pistes envisagées (**propositions**, non validées) :

| Piste | Principe | Risque |
|---|---|---|
| A | Remplacer les deux paliers 255 / 85 par une vitesse **proportionnelle** à l'écart, avec minimum et maximum | Faible ; demande de connaître le PWM minimum de démarrage |
| B | Normaliser les gains par la vitesse **mesurée** du vérin (°/s) | Moyen ; demande une mesure fiable et filtrée |
| C | Limiter la vitesse de variation de la barre cible (« slew rate ») avant le PID | Faible à moyen ; le modèle de référence de Fossen en fait déjà une partie (À VÉRIFIER) |

Recommandation formulée dans la discussion : commencer par A, garder C en réserve, ne pas toucher à B avant d'avoir
mesuré la vitesse réelle. **Statut : PROPOSITION, non décidée.**

## 10. Matériel et montage de Mathieu

### 10.1 Vérin — fiche technique fournie par Mathieu (**CONFIRMÉ**, copie d'écran)

Modèle FA-HF-100-12-XX : poussée dynamique 100 lb, statique 180 lb ; vitesse 3 po/s à vide, 2,5 po/s à pleine charge ;
**cycle de service 20 %** ; vis à vis sans fin (worm gear) ; 12 V CC ; 10 A à pleine charge (courbe : environ 1 A à
vide, linéaire jusqu'à 10 A à 100 lb) ; **aucun retour de position** ; variation de vitesse de 5 à 10 % ; fins de course
intégrés ; IP66 ; câble de 1,5 pi. La course (le « XX ») n'est pas connue.

### 10.2 Montage selon la recommandation Raymarine ST1000+ (**CONFIRMÉ** : cotes données par Mathieu ; leur source web n'a pas été vérifiée)

| Cote | Valeur |
|---|---|
| Axe de la mèche → trou de fixation sur la barre | 589 mm |
| Longueur du vérin en veille (entraxe) | 610 mm |
| Distance perpendiculaire du point fixe à l'axe de la barre | 460 mm |
| Extension | 170 mm (rôle exact **À VÉRIFIER** : rallonge de tige ou de téton) |

### 10.3 Calculs (**INFÉRENCE**, arithmétique à refaire sur les vraies cotes)

Si le vérin pousse perpendiculairement à la barre, la vitesse de barre est la vitesse linéaire divisée par 589 mm :

| Cas | Vitesse linéaire | Vitesse de barre |
|---|---|---|
| À vide | 3 po/s = 76,2 mm/s | ≈ 7,4 °/s |
| À pleine charge | 2,5 po/s = 63,5 mm/s | ≈ 6,2 °/s |

Conséquences :

- C'est proche de l'hypothèse V = 7 °/s des simulations : les résultats des § 6 et 7 s'appliquent assez directement,
  **au bateau près** (§ 8).
- Un cycle Fenix de 100 ms à pleine vitesse déplace la barre d'environ 0,74° (≈ 0,25° à un tiers de vitesse), du même
  ordre que la bande d'arrêt du code (0,7° dans ma première lecture, ≈ 0,3° d'après la lecture corrigée du § 14.2).
- Avec pypilot aux réglages par défaut, l'impulsion minimale vaut ≈ 3° de barre (7,4 × 0,4).
- Course nécessaire : déplacement du téton ≈ 589 × sin(angle de barre) ; soit ≈ ±201 mm pour ±20° et ≈ ±295 mm pour ±30°.

**Incohérence des cotes, non résolue.** Si le vérin est perpendiculaire à la barre au centre, sa longueur devrait être
460 mm, pas 610 mm. Avec Pythagore (610 et 460), le point fixe serait à ≈ 401 mm le long de la barre, vérin oblique de
≈ 41° ; la vitesse de barre tomberait alors à ≈ 5,6 °/s (7,4 × 460/610). Autre explication possible : 610 inclut l'extension de
170 mm (610 − 170 = 440 mm, proche de 460 mm). **À VÉRIFIER** par une mesure sur le bateau (test M1 du plan de tests).

### 10.4 Cycle de service

**HYPOTHÈSE** : un pilote qui corrige souvent à pleine vitesse peut dépasser 20 % de temps de marche, surtout par mer
formée. Réduire la vitesse et élargir la zone morte diminue ce temps. Aucune mesure ne permet de le confirmer
(test M6).

## 11. Décisions, propositions et points ouverts

**Décisions validées :** aucune.

**Propositions (non validées) :** pistes A, B, C (§ 9) ; rejouer les cas de simulation avec `SHIP_SIM` /
`VIRTUAL_ACTUATOR` ; signaler à l'auteur de Fenix les points du § 6 après vérification.

**Points ouverts :**

1. Quel vérin est réellement monté (Raymarine d'origine ou Firgelli) ? Mathieu a répondu en substance « c'est bon comme cela » ;
   la question reste donc ouverte, sans urgence.
2. Course totale du vérin et rôle exact de l'extension de 170 mm.
3. PWM minimum de démarrage et vitesse réelle du vérin en °/s (tests M2, M3).
4. T et K du Catalina Capri 22 (test M7 ou identification en ligne de Fenix).
5. Les cotes 589 / 610 / 460 mm ne se recoupent pas (§ 10.3).

## 12. Fichiers produits pendant la discussion

| Fichier | Rôle | Dans ce dépôt ? |
|---|---|---|
| `fenix_pid_sim.py` | Simulation de la régulation Fenix (scénarios S0–S4), figure `fenix_pid_sim.png` | Non — livré dans la conversation |
| `pypilot_sim.py` | Simulation de la régulation pypilot (scénarios S0–S4), figure `pypilot_sim.png` | Non — livré dans la conversation |
| `comparaison_pilotes.py` | Banc commun Fenix / pypilot : mêmes bateau, vérin, limite de barre, perturbations ; cinq indicateurs (§ 14). Importe les deux scripts ci-dessus (même dossier). Figure `comparaison_pilotes.png` | Non — livré dans la conversation |

Les scripts ne dépendent que de `numpy` (et de `matplotlib` pour les figures). Pour que le plan de tests soit rejouable
depuis le dépôt, il faudra les y déposer (décision de Mathieu).

## 13. Avertissement

Comme le reste de `sources-brutes/` : contenu **non vérifié sur du matériel**. Les résultats de simulation décrivent un
modèle, pas le bateau de Mathieu. À revalider avant tout réglage réel — un pilote mal réglé lâche la barre en mer.

## 14. Supplément du 2026-10-28 — banc commun, perturbations et indicateurs

### 14.1 Ce qui a été fait

À la suite du supplément du plan de tests (§ 10 du plan), un script de comparaison commun a été écrit
(`comparaison_pilotes.py`, hors dépôt pour l'instant). Il réutilise les deux scripts d'origine sans les modifier.

- **Validation V0** (**SIMULÉ**) : sans bruit ni houle et avec les mêmes réglages, le banc commun reproduit les trajectoires des
  deux scripts d'origine avec un écart de cap de **0,00 °** (pypilot servo idéal, pypilot servo réel, Fenix à vérin idéal).
  Cela valide le montage du banc, pas les modèles eux-mêmes.
- **Mêmes conditions pour tous** : bateau Nomoto (T = 2,26 s, K = 0,19), vérin à 7,4 °/s maximum, limite de barre commune de ±20°,
  mêmes bruits capteurs, mêmes perturbations (5 graines, résultats moyennés).
- **Perturbations** (toutes des **HYPOTHÈSES**, non mesurées) : P1 vent (échelon de +2° de barre équivalente à 100 s, rampe vers −1°),
  P2 houle (lacet direct de ±2,5° environ, périodes 4 à 9 s), P3 changement de vitesse du bateau (f : 1,0 → 0,5 → 1,0, avec
  2° de barre de compensation), P4 combinaison.
- **Indicateurs** : temps d'établissement (±0,5°), dépassement maximal (°), erreur RMS, écart maximal, activations du vérin par
  minute, temps de marche (%), course de barre (°/min), énergie estimée (Wh/h), saturations.
- **Vérin de Fenix plus fidèle** (lecture de `controlActuator`, jamais exécuté) : seuils d'arrêt et de redémarrage, deux niveaux de
  vitesse (255 / 85), rampes de ±5 par appel, attente de 1,8 s à chaque inversion de sens.

### 14.2 Correction : la bande d'arrêt de Fenix

Le § 6 et le § 10.3 retenaient une bande d'arrêt de **0,7°**, tirée de `DEFAULT_ERROR_FEEDBACK = 10`. Une lecture plus complète
montre que le firmware initialise `rudDamping = 5` (`HC_INSTPARAM`, `Autopilot.h`), valeur transmise comme « erreur de
potentiomètre » à `ActuatorManager`. Le code convertit cette valeur en dixièmes de degré avec un rapport
`_ratio = longueur de barre / longueur de course du potentiomètre`.

- Si le potentiomètre est étalonné sur 0–1023 et la barre sur ±35° (hypothèse du banc) : seuil d'arrêt ≈ **0,3°**, seuil de
  redémarrage (4 fois plus) ≈ **1,2°**.
- Avec la valeur 10 (`DEFAULT_ERROR_FEEDBACK`) : ≈ 0,6° et ≈ 2,4°. C'est la variante « arrêt 0,6° » du banc.
- **À VÉRIFIER** : la valeur réellement en vigueur (EEPROM, application) et l'étalonnage du potentiomètre.

Conséquence : les scénarios S2 et S3 du § 6 (qui utilisaient 0,7°) sont à prendre comme indicatifs ; S1 et S4 (vérin idéal) ne sont
pas touchés.

### 14.3 Résultats (**SIMULÉ**, moyenne de 5 graines ; sortie complète en annexe 10.9 du plan de tests)

Scénario P4 (vent + houle + changement de vitesse), erreur calculée sur t > 60 s :

| Algorithme | RMS (°) | Écart max (°) | Activations/min | Temps de marche (%) | Wh/h (1 A – 10 A) |
|---|---|---|---|---|---|
| Fenix codé, appel à 10 Hz | 53,7 | 101,0 | 0,0 | 0,0 | 0,00 – 0,00 |
| Fenix codé, appel à 100 Hz | 7,21 | 18,3 | 2,4 | 2,0 | 0,07 – 0,69 |
| Fenix codé, appel à 100 Hz, arrêt 0,6° | 9,46 | 23,5 | 0,9 | 1,4 | 0,05 – 0,53 |
| Fenix piste A (proportionnelle), 100 Hz | 6,99 | 17,2 | 2,3 | 2,4 | 0,06 – 0,63 |
| pypilot réglages par défaut | 1,47 | 5,90 | 12,4 | 8,8 | 1,06 – 10,60 |
| pypilot réglé (0,1 s / 30 %) | 1,36 | 5,28 | 129,6 | 40,1 | 1,45 – 14,50 |
| pypilot servo idéal (référence irréaliste) | 1,35 | 5,26 | 0,1 | 100,0 | 1,46 – 14,56 |

Autres scénarios (RMS en °, activations/min) : **E0** (écart initial de 5°) : Fenix codé 100 Hz 1,62° / 1,0 ; Fenix arrêt 0,6° 5,00° /
0,0 (aucune correction) ; pypilot défaut 0,77° / 3,6 ; pypilot réglé 0,08° / 24,5. **P2** (houle seule) : Fenix 1,08° / 0,0
(aucun mouvement) ; pypilot défaut 1,22° / 11,4 ; pypilot réglé 1,14° / 130,6.

### 14.4 Lecture prudente

1. **Mon modèle de Fenix est très en retrait sur la précision** (RMS de 3 à 9° dès que le vent change, contre environ 1° pour pypilot).
   **INFÉRENCE** sur la cause, dans mon modèle : (a) le vérin ne démarre que si l'écart de barre dépasse le seuil de redémarrage,
   et (b) l'intégrale du PID est gelée tant que l'écart de barre dépasse 1° (`actuator_busy`), si bien que de petites erreurs de
   cap restent sans réaction ; (c) en P3 et P4, le facteur de vitesse réduit les gains de Fenix quand f baisse (à f = 0,5 le
   gain proportionnel est divisé par 4).
   **Réserve importante** : mon modèle omet le modèle de référence de Fossen, l'anticipation, l'observateur de vagues et
   l'anticipation du vent de Fenix. Ces résultats ne disent donc **pas** que Fenix se comporte ainsi sur un bateau.
2. **La fréquence d'appel de `controlActuator` est décisive.** À 10 Hz, les rampes de ±5 durent environ 5 s pour atteindre la pleine
   vitesse, et la régulation diverge dans mon modèle (RMS de 54° à 81°). À 100 Hz elle reste stable. **À VÉRIFIER** : le nombre
   d'appels par seconde dans le vrai firmware (test F6 du plan).
3. **Sensibilité au réglage du potentiomètre** : avec arrêt 0,6° et redémarrage 2,4°, une erreur de cap de 5° ne déclenche aucun
   mouvement du vérin (E0). **INFÉRENCE** : une erreur de cap inférieure à environ 7° (2,4° / 0,35 de gain) pourrait rester sans
   correction dans ce réglage. À confirmer par le test F8.
4. **Houle** : Fenix ne bouge pas, et pypilot bouge beaucoup (de 11 à 130 activations/min) sans améliorer l'erreur de cap (RMS 1,14 à
   1,22° contre 1,08° pour Fenix immobile). **INFÉRENCE** : dans mon modèle la houle déplace le cap sans que la barre puisse la
   compenser ; bouger la barre pour elle coûte de l'usure et de l'énergie pour aucun gain. C'est exactement le risque que décrivait
   le supplément du plan de tests (§ 10).
5. **Cycle de service** : pypilot réglé (0,1 s / 30 %) fait marcher le vérin 40 % du temps en houle, au-dessus des 20 % de la
   fiche du vérin ; pypilot par défaut 8 à 9 % ; Fenix 1 à 2 %. **HYPOTHÈSE** : temps de marche = fraction du temps où le vérin
   est commandé ; la durée de référence du cycle de 20 % n'est pas précisée par la fiche.
6. **Énergie** : ordre de grandeur de 0,02 à 0,7 Wh/h pour Fenix, 0,3 à 10,6 pour pypilot par défaut et 0,1 à 14,5 pour pypilot
   réglé. La fourchette est large car elle encadre le courant entre 1 A et 10 A ; l'électronique de commande est exclue.
7. **La piste A change très peu** (RMS 6,99° contre 7,21° en P4 ; 2,3 contre 2,4 activations/min). Dans mon modèle, la limite vient
   des seuils d'arrêt / redémarrage et de l'intégrale gelée, pas du choix des paliers de vitesse.
   **Révision de ma recommandation du § 9** (**PROPOSITION**, non validée) : avant de modifier la vitesse du vérin, vérifier d'abord
   les seuils et la fréquence d'appel (tests F6 à F8), puis seulement reconsidérer la piste A.

### 14.5 Limites propres à ce supplément

- Aucune de ces valeurs n'est une mesure : perturbations, courant du vérin, fréquence d'appel, seuils et étalonnage du potentiomètre
  sont des hypothèses.
- Le servo « réel » de pypilot reste mon portage de `do_command` ; Fenix est simulé sans ses fonctions avancées (point 1).
- Cinq graines seulement ; les écarts entre graines ne sont pas affichés.
- Ce supplément ne choisit aucun algorithme : aucun seuil d'acceptation n'a été fixé par Mathieu.
