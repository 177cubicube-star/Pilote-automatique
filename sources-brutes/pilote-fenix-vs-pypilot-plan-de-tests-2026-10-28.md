# Fenix vs pypilot — plan de tests (simulation, banc, bateau)

Rédigé le 2026-10-28, en complément de `pilote-fenix-vs-pypilot-rapport-discussion-2026-10-28.md` (même dossier).
Le rapport dit **ce qu'on croit** ; ce plan dit **comment le vérifier**.

**Aucun test de ce plan n'a encore été exécuté**, sauf les simulations du § 2 (qui ont tourné une fois, sur mon modèle).
Toutes les colonnes « Résultat » sont vides à dessein : elles se remplissent au fil des essais.

Légende : **CONFIRMÉ** · **SIMULÉ** · **INFÉRENCE** · **HYPOTHÈSE** · **À VÉRIFIER** (comme dans le rapport).

---

## 1. Ordre recommandé (**PROPOSITION**, non validée)

Du moins risqué au plus risqué. Chaque niveau ne se tente que si le précédent a donné un résultat lisible.

| Niveau | Où | Risque | Contenu |
|---|---|---|---|
| 0 | Ordinateur | Aucun | Rejouer les simulations (§ 2) |
| 1 | Établi, **sans bateau** | Faible | Mesures sur le vérin et la géométrie (§ 3) |
| 2 | Établi, firmware Fenix en `SHIP_SIM` / `VIRTUAL_ACTUATOR` | Faible | Rejouer les scénarios avec le vrai code (§ 4) |
| 3 | Bateau **à quai**, moteur du bateau arrêté | Moyen | Réponse du vérin et de la barre sous charge (§ 5) |
| 4 | Bateau en navigation | Élevé | Pas couvert ici : à définir seulement quand les niveaux 1 à 3 sont concluants |

**Sécurité, avant tout essai avec le vérin branché :** un fusible dimensionné (le vérin tire jusqu'à 10 A), un arrêt
d'urgence qui coupe l'alimentation, la barre libre de se dégager à la main, et un montage qui ne peut pas pincer un doigt
(course de 589 mm de bras de levier). Un pilote mal réglé lâche la barre en mer : ne pas passer au niveau 4 sans accord
explicite.

## 2. Niveau 0 — simulations (rejouables)

**Prérequis.** Python 3 et `numpy` ; `matplotlib` pour les figures. Les scripts `fenix_pid_sim.py` et `pypilot_sim.py`
ont été livrés dans la conversation et ne sont **pas encore dans ce dépôt**. Ils s'exécutent en environ 2 secondes chacun.

**Lancer :** `python fenix_pid_sim.py` puis `python pypilot_sim.py`. Chaque script affiche des tableaux dans la console
et enregistre une figure PNG à côté de lui.

### 2.1 Fenix (`fenix_pid_sim.py`)

| Scénario | Ce qu'il teste | Valeur de référence (mon exécution du 2026-10-28) | Ce qui doit alerter |
|---|---|---|---|
| S0 | Validation du banc contre la théorie linéaire | Dépassement 0,00 % à f = 0,4 et 1,0 ; ζ théorique ≈ 1,30 | Dépassement non nul → mon portage est faux |
| S1 | Facteur de vitesse : tel que codé / aucun / inverse | f = 0,4 : 67,9 % (codé) · 45,5 % (aucun) · 32,3 % (inverse) | Si le « codé » devient meilleur que « aucun » à basse vitesse, mon analyse est à reprendre |
| S2 | Balayage de Kp (embardée de 20°) | Kp = 5 → Kp effectif 2,45, limite de barre 17,1° | Un Kp effectif qui ne baisse pas au-delà de 3,5 |
| S3 | Filtre dérivé « codé » vs « corrigé » | RMS cap 1,24° vs 1,30° | Un écart marqué |
| S4 | Bande morte décalée | Cap final +0,50° (bande 0,5°) vs +0,00° | Un cap final proche de 0 avec bande morte |

### 2.2 pypilot (`pypilot_sim.py`)

| Scénario | Ce qu'il teste | Valeur de référence | Ce qui doit alerter |
|---|---|---|---|
| S0 | Validation contre la théorie (servo idéal) | Cap simulé = théorique à 0,01° près (t = 20, 60, 120 s) | Écart > 0,05° |
| S1 | Servo idéal vs réel, par vitesse f | f = 1,0 : 9,1 % (idéal) / 29,7 % (réel) ; RMS 0,05° / 0,56° | Servo réel meilleur que l'idéal |
| S2 | Vitesse du vérin V | V = 7 : 29,7 % ; V = 20 : 73,8 % (servo réel) | Dépassement qui baisse avec V (servo réel) |
| S3 | Période et `speed.min` | 0,1 s / 30 % : impulsion 0,27°, RMS 0,07° | Impulsion qui ne varie pas avec la période |
| S4 | Échelon de +20°, FF | 6,3 % (FF 0,6) / 11,4 % (FF 0) | FF = 0,6 pire que FF = 0 |

### 2.3 Simulations à ajouter (**PROPOSITION**)

À écrire seulement si Mathieu les demande :

| Id | Contenu | Données nécessaires |
|---|---|---|
| SIM-A | Fenix avec le vrai vérin : rampes ±5, paliers 255 / 85, seuil de redémarrage, V = 7,4 °/s | Fréquence d'appel de `controlActuator`, PWM minimum (M3) |
| SIM-B | Comparaison paliers 255 / 85 vs vitesse proportionnelle (piste A) | Idem |
| SIM-C | Rejouer S1–S4 avec T et K du Catalina Capri 22 | T et K (M7) |
| SIM-D | Cycle de service : pourcentage de temps de marche du vérin dans chaque scénario | Aucune (sortie du modèle, mais **SIMULÉ** seulement) |

## 3. Niveau 1 — mesures sur l'établi (sans bateau)

Matériel : mètre ruban, chronomètre (ou la sortie série d'un Arduino qui date les changements du potentiomètre),
alimentation 12 V, multimètre ou pince ampèremétrique.

| Id | Mesure | Procédure | À noter | Pourquoi |
|---|---|---|---|---|
| M1 | Géométrie réelle | Barre au centre : mesurer axe de mèche → trou de la barre ; longueur du vérin en veille ; distance perpendiculaire du point fixe à l'axe de la barre ; rôle et longueur de l'extension | 4 cotes + schéma coté | Lever l'incohérence 589 / 610 / 460 mm du rapport (§ 10.3) |
| M2 | Vitesse réelle du vérin | Mouvement sur la course entière à PWM 255, 170 et 85, **à vide** puis **avec un effort** (ressort ou masse tirant sur la barre) ; chronométrer 3 allers-retours par réglage | Temps de course, mm/s, puis °/s de barre | Remplacer l'hypothèse V = 7 °/s ; documenter la variation de 5 à 10 % |
| M3 | PWM minimum de démarrage | Monter le PWM de 0 par pas de 5 jusqu'au mouvement, dans les deux sens, à vide puis en charge | Valeur de démarrage et d'arrêt | Dimensionner la piste A et la zone de redémarrage |
| M4 | Course et angle de barre | Aller bout à bout ; mesurer la lecture du potentiomètre aux butées et l'angle de barre correspondant | Course (mm), angle de barre max bâbord/tribord | Vérifier l'autorité (≈ ±201 mm pour ±20°) |
| M5 | Courant | Lire A9 (Fenix) ou un multimètre à vide, à mi-charge et à charge max | Courant en fonction de l'effort ; courant de démarrage | Valider la courbe de la fiche (≈ 1 à 10 A) et régler `maxCurrent` |
| M6 | Échauffement / cycle de service | Séquence répétée de petits mouvements imitant un pilote (ex. 1 s de marche / 4 s d'arrêt), pendant 30 min ; mesure de la température du boîtier | Température au fil du temps ; temps de marche cumulé | Vérifier que 20 % tient dans un usage réel (HYPOTHÈSE à confirmer) |
| M7 | Dynamique du bateau (T, K) | À faire **plus tard, sur l'eau** : écrire ici le protocole d'identification retenu (ex. coup de barre de 10° puis lecture de la vitesse de rotation) | T (s), K | Remplacer T = 2,26 s et K = 0,19, valeurs d'un bateau de 12 m |
| M8 | Bruit de cap statique | IMU fixe, 5 min, enregistrer le cap | Écart-type du cap et de la vitesse de rotation | Remplacer les bruits supposés (0,2° et 0,1 °/s) |
| M9 | Précision du potentiomètre | Comparer la lecture à un rapporteur d'angle sur la barre en 5 points | Erreur (°) et jeu mécanique | Évaluer la bande d'arrêt de Fenix (≈ 0,3° à 0,7° selon `rudDamping` et l'étalonnage, voir rapport § 14.2) |

## 4. Niveau 2 — firmware Fenix sans bateau

Fenix prévoit deux options dans `Fenix_config.h` (lignes 81 et 82, actuellement en commentaire) :
`SHIP_SIM` (simule le cap du bateau, sans IMU) et `VIRTUAL_ACTUATOR` (simule la barre, utile quand le vérin n'est
pas disponible). **À VÉRIFIER** : comment elles se configurent et si leurs paramètres (ligne 198 pour le vérin virtuel)
peuvent être réglés sur T, K et V de Mathieu.

| Id | Test | Procédure | Critère de lecture |
|---|---|---|---|
| F1 | Compilation du firmware tel quel | Compiler avec la configuration de Mathieu | Compile sans erreur ; **noter la taille et le message du compilateur** |
| F2 | Rejouer S1 (facteur de vitesse) | `SHIP_SIM` + `VIRTUAL_ACTUATOR`, écart initial de 5°, faire varier la vitesse moyenne (`VD_USER_AVG_SPEED`) | Le dépassement et le temps de retour sous 1° se comparent à la colonne « codé » du § 2.1 |
| F3 | Rejouer S2 (Kp) | Régler Kp à 2, 3,5, 5, 7 ; embardée de 20° | Le Kp effectif baisse-t-il au-delà de 3,5 ? La limite de barre diminue-t-elle ? |
| F4 | Rejouer S4 (bande morte) | Bande morte 0 et 0,5° | Le cap final reste-t-il décalé de la valeur de la bande ? |
| F5 | Journaliser | Utiliser la sortie de débogage série pour enregistrer cap, consigne, barre cible, barre mesurée, PWM | Fichier CSV à comparer aux figures du § 2 |

Si F2 à F4 **confirment** la simulation, c'est un argument pour contacter l'auteur du code ; si elles l'**infirment**, c'est
mon portage qui est en cause. Dans les deux cas, ne rien modifier dans Fenix avant d'avoir noté le résultat.

## 5. Niveau 3 — bateau à quai

| Id | Test | Procédure | Critère de lecture |
|---|---|---|---|
| Q1 | Course sous charge | Pilote en veille, barre libre, vérin d'un bout à l'autre | Mouvement continu, pas de point dur, pas de claquement |
| Q2 | Vitesse sous charge réelle | Chronométrer la course avec la barre attachée au safran (dans l'eau, bateau amarré) | Vitesse de barre réelle ; comparer à 6,2 à 7,4 °/s |
| Q3 | Autorité | Atteindre ±20° de barre ; noter l'effort et le courant | Courant ≤ celui de la courbe de la fiche ; pas de butée atteinte avant ±20° |
| Q4 | Comportement de la zone d'arrêt | Demander des consignes de barre de 0,5°, 1°, 2° et 5° | Position finale (potentiomètre) ; nombre de mouvements nécessaires |
| Q5 | Cycle de service | Mode automatique avec cap simulé bruité pendant 20 min | Température du vérin ; temps de marche cumulé en % |
| Q6 | Coupure d'urgence | Couper l'alimentation pendant un mouvement | Le vérin s'arrête ; la barre reste manœuvrable à la main |

## 6. Tests de comparaison des pistes (**PROPOSITION**)

À ne faire que si Mathieu décide d'explorer les pistes A, B ou C du rapport (§ 9). Procédure commune : les mêmes
scénarios (F2, F3, Q4), version actuelle contre version modifiée, mêmes conditions, **une seule modification à la fois**.

| Piste | Critère de réussite proposé (à valider par Mathieu avant l'essai) |
|---|---|
| A — vitesse proportionnelle | Moins de mouvements de barre par minute qu'avec 255 / 85 pour une erreur de cap RMS comparable ; temps de marche inférieur |
| B — normalisation par V mesuré | Dépassement stable quand V varie de ±30 % |
| C — limite de variation de la consigne | Moins d'oscillation autour de la consigne ; pas de retard excessif sur un échelon de 20° |

## 7. Suivi des tests

| Id | Description courte | Statut | Date | Résultat | Écart avec la simulation |
|---|---|---|---|---|---|
| § 2.1 S0–S4 | Simulation Fenix | Exécuté une fois (SIMULÉ) | 2026-10-28 | Voir rapport § 6 | — |
| § 2.2 S0–S4 | Simulation pypilot | Exécuté une fois (SIMULÉ) | 2026-10-28 | Voir rapport § 7 | — |
| M1 | Géométrie réelle | À faire | | | |
| M2 | Vitesse réelle du vérin | À faire | | | |
| M3 | PWM minimum | À faire | | | |
| M4 | Course et angle | À faire | | | |
| M5 | Courant | À faire | | | |
| M6 | Échauffement | À faire | | | |
| M7 | T et K du bateau | À faire (sur l'eau) | | | |
| M8 | Bruit de cap | À faire | | | |
| M9 | Précision du potentiomètre | À faire | | | |
| F1–F5 | Firmware Fenix sans bateau | À faire | | | |
| Q1–Q6 | Bateau à quai | À faire | | | |
| SIM-A à D | Simulations supplémentaires | Proposé, non demandé | | | |
| IND-1 | Ajouter les 5 indicateurs aux simulations (§ 10.2) | Exécuté une fois (SIMULÉ), via `comparaison_pilotes.py` | 2026-10-28 | Voir § 10.7 et rapport § 14 | — |
| P1–P4 | Simulations avec perturbations réalistes (§ 10.4) | Exécuté une fois (SIMULÉ), perturbations hypothétiques | 2026-10-28 | Voir § 10.7 et rapport § 14 | — |
| F6–F9 | Nouveaux tests firmware Fenix (§ 10.8) | À faire | | | |
| Q7 | Mesure d'énergie (Wh) et d'activations sur le bateau (§ 10.2) | À faire | | | |

## 8. Hypothèses à remplacer par des mesures

| Hypothèse | Valeur utilisée | Remplacée par |
|---|---|---|
| Vitesse du vérin | 7 °/s (calcul avec le montage : 5,6 à 7,4 °/s) | M2, Q2 |
| Dynamique du bateau | T = 2,26 s, K = 0,19 (bateau de 12 m) | M7 |
| Bruit de cap / de rotation | 0,2° / 0,1 °/s | M8 |
| Géométrie du montage | 589 / 610 / 460 mm, extension 170 mm | M1 |
| Servo pypilot « réel » | Mon portage de `do_command` | Essai sur un vrai pypilot (hors périmètre actuel) |
| Cycle de service 20 % respecté | Non vérifié | M6, Q5 |

## 9. Avertissement

Ce plan n'a pas été relu par Mathieu et ne constitue pas une procédure validée. Les critères de lecture sont des
repères tirés de simulations, pas des seuils d'acceptation. À adapter avant exécution ; la sécurité du § 1 prime sur
tout le reste.

## 10. Supplément du 2026-10-28 — indicateurs de comparaison et perturbations

### 10.1 Origine

Texte **transmis par Mathieu** le 2026-10-28, sans indication de sa provenance (**À VÉRIFIER** : auteur ou outil qui l'a
rédigé). Il est repris ici en substance, avec mes commentaires séparés ; ce n'est pas une décision validée. Il dit en
résumé : les graphiques des simulations donnent une première comparaison visuelle, mais ne permettent pas de choisir
définitivement un algorithme ; les prochains essais doivent se comparer sur des indicateurs chiffrés, dans des conditions
strictement identiques, et inclure des perturbations réalistes.

### 10.2 Les cinq indicateurs proposés (transmis par Mathieu)

| Indicateur | Ce qu'il mesure | Dans mes simulations actuelles ? (**CONFIRMÉ** par les sorties du § 2) | À faire |
|---|---|---|---|
| Temps d'établissement | Temps pour rester dans une tolérance de cap, par exemple ±0,5° | Partiellement : colonne « <1° à (s) », avec un seuil de **1°** et non 0,5° | Passer à ±0,5°. La mesure actuelle est bien « dernière sortie de la bande » (donc rester dedans) : **CONFIRMÉ** dans `metrics()` des deux scripts ; le script Fenix a un paramètre de bande, celui de pypilot un seuil fixe |
| Dépassement maximal | Écart de cap au-delà de la consigne | Oui, mais en **pourcentage** de l'écart initial | Ajouter la valeur en degrés |
| Erreur RMS | Précision moyenne du maintien de cap | pypilot : oui (RMS sur les 100 dernières secondes). Fenix : seulement dans S3 | Ajouter dans tous les scénarios Fenix |
| Nombre d'activations du moteur | Sollicitation du vérin et usure potentielle | pypilot : « impuls./min » (sens réel seulement pour le servo « réel » ; la valeur du servo idéal, ≈ 600, n'est pas comparable). Fenix : seulement « barre °/min » (course), pas un nombre d'activations | Compter les démarrages du vérin dans les deux simulations, avec la même définition |
| Énergie consommée (Wh) | Impact sur les batteries | **Non** : absent des simulations | Mesure réelle : tension × courant intégrés dans le temps (courant lu sur A9 chez Fenix ; la fiche du vérin donne environ 1 A à vide et jusqu'à 10 A à pleine charge). En simulation, une estimation demande un modèle courant-effort : **HYPOTHÈSE**, à ne présenter que comme ordre de grandeur |

Les deux derniers indicateurs sont ceux que mes simulations couvrent le moins, alors que le texte les juge les plus
importants. **INFÉRENCE** (cohérente avec le rapport, § 7) : le résultat de pypilot le montre déjà, un servo « idéal » très
précis (RMS 0,05°) n'est pas réaliste ; une comparaison qui ignorerait l'usure et l'énergie favoriserait des solutions qui
bougent la barre en permanence.

### 10.3 Conditions de comparaison exigées (transmises par Mathieu) et état actuel

Exigences : mêmes caractéristiques de bateau et d'actionneur, mêmes perturbations, mêmes conditions initiales, **même limite
de barre**, saturations documentées.

| Exigence | État dans mes simulations (**CONFIRMÉ** par les sorties du § 2 et le rapport) | Écart à combler |
|---|---|---|
| Même bateau | T = 2,26 s, K = 0,19 dans les deux | Remplacer par les valeurs mesurées (M7) |
| Même actionneur | Non : Fenix S1 utilise un vérin idéal, d'autres scénarios Fenix une bande d'arrêt de 0,7° (corrigée en ≈ 0,3° dans le banc commun, rapport § 14.2) ; pypilot compare un servo idéal et un servo « réel » | Définir un seul modèle de vérin commun (SIM-A) |
| Mêmes conditions initiales | Écart initial de 5° dans S1 des deux ; autres scénarios différents (embardée de 20°, échelon de +20°) | Fixer une série commune de scénarios |
| Même limite de barre | Non : la limite de barre de Fenix **diminue** quand Kp dépasse 3,5 (S2 : 17,1° à Kp = 5) ; le script pypilot bute à une plage fixe de ±45° (`RUDDER_RANGE`, **CONFIRMÉ**) | Imposer la même limite aux deux, par exemple ±20° (valeur à choisir) |
| Saturations documentées | Non : les sorties ne comptent pas les saturations | Ajouter le pourcentage du temps passé à la limite de barre |

### 10.4 Perturbations réalistes à ajouter (simulation)

État actuel (**CONFIRMÉ**) : les simulations ne contiennent que des écarts initiaux, des échelons de consigne et un décalage
constant de barre (« helm »). Il n'y a ni vagues, ni variations de vent, ni variation de la vitesse du bateau en cours d'essai
(la vitesse f n'est qu'un paramètre constant par essai).

| Id | Perturbation | Principe proposé | Paramètres à fixer (aucun n'est mesuré : **HYPOTHÈSES**) |
|---|---|---|---|
| P1 | Variation de vent | Décalage de barre (« helm ») qui change en échelon puis en rampe | Amplitude, vitesse de variation |
| P2 | Houle / vagues | Perturbation oscillante sur le lacet | Amplitude, période (quelques secondes), bruit associé |
| P3 | Changement de vitesse du bateau | Facteur de vitesse f qui varie en cours d'essai (ex. 1,0 → 0,5) | Durée et forme de la variation |
| P4 | Combinaison réaliste | P1 + P2 + P3 ensemble | Ordre et durée |

**INFÉRENCE** : ces perturbations sont aussi celles pour lesquelles Fenix a des fonctions dédiées (observateur de vagues,
anticipation du vent). Sans elles, mes simulations **ne peuvent pas** évaluer ces fonctions ; leur utilité n'est donc
ni confirmée ni infirmée.

### 10.5 Sur le bateau

Reprendre les cinq indicateurs dans les essais Q2 à Q5 : activations et énergie mesurées en continu (courant sur A9 ou
pince ampèremétrique, tension de la batterie), pendant une durée identique pour chaque algorithme.

### 10.6 Point laissé à Mathieu

Aucun seuil d'acceptation n'est fixé ici (par exemple « ±0,5° en moins de X s » ou un maximum de Y activations par
minute) : ils dépendent de l'usage visé et restent à décider.

### 10.7 Première exécution du banc commun (2026-10-28, **SIMULÉ**)

Le script `comparaison_pilotes.py` (hors dépôt, livré dans la conversation ; il importe `fenix_pid_sim.py` et `pypilot_sim.py`,
à placer dans le même dossier) a été exécuté une fois : environ 9 secondes. Validation V0 : écart de cap de 0,00° avec les deux
scripts d'origine. Détail des résultats et lecture prudente : rapport § 14. Sortie brute en annexe 10.9.

Ce que cela change pour ce plan :

- Les cinq indicateurs sont désormais calculés (temps d'établissement à ±0,5° seulement pour E0, où il a un sens), avec en plus le
  temps de marche (cycle de service) et les saturations.
- Même bateau, même vérin (7,4 °/s), même limite de barre (±20°) et mêmes perturbations pour tous. Ces perturbations restent des
  **hypothèses** : à remplacer par des mesures (M7, M8).
- Les deux dernières exigences du § 10.3 (même limite de barre, saturations documentées) sont remplies ; la saturation de barre
  mesurée est de 0,0 % dans tous les cas (la barre n'atteint pas ±20°). Une partie de la consigne de Fenix est écrêtée à ±20°
  dans les cas qui divergent (10 Hz).
- Résultat à ne pas sur-interpréter : Fenix est simulé sans modèle de référence, sans anticipation du vent et sans observateur de
  vagues (rapport § 14.4, point 1).

### 10.8 Nouveaux tests proposés à la suite du banc commun (**PROPOSITION**)

Ils visent les trois paramètres dont dépend le plus le résultat simulé de Fenix et que je n'ai pas pu lire dans le code.

| Id | Test | Procédure | À noter |
|---|---|---|---|
| F6 | Fréquence d'appel de `controlActuator` | Activer le moniteur de fréquence de boucle **déjà présent** dans le firmware (`Monitor_frequency`, `LOOP_FREQ`, `Autopilot.cpp:1344` et `:1677-1689` : il affiche `!Loop.Freq` tous les 100 tours) et lire la sortie série. `controlActuator` est appelé à chaque tour (`ActuatorManager.cpp:158`), donc la fréquence de boucle est sa fréquence d'appel (lecture de code, **à confirmer** par la mesure) | Fréquence de boucle (Hz) ; en déduire la durée réelle d'une rampe de 0 à 255 (51 appels) |
| F7 | Seuils réels d'arrêt et de redémarrage | Lire `rudDamping` effectif (EEPROM / application) et l'étalonnage du potentiomètre ; calculer `toRudder(rudDamping)` | Seuil d'arrêt et de redémarrage en degrés de barre (comparer à 0,3° / 1,2° et 0,6° / 2,4°) |
| F8 | Zone morte de démarrage | Vérin à l'arrêt, `SHIP_SIM` + `VIRTUAL_ACTUATOR` ou à l'établi : imposer des écarts de cap de 2°, 4°, 6°, 8°, et un décalage constant de 2° de barre | Écart de cap à partir duquel le vérin démarre ; écart de cap stationnaire |
| F9 | Facteur de vitesse | Faire varier la vitesse moyenne déclarée de 1,0 à 0,5 avec un décalage constant de barre | Écart de cap stationnaire en fonction de f (à comparer à P3) |

### 10.9 Annexe — sortie brute de `comparaison_pilotes.py`, 2026-10-28

```
=== V0 : validation du banc commun contre les deux scripts d'origine ===
  pypilot ideal : écart max de cap = 0.00e+00 °
  pypilot real  : écart max de cap = 0.00e+00 °
  Fenix  idéal  : écart max de cap = 0.00e+00 °

=== E0 : écart initial de 5°, sans perturbation (RMS sur t > 400 s) ===
algorithme                 | établ.±0,5° dépass.°  RMS° max|e|° | activ./min marche% barre°/min | Wh/h bas–haut | sat.% cible écr.%
Fenix codé (10 Hz)         |        >600     0.00  5.00    5.00 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
Fenix codé (100 Hz)        |        >600     2.92  1.62    2.81 |        1.0     0.7        0.9 |  0.02– 0.24 |   0.0         0.0
Fenix codé 100Hz arrêt0,6  |        >600     0.00  5.00    5.00 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
Fenix piste A (100 Hz)     |        >600     2.90  1.60    2.73 |        1.0     0.9        0.9 |  0.02– 0.24 |   0.0         0.0
pypilot défaut             |        >600     1.49  0.77    1.36 |        3.6     2.6       11.5 |  0.31– 3.10 |   0.0         0.0
pypilot réglé 0,1 s/30%    |          34     0.49  0.08    0.18 |       24.5     5.7        7.6 |  0.21– 2.05 |   0.0         0.0
pypilot servo idéal*       |          34     0.49  0.05    0.12 |        0.1   100.0        6.0 |  0.16– 1.63 |   0.0         0.0

=== P1 : variation de vent (RMS sur t > 60 s) ===
Fenix codé (10 Hz)         |           —        — 54.48   97.96 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0        37.3
Fenix codé (100 Hz)        |           —        —  3.33    7.70 |        1.8     1.2        1.5 |  0.04– 0.40 |   0.0         0.0
Fenix codé 100Hz arrêt0,6  |           —        —  8.42   13.24 |        0.6     0.8        1.1 |  0.03– 0.29 |   0.0         0.0
Fenix piste A (100 Hz)     |           —        —  3.34    7.66 |        1.7     1.4        1.4 |  0.04– 0.37 |   0.0         0.0
pypilot défaut             |           —        —  0.93    3.42 |        4.0     2.8       12.6 |  0.34– 3.40 |   0.0         0.0
pypilot réglé 0,1 s/30%    |           —        —  0.72    3.24 |       20.0     4.5        6.0 |  0.16– 1.63 |   0.0         0.0
pypilot servo idéal*       |           —        —  0.70    3.19 |        0.1   100.0        6.4 |  0.17– 1.72 |   0.0         0.0

=== P2 : houle (RMS sur t > 60 s) ===
Fenix codé (10 Hz)         |           —        —  1.08    2.34 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
Fenix codé (100 Hz)        |           —        —  1.08    2.34 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
Fenix codé 100Hz arrêt0,6  |           —        —  1.08    2.34 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
Fenix piste A (100 Hz)     |           —        —  1.08    2.34 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0         0.0
pypilot défaut             |           —        —  1.22    3.30 |       11.4     8.1       36.0 |  0.97– 9.73 |   0.0         0.0
pypilot réglé 0,1 s/30%    |           —        —  1.14    2.58 |      130.6    40.5       54.2 |  1.46–14.65 |   0.0         0.0
pypilot servo idéal*       |           —        —  1.14    2.57 |        0.1   100.0       54.4 |  1.47–14.70 |   0.0         0.0

=== P3 : changement de vitesse du bateau (f : 1,0 → 0,5 → 1,0), barre de compensation 2° dès 100 s ===
Fenix codé (10 Hz)         |           —        — 80.72  151.19 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0        27.4
Fenix codé (100 Hz)        |           —        —  2.74    6.00 |        0.9     0.6        0.8 |  0.02– 0.21 |   0.0         0.0
Fenix codé 100Hz arrêt0,6  |           —        —  7.96   11.86 |        0.4     0.5        0.7 |  0.02– 0.19 |   0.0         0.0
Fenix piste A (100 Hz)     |           —        —  2.82    6.06 |        0.9     0.8        0.7 |  0.02– 0.20 |   0.0         0.0
pypilot défaut             |           —        —  0.74    2.51 |        3.4     2.4       10.7 |  0.29– 2.90 |   0.0         0.0
pypilot réglé 0,1 s/30%    |           —        —  0.39    2.13 |       16.5     3.8        5.0 |  0.14– 1.36 |   0.0         0.0
pypilot servo idéal*       |           —        —  0.37    2.07 |        0.1   100.0        6.1 |  0.16– 1.65 |   0.0         0.0

=== P4 : combinaison P1 + P2 + P3 (RMS sur t > 60 s) ===
Fenix codé (10 Hz)         |           —        — 53.71  101.01 |        0.0     0.0        0.0 |  0.00– 0.00 |   0.0        18.8
Fenix codé (100 Hz)        |           —        —  7.21   18.31 |        2.4     2.0        2.5 |  0.07– 0.69 |   0.0         0.0
Fenix codé 100Hz arrêt0,6  |           —        —  9.46   23.46 |        0.9     1.4        1.9 |  0.05– 0.53 |   0.0         0.0
Fenix piste A (100 Hz)     |           —        —  6.99   17.21 |        2.3     2.4        2.3 |  0.06– 0.63 |   0.0         0.0
pypilot défaut             |           —        —  1.47    5.90 |       12.4     8.8       39.2 |  1.06–10.60 |   0.0         0.0
pypilot réglé 0,1 s/30%    |           —        —  1.36    5.28 |      129.6    40.1       53.7 |  1.45–14.50 |   0.0         0.0
pypilot servo idéal*       |           —        —  1.35    5.26 |        0.1   100.0       53.9 |  1.46–14.56 |   0.0         0.0
```

Les en-têtes de colonnes des scénarios P1 à P4 sont les mêmes que ceux de E0 ; les titres ci-dessus sont abrégés. `*` : servo idéal,
référence théorique ; ses activations ne sont pas comparables.
