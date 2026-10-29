# Architecture proposée du pilote — fondée sur l'audit du code (Fenix, pypilot)

Rédigé le 2026-10-28. **Statut : PROPOSITION. Aucune décision de conception n'est validée.**
Ce document répond à une demande de Mathieu : une architecture **fondée sur l'audit du code source**, avec la
**traçabilité** de chaque choix vers des fichiers précis des deux projets, et des **exigences de validation** explicites.

Il s'appuie sur les trois documents de `sources-brutes/` du même jour :
`pilote-fenix-vs-pypilot-rapport-discussion-2026-10-28.md` (« le rapport »),
`pilote-fenix-vs-pypilot-plan-de-tests-2026-10-28.md` (« le plan ») et `fenix-imu-actionneur-lecture-2026-10-28.md`.

> Le `README.md` indique que le dépôt est en **phase de collecte de sources**, sans décision technique arrêtée, et que
> l'organisation en dossiers se fixe « quand le contenu arrivera ». Ce document ouvre le volet **Conception** : il est rangé
> dans un nouveau dossier `conception/`, choix de rangement **à confirmer par Mathieu** (le déplacer ne change rien au contenu).

**Non exécuté :** rien n'a été compilé, téléversé ni testé sur du matériel. L'audit est une **lecture de code**
(clones superficiels, jamais lancés) et les résultats chiffrés viennent de **simulations Python écrites pour l'occasion**.

Légende : **CONFIRMÉ** = lu dans le code ou fourni par Mathieu · **SIMULÉ** = résultat de mes modèles Python (limites au
rapport § 8 et § 14.5) · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte.
Statut d'une décision : **PROPOSÉE** (ma recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour).

---

## 1. Ce que l'architecture doit servir

D'après le `README.md` et ce que Mathieu a décrit :

- Un pilote de barre pour voilier du type Fenix : **Arduino Mega + vérin linéaire + IMU**, avec une conception comparable à un
  produit commercial (Pelagic Autopilot). Références du dépôt : Pelagic (commerciale), pypilot (open source, architecture
  la plus proche de Pelagic), Fenix (base de départ DIY).
- Le bateau de Mathieu : un Catalina Capri 22, barre franche, montage de vérin selon la recommandation du Raymarine ST1000+
  (cotes 589 / 610 / 460 mm, extension de 170 mm ; rapport § 10.2).
- Le vérin envisagé : Firgelli FA-HF-100-12, 12 V, 3 po/s à vide, **cycle de service de 20 %, sans retour de position**
  (rapport § 10.1). Le retour de position doit donc venir d'un **potentiomètre de barre** (comme `PIN_RUDDER` chez Fenix).

Priorités de Mathieu pour trancher entre solutions (préférences de travail) : exactitude, compréhension, respect des décisions
existantes, traçabilité, simplicité, testabilité, maintenabilité.

## 2. Constats de l'audit (faits traçables)

Références : Fenix commit `b8410e50fa19` (2026-10-23), pypilot commit `fdff88ffe59c` (2026-10-07, version 0.71). Les numéros de
ligne valent pour ces commits. Tous sont **CONFIRMÉS** par lecture, sauf mention.

### 2.1 Fenix

| ID | Constat | Fichier : lignes |
|---|---|---|
| F-01 | Un seul fil d'exécution : `loop()` appelle `MyPilot.Compute()` à chaque tour, sans temporisation visible | `Fenix.ino:109`, `:132` |
| F-02 | `Autopilot::Compute` appelle `ActuatorManager::Compute` à chaque tour en mode opérationnel | `Autopilot.cpp:151`, `:238` |
| F-03 | `ActuatorManager` **hérite** du PID, du retour de barre et du contrôleur d'actionneur (trois rôles dans une classe) | `ActuatorManager.h:38` |
| F-04 | Chaîne de calcul : modèle de référence de Fossen → anticipation (FF) → PID → `controlActuator` | `ActuatorManager.cpp:138-158` |
| F-05 | Le PID n'est exécuté que si 100 ms se sont écoulées ; `controlActuator` est appelé, lui, à **chaque tour** de `loop()` | `PID_v1_ext.cpp:80-83` ; `ActuatorManager.cpp:158` |
| F-06 | Facteur de vitesse : Kp et Ki × f², Kd ÷ f, limite de sortie × min(f², 1) ; f **plafonné** à `outMax/(kp·100)`, soit 1,0 aux gains par défaut | `PID_v1_ext.cpp:102-110` ; gains `Autopilot.h:420` |
| F-07 | f = vitesse mesurée / vitesse moyenne saisie, lissé (90/10) et borné entre 0,4 et 1,6 | `Autopilot.cpp:387-388` ; `Autopilot.h:599-603`, `:841` |
| F-08 | L'intégrale est **gelée** tant que l'écart de barre (cible − mesure) dépasse 1° (`actuator_busy`) et selon d'autres conditions | `PID_v1_ext.cpp:124-129`, `:144-151`, `:199` ; `PID_v1_ext.h:28` |
| F-09 | La zone morte adaptative `calcDeadband` n'est pas appelée (appel en commentaire) ; la zone morte vaut le minimum de 0,5°, appliquée comme **décalage** de l'erreur | `PID_v1_ext.cpp:96`, `:223` ; `PID_v1_ext.h:35` |
| F-10 | `_kdContrib_prev` est initialisée et lue mais **jamais réaffectée** | `PID_v1_ext.cpp:41`, `:167` |
| F-11 | Seuils du vérin : arrêt = `toRudder(rudDamping)`, redémarrage = 4 × arrêt, mode lent sous 3,0° ; `rudDamping` vaut 5 par défaut | `ActuatorManager.cpp:270-272` ; `Autopilot.h:443` ; `Fenix_config.h:189-190` |
| F-12 | Deux niveaux de vitesse (255 / 255÷3), rampes de ±5 par appel, attente de 1,8 s à l'inversion de sens | `ActuatorManager.cpp:407-427`, `:455-483` ; `ActuatorManager.h:31` ; `Fenix_config.h:169` |
| F-13 | Interface matérielle : moteur en PWM (D6) + sens (D7), potentiomètre de barre en A8, mesure de courant en A9 | `Fenix_config.h:105-117` |
| F-14 | Protection : détection de blocage par le courant | `ActuatorManager.cpp:225` |
| F-15 | IMU : l'ICM20948 est la seule puce gérée ; cap par filtre Mahony dans le firmware | `Fenix_config.h:146` ; `ICM20948AHRS.cpp:1-6` ; voir `fenix-imu-actionneur-lecture-2026-10-28.md` |
| F-16 | Modèle de bateau : Nomoto T = 2,26 s, K = 0,19 (« bateau de 12 m »), identifié en ligne et mis à l'échelle de la vitesse | `Autopilot.cpp:44`, `:391` ; `OnlineNomotoIdentifier.cpp:387` |
| F-17 | Observateur de vagues et anticipation du vent présents | `BearingMonitor.cpp:444-471` ; `ActuatorManager.cpp:154` |
| F-18 | Modes de simulation : `SHIP_SIM` (cap simulé) et `VIRTUAL_ACTUATOR` (barre simulée), en commentaire dans la configuration | `Fenix_config.h:81-82` ; usage dans `Autopilot::Compute`, `Autopilot.cpp:151-175` |
| F-19 | Moniteur de fréquence de boucle déjà intégré (affiche `!Loop.Freq` tous les 100 tours) | `Autopilot.cpp:1344`, `:1677-1689` ; `Autopilot.h:401-402` |

### 2.2 pypilot

| ID | Constat | Fichier : lignes |
|---|---|---|
| P-01 | Architecture multi-processus autour d'un serveur de valeurs (port 23322 par défaut) | `server.py:27` ; lecture antérieure du reste (lignes non relevées) |
| P-02 | Pilote `basic` : gains P 0,003, D 0,09, DD 0,075, PR 0,005, FF 0,6 ; le terme intégral est **commenté** | `pilots/basic.py:19-24` |
| P-03 | La commande est la **somme pondérée** des termes ; sa sortie est une **vitesse de servo normalisée** | `pilots/pilot.py:38-47` ; `pilots/basic.py:26-46` |
| P-04 | Erreur de cap écrêtée à ±30° | `autopilot.py:322-326` |
| P-05 | Une intégrale d'erreur existe dans `autopilot.py` (bornée à ±10) mais n'est pas utilisée par `basic` | `autopilot.py:344-351` |
| P-06 | Servo : mécanisme « période / windup » (impulsions d'au moins `period` à une vitesse entre `speed.min` et `speed.max`) ; défauts 0,4 s et 100 % / 100 % | `servo.py:414-455`, `:288`, `:296-297` |
| P-07 | Le servo **applique un étalonnage** vitesse → commande moteur, séparé bâbord / tribord (défaut [0,2 ; 0,8]), ce qui compense un seuil minimal de démarrage | `servo.py:459-469` |
| P-08 | Protections : courant maximal (4,5 A par défaut), vitesse de variation maximale, défauts de surintensité par sens | `servo.py:272`, `:280-281`, `:731-735` |
| P-09 | Fusion IMU de Kalman (RTIMULib, type 1), filtres de cap et de vitesse de rotation | `boatimu.py:65`, `:117`, `:233` |
| P-10 | Plage de barre (45° par défaut), décalage et échelle persistants | `rudder.py:24-29` |
| P-11 | Firmware moteur séparé (Arduino), trames avec CRC8 | `arduino/motor/motor.ino:75` |
| P-12 | Plusieurs pilotes sont désactivés (`disabled = True`) : autotune, deadzone, fuzzy, gps, learning, rate, simple, vmg | `pilots/*.py` |

### 2.3 Preuves chiffrées issues des simulations (**SIMULÉ**)

Renvois : rapport § 6, § 7, § 14 ; plan § 2, § 10.7. Scripts hors dépôt : `fenix_pid_sim.py`, `pypilot_sim.py`,
`comparaison_pilotes.py` (le dernier a une validation V0 : écart de cap de 0,00° avec les deux autres).

| ID | Résultat | Réf. |
|---|---|---|
| S-01 | Facteur de vitesse de Fenix tel que codé : régulation plus lente et plus oscillante à basse vitesse que sans facteur (f = 0,4 : dépassement 67,9 % contre 45,5 %) | rapport § 6 |
| S-02 | Au-delà de Kp = 3,5, le plafond fait baisser le Kp effectif et réduit la limite de barre (Kp = 5 : limite 17,1°) | rapport § 6 |
| S-03 | pypilot, réglages par défaut, servo réel : impulsion minimale ≈ 3° de barre ; cap qui oscille en permanence (RMS 0,56° contre 0,05° pour un servo idéal) | rapport § 7 |
| S-04 | pypilot : les gains ne sont pas normalisés par la vitesse du vérin V (dépassement de 22 % à V = 3 °/s jusqu'à 74 % à V = 20 °/s) | rapport § 7 |
| S-05 | Mon modèle de Fenix : un vérin qui ne démarre que si l'écart de barre dépasse le seuil de redémarrage, combiné à l'intégrale gelée, laisse de petites erreurs de cap sans réaction (arrêt 0,6° : aucune correction d'un écart de 5°) | rapport § 14.4 |
| S-06 | La fréquence d'appel de `controlActuator` est décisive : à 10 Hz la régulation diverge dans mon modèle, à 100 Hz elle reste stable | rapport § 14.4 |
| S-07 | Houle : un pilote qui bouge la barre pour la suivre (11 à 130 activations/min) n'améliore pas l'erreur de cap (RMS 1,14 à 1,22° contre 1,08° sans mouvement) | rapport § 14.4 |
| S-08 | Cycle de service : pypilot réglé fin (0,1 s / 30 %) fait marcher le vérin 40 % du temps en houle ; pypilot par défaut 8 à 9 % ; Fenix 1 à 2 % | rapport § 14.4 |
| S-09 | La piste « vitesse proportionnelle » (A) change très peu le résultat de Fenix dans mon modèle | rapport § 14.4 |

**Réserve générale** : Fenix est simulé sans modèle de référence, sans anticipation ni observateur de vagues. Les points S-05 à
S-09 décrivent mon modèle, pas le firmware réel.

## 3. Principes d'architecture proposés

Chaque principe cite les constats et les preuves qui le justifient. Statut de tous : **PROPOSÉ**.

| ID | Principe | Constats | Preuves |
|---|---|---|---|
| A-1 | **Quatre responsabilités séparées** : (1) estimation du cap et de la rotation, (2) loi de commande cap → demande de barre, (3) couche vérin demande → moteur, (4) supervision et protections. Fenix mélange 2, 3 et 4 dans une classe (F-03) ; pypilot les sépare en processus et fichiers (P-01, P-03, P-06, P-08) | F-03, P-01, P-03, P-06, P-08 | S-05 (un défaut né de l'interaction entre loi et vérin) |
| A-2 | **Contrat explicite entre la loi de commande et la couche vérin**, avec unités et fréquence documentées. La loi ne connaît ni PWM ni seuils ; la couche vérin ne connaît ni cap ni gains | F-03, F-05, P-03 | S-05, S-06 |
| A-3 | **La couche vérin est testable seule** (réponse à un échelon, zone morte de démarrage, rampes), avant d'être couplée à la loi | F-11, F-12, P-06 | S-03, S-05 |
| A-4 | **L'anti-emballement de l'intégrale se fonde sur la saturation réelle de la commande**, pas sur le fait que la barre « n'est pas encore arrivée » | F-08 | S-05 |
| A-5 | **Étalonner la relation vitesse (ou PWM) → mouvement réel** et l'utiliser dans la couche vérin, comme le fait pypilot | P-07, F-12 | S-04 ; plan M2, M3 |
| A-6 | **Ne pas poursuivre la houle** : la bande de fréquence de la houle est traitée par filtrage ou zone morte, pas par la barre | F-17, P-09 | S-07, S-08 |
| A-7 | **Le temps de marche du vérin est une grandeur surveillée et bornée** (cycle de service de 20 % de la fiche) | F-14, P-08 | S-08 |
| A-8 | **Architecture exécutable sur ordinateur** : la loi de commande et la couche vérin se compilent et se simulent hors matériel, avec le même code que le firmware (équivalent des modes `SHIP_SIM` / `VIRTUAL_ACTUATOR`) | F-18 | V0 du banc commun |
| A-9 | **Journalisation** de cap, consigne, barre cible, barre mesurée, PWM, courant, avec horodatage | F-19, plan F5 | plan § 4 |
| A-10 | **Chaque gain et chaque seuil porte sa source et son statut** (mesuré, hypothèse, repris de tel fichier) | F-06, F-11, F-16, P-02 | rapport § 8 |

## 4. Décisions à prendre

Elles ne sont **pas** prises : chaque ligne propose une recommandation, mais le choix revient à Mathieu.

| ID | Question | Options | Recommandation proposée et raison | Pour trancher |
|---|---|---|---|---|
| D-1 | Base logicielle | (a) partir de Fenix et réécrire ce qui se révèle défectueux ; (b) réécriture complète inspirée des deux projets ; (c) pypilot sur Raspberry Pi | **(a)**, cohérente avec le `README.md` (« base de départ DIY : Fenix », Mega + vérin + IMU) : le matériel visé et le code de bas niveau (IMU, PWM/DIR, potentiomètre) existent déjà (F-13, F-15). Bascule vers (b) pour la couche vérin et l'intégrale si les tests F6 à F9 confirment les défauts simulés | plan F6–F9, M1–M3 |
| D-2 | Contrat loi → vérin | (a) **position cible** en degrés de barre + vitesse maximale (Fenix, F-04) ; (b) **vitesse normalisée** [−1 ; 1] (pypilot, P-03) | **(a)**, parce que le matériel de Mathieu a un potentiomètre de barre (le vérin n'a pas de retour propre), parce que la position est mesurable et se teste seule (A-3), et parce que la variation de vitesse de 5 à 10 % entre exemplaires est absorbée par la boucle de position. Contre-point : en pypilot, le terme P agit comme un intégrateur, ce qui évite un ajustement séparé de l'intégrale (S-03 montre cependant le coût du servo à impulsions) | plan Q4, F8 ; banc commun E0–P4 |
| D-3 | Traitement de l'intégrale | (a) comme Fenix (gel quand la barre est « occupée ») ; (b) anti-emballement par saturation réelle ; (c) pas d'intégrale (pypilot `basic`, P-02) | **(b)** (principe A-4) ; (c) reste la solution de repli la plus simple | banc commun P1, P3 ; plan F8 |
| D-4 | Mise à l'échelle par la vitesse du bateau | (a) comme Fenix (F-06) ; (b) aucune (pypilot) ; (c) inverse (gains ÷ f²), hypothèse non lue dans le code | **À décider après test** : le facteur codé dégrade la régulation à basse vitesse dans mon modèle (S-01). La vitesse mesurée existe déjà dans Fenix (F-07). Je ne recommande pas (c) sans validation sur bateau | plan F9, M7 |
| D-5 | Source du modèle de bateau | (a) identification en ligne (Fenix, F-16) ; (b) gains empiriques (pypilot, P-02) ; (c) mesure de T et K puis gains fixes | **(c) d'abord** (plan M7) : c'est la valeur la plus manquante des simulations ; (a) se reconsidère ensuite | plan M7 |
| D-6 | Gestion de la houle | (a) filtre de cap seul ; (b) zone morte ; (c) observateur de vagues (Fenix, F-17) ; (d) rien | **À décider** : la preuve S-07 est un résultat de modèle (houle supposée) ; mesurer d'abord le bruit et la houle réels (M8) | plan M8 ; banc commun P2 |
| D-7 | Interfaces utilisateur et communication | Application Bluetooth + NMEA (Fenix), SignalK / web (pypilot), à définir | **Hors périmètre de ce document** ; à traiter après D-1 à D-6 | — |
| D-8 | Électronique de puissance et protections | Driver PWM + DIR (Cytron MD10C recommandé dans le projet), fusible, arrêt d'urgence | Le driver doit tenir le courant du vérin (10 A à pleine charge d'après la fiche) avec marge : **capacité du driver À VÉRIFIER** ; fusible et coupure d'urgence exigés (plan § 1) | plan M5, Q6 |

## 5. Architecture en couches (proposition)

```
  Capteurs                Estimation            Commande               Vérin                  Supervision
 ┌───────────┐         ┌──────────────┐     ┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐
 │ IMU       │ cap,    │ Cap filtré,  │     │ Consigne de cap │    │ Position cible → │    │ Modes,       │
 │ ICM20948  ├────────►│ vitesse de   ├────►│ (+ modèle de    ├───►│ PWM / sens,      │    │ alarmes,     │
 │ (F-15)    │ rotation│ rotation     │     │ référence ?)    │ δ* │ rampes, seuils,  │    │ limites de   │
 └───────────┘         │ (P-09)       │     │ Loi de cap → δ* │    │ attente inversion│    │ barre, temps │
 ┌───────────┐ barre   └──────────────┘     │ (PID, A-4)      │    │ (F-11, F-12)     │    │ de marche    │
 │ Potentio- │ mesurée                      └─────────────────┘    └────────┬─────────┘    │ (A-7)        │
 │ mètre A8  ├──────────────────────────────────────────────────────────────┤ PWM + DIR    └──────┬───────┘
 │ (F-13)    │                                                              ▼  (D6, D7)           │
 └───────────┘                                                    ┌──────────────────┐            │
 ┌───────────┐ courant                                            │ Driver + vérin   │◄───────────┘
 │ Courant A9├───────────────────────────────────────────────────►│ FA-HF-100-12     │  coupure
 │ (F-13/14) │                                                    └──────────────────┘
 └───────────┘
```

| Couche | Entrées → sorties (unités) | Source dans Fenix | Source dans pypilot | Point de décision |
|---|---|---|---|---|
| Capteurs | IMU, potentiomètre, courant → valeurs brutes horodatées | `DevICM20948.h`, `Fenix_config.h:105-117` | `boatimu.py`, `rudder.py` | — |
| Estimation | brutes → cap (°), vitesse de rotation (°/s) filtrés | `ICM20948AHRS.cpp` (Mahony) | `boatimu.py:65,117,233` (Kalman) | D-6 |
| Commande | cap, consigne → **angle de barre cible δ\*** (°) | `PID_v1_ext.cpp`, `ActuatorManager.cpp:138-158` | `pilots/basic.py`, `pilots/pilot.py` | D-3, D-4, D-5 |
| Vérin | δ\*, barre mesurée → PWM (0–255) et sens | `ActuatorManager.cpp:253-490` | `servo.py:367-470` | D-2 |
| Supervision | tout → modes, alarmes, coupure | `Autopilot.cpp`, `ActuatorManager.cpp:225` | `autopilot.py`, `servo.py:272,731-735` | D-8 |

Interfaces à documenter pour chaque flèche (principe A-2) : grandeur, unité, fréquence, domaine de validité, comportement si la
donnée manque. **À rédiger** avant de coder, une fois D-2 tranchée.

## 6. Exigences de validation

Chaque exigence cite la méthode (un test du plan ou une simulation) et son **statut**. Aucun seuil n'est inventé : quand il
dépend de l'usage visé, la colonne « Critère » dit « à fixer par Mathieu » et propose une référence relative.

| ID | Exigence | Méthode | Critère | Statut |
|---|---|---|---|---|
| VR-01 | La géométrie du montage est mesurée et cohérente | plan M1 | Les 4 cotes consignées ; l'incohérence 589 / 610 / 460 mm est résolue | À faire |
| VR-02 | La vitesse réelle du vérin en °/s de barre est connue | plan M2, Q2 | Écart avec 7,4 °/s consigné ; si supérieur à 10 %, les simulations sont refaites | À faire |
| VR-03 | Le PWM minimal de démarrage est connu, dans les deux sens | plan M3 | Valeur consignée ; entrée de la couche vérin (A-5) | À faire |
| VR-04 | La course et l'autorité de barre couvrent l'usage visé | plan M4, Q3 | Angle de barre atteignable ≥ valeur à fixer par Mathieu (≈ ±20° suppose ±201 mm de course) | À faire |
| VR-05 | Le courant reste sous le seuil de blocage et sous la capacité du driver | plan M5, Q3 | Courant maximal mesuré < seuil de blocage configuré < capacité du driver (**À VÉRIFIER**) | À faire |
| VR-06 | Le cycle de service du vérin est respecté en usage | plan M6, Q5 ; banc commun | Temps de marche ≤ 20 % (fiche ; durée de référence du cycle non précisée) en houle (P2) et en P4 | À faire |
| VR-07 | La couche vérin positionne sans zone morte de démarrage inattendue | plan F7, F8, Q4 | Échelons de 1°, 2°, 5°, 10° atteints à une tolérance à fixer ; seuils d'arrêt et de redémarrage mesurés | À faire |
| VR-08 | L'intégrale ne reste pas gelée sans cause | plan F8 ; banc commun P1, P3 | Écart de cap stationnaire sous vent constant ≤ valeur à fixer ; comparaison à pypilot par défaut (RMS 0,93° en P1) | À faire |
| VR-09 | La fréquence d'exécution de la couche vérin est connue et documentée | plan F6 (moniteur `LOOP_FREQ`, F-19) | Appels par seconde consignés ; durée réelle d'une rampe de 0 à 255 en découle | À faire |
| VR-10 | Les cinq indicateurs sont dans les limites voulues | banc commun E0, P1–P4 ; plan Q2–Q5 | Temps d'établissement (±0,5°), dépassement, RMS, activations/min, énergie : **seuils à fixer par Mathieu** | À définir |
| VR-11 | La houle n'est pas poursuivie inutilement | banc commun P2 ; plan Q5 | Activations/min ≤ valeur à fixer, sans dégradation du RMS par rapport au vérin immobile (RMS 1,08° dans mon modèle) | À faire |
| VR-12 | Défauts capteur et coupure sont sûrs | plan Q6 ; essais d'injection de défaut (à écrire) | Perte de l'IMU ou du potentiomètre, ou coupure d'alimentation : le vérin s'arrête, la barre reste manœuvrable à la main | À définir |
| VR-13 | Aucune régression du banc de simulation | banc commun V0 | Écart de cap de 0,00° avec les scripts de référence ; tout changement de loi repasse E0 et P1–P4 | Fait une fois (SIMULÉ) |
| VR-14 | Le modèle de bateau est mesuré | plan M7 | T et K consignés ; simulations refaites avec ces valeurs | À faire |
| VR-15 | Le bruit capteur est mesuré | plan M8 | Écart-type du cap et de la rotation consigné, remplaçant 0,2° et 0,1 °/s | À faire |
| VR-16 | La calibration de l'IMU est documentée | outil `Fenix_ICM_20948_Cal` (source n° 209) ; plan à compléter | Procédure et erreur de cap statique résiduelle, seuil à fixer par Mathieu | À définir |
| VR-17 | Chaque paramètre est traçable | revue du code et des fiches | Chaque gain et seuil porte source et statut (principe A-10) | À définir |

## 7. Matrice de traçabilité

| Choix (principe ou décision) | Constats | Preuves | Exigences | Tests |
|---|---|---|---|---|
| A-1 séparation en quatre responsabilités | F-03, P-01, P-03, P-06, P-08 | S-05 | VR-17 | revue de conception |
| A-2 contrat loi / vérin | F-03, F-05, P-03 | S-05, S-06 | VR-09 | F6 |
| A-3 couche vérin testable seule | F-11, F-12, P-06 | S-03, S-05 | VR-07 | F7, F8, Q4 |
| A-4 intégrale anti-emballement par saturation | F-08 | S-05 | VR-08 | banc P1, P3 ; F8 |
| A-5 étalonnage vitesse / PWM → mouvement | P-07, F-12 | S-04 | VR-02, VR-03 | M2, M3 |
| A-6 ne pas poursuivre la houle | F-17, P-09 | S-07, S-08 | VR-11, VR-15 | banc P2 ; M8 |
| A-7 temps de marche borné | F-14, P-08 | S-08 | VR-06 | M6, Q5 |
| A-8 exécutable sur ordinateur | F-18 | V0 | VR-13 | banc V0 |
| A-9 journalisation | F-19 | — | VR-09, VR-10 | F5 |
| A-10 paramètres traçables | F-06, F-11, F-16, P-02 | — | VR-17 | revue |
| D-1 base Fenix | F-13, F-15, README | S-05, S-06 | VR-07, VR-09 | F6–F9 |
| D-2 position cible | F-04, F-13, P-03 | S-03, S-05 | VR-07 | Q4, F8 |
| D-3 intégrale | F-08, P-02, P-05 | S-05 | VR-08 | banc P1, P3 |
| D-4 échelle de vitesse | F-06, F-07 | S-01 | VR-10 | F9, M7 |
| D-5 modèle de bateau | F-16, P-02 | S-01 | VR-14 | M7 |
| D-6 houle | F-17, P-09 | S-07 | VR-11, VR-15 | M8, banc P2 |
| D-8 électronique | F-13, F-14, P-08 | fiche du vérin | VR-05, VR-12 | M5, Q6 |

## 8. Ce qui reste inconnu ou fragile

1. **Le firmware réel de Fenix n'a jamais été exécuté ici.** Mes simulations de Fenix omettent le modèle de référence,
   l'anticipation du vent et l'observateur de vagues : les points S-05 à S-09 sont des alertes à vérifier, pas des défauts avérés.
2. **Le servo « réel » de pypilot est mon portage** de `do_command` ; le firmware `motor.ino` n'est pas simulé.
3. **Les paramètres physiques sont des hypothèses** : vitesse du vérin (7,4 °/s), T et K du bateau, bruit capteur, houle, vent,
   courant du vérin (rapport § 8, § 14.5).
4. **Le rapport `_ratio` du potentiomètre** (seuils d'arrêt et de redémarrage de Fenix) dépend de l'étalonnage : 0,3° / 1,2° ou
   0,6° / 2,4° selon l'hypothèse (rapport § 14.2).
5. **Les cotes du montage** ne se recoupent pas encore (rapport § 10.3).
6. **Pelagic Autopilot** est cité comme référence du projet mais son code n'est pas disponible : l'architecture se fonde sur Fenix
   et pypilot, pas sur Pelagic.

## 9. Prochaines étapes possibles (aucune décidée)

Dans l'ordre qui réduit le plus d'incertitude pour le moins de risque :

1. Mesures à l'établi M1 à M5 (plan § 3) : elles fixent le vérin, la géométrie et le PWM de démarrage.
2. Tests F6 à F9 (plan § 4 et § 10.8) : ils confirment ou infirment les alertes S-05 et S-06 sur le vrai firmware.
3. Décider D-1 à D-4 à la lumière de ces résultats.
4. Rédiger les interfaces de couches (§ 5) puis fixer les seuils des exigences VR-04, VR-08, VR-10, VR-11.
5. Déposer dans le dépôt les scripts de simulation, pour que les preuves S-xx soient rejouables.

## 10. Avertissement

Ce document est une proposition non relue par Mathieu. Les numéros de ligne valent pour les commits cités et peuvent changer
dans d'autres versions. Comme le reste du dépôt : à revalider contre la documentation d'origine et sur le matériel avant tout
usage — un pilote mal réglé lâche la barre en mer.
