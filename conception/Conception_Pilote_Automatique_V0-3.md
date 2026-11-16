
# Pilote automatique Capri 22 — cahier de conception V0.3

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `03 - Analyses/Conception_Pilote_Automatique_V0-3.md` (type `analyse`, statut `en-cours`). Remplace la V0-2 (`Conception_Pilote_Automatique_V0-2.docx`, conservée) pour la planification. Effet des DEC du 2026-11-16 sur D-01 à D-11 : voir `conception/cahier-des-besoins-et-decisions-2026-11-16.md`, section B.5. Les noms entre « » désignent des notes du vault.

**Date :** 2026-10-30  
**Statut documentaire :** `[Proposition]` — aucune décision technique nouvellement `[Validé]` par le propriétaire.  
**Portée :** Catalina Capri 22 à barre franche, réseau de bord 12 V CC, pilote expérimental à vérin linéaire, développement et validation progressifs.  
**Remplace pour la planification :** `Conception_Pilote_Automatique_V0-2.md` (conservé intact ; V0-1 reste l'historique antérieur).  
**Documents coordonnés :** `Plan_execution_pilote_Capri22_V0-5.md`, `Qualification_SailSim_Capri22_V0-2.md`, `BOM_pilote_automatique_V0-2.xlsx` et `.csv` (dépôt GitHub, `conception/`), `Correspondance_architecture-2026-10-28_vers_V0-2.md`.

> **Rapprochement du 2026-11-16.** Les décisions DEC-003 à DEC-008, acceptées par Mathieu le 2026-11-16, précisent le périmètre fonctionnel (vent et route en extension, interface et liaisons du socle, vérin linéaire seulement). Leur effet sur D-01 à D-11 est tracé dans « Cahier des besoins du pilote », section 5. Aucune décision D-xx n'est tranchée par ce rapprochement. Le corps de ce document n'a pas été modifié.

> **Principe de gouvernance.** Les étiquettes « confirmé par lecture du code », « simulé », « mesuré », « inféré » et « à vérifier » qualifient les preuves ; elles ne constituent jamais une approbation de conception. Seul le propriétaire attribue `[Validé]`. Les recommandations ci-dessous sont `[Proposition]`.

## 0. Delta V0.3 (2026-10-30)

Décisions **documentaires** de Mathieu du 2026-10-30, prises sur les lacunes L-1 à L-12 de `Correspondance_architecture-2026-10-28_vers_V0-2.md`. Aucune décision **technique** n'est validée par ce delta, sauf mention.

| Lacune | Décision de Mathieu | Où dans V0.3 |
|---|---|---|
| L-1 | Ajouter D-11 « Traitement de l'intégrale », statut `[À décider]` | §9, §10 |
| L-2 | Phrase dans D-07 : mesurer T et K avant l'identification en ligne Fenix | §9 |
| L-3 | D-02 reste `[À décider]` et mentionne la recommandation antérieure « position cible » | §9 |
| L-5 | Citer l'outil `Fenix_ICM_20948_Cal` dans D-04 | §9 |
| L-7 | Règle de traçabilité par paramètre | §4.3 |
| L-10 | Préfixe `ARCH:` pour les identifiants de l'ancien document | §4.3, §11 |
| L-12 | **Validé par Mathieu** : le Firgelli FA-HF-100-12 est un vérin linéaire **générique de référence** ; modèle précis choisi plus tard d'après le pourcentage d'utilisation en charge. La mécanique ST1000+ **sort du projet** (projet séparé envisagé après les essais en mer avec le vérin linéaire). Ses cotes de montage restent la référence géométrique de départ. | §6, §9 (D-05) |
| L-4, L-6, L-8, L-9 | Mesures, grilles d'essai et archivage des scripts | `Plan_execution_pilote_Capri22_V0-5.md` |
| L-11 | Garder `conception/` et supprimer la copie à la racine du dépôt (geste de Mathieu) | — |

Non révisés par ce delta : `Qualification_SailSim_Capri22_V0-2.md` et la BOM V0.2 (lire l'article M01B Firgelli comme modèle générique). Le `.docx` n'a pas été régénéré : seule la version Markdown existe en V0.3.

## 1. Synthèse et delta de version

La V0.1 proposait un contrôleur PD/gyro et du matériel de prototypage ESP32-S3 + BNO085 + pont en H Pololu. La V0.2 **retire le statut de solution privilégiée à ces choix** : ils deviennent des options, parce que la lecture du code Fenix et PyPilot révèle des architectures plus élaborées qui n'ont pas été comparées équitablement. La V0.2 reconnaît également l'existence d'un simulateur open source candidat, `herostrat/sailsim`, **dont le moteur physique et l'intégration PyPilot ne sont pas encore qualifiés dans notre environnement**.

**Finalité inchangée :** maintenir le cap sur un voilier de taille moyenne avec un compromis documenté entre précision de route/cap, consommation, fréquence de démarrage du vérin, effort mécanique, robustesse et sécurité.

**Décisions retenues au niveau de la méthode seulement** (toujours proposées) : (A) mesurer bateau et actionneur ; (B) conserver les contrôleurs originaux comme références de comparaison ; (C) séparer estimation, commande de cap, actionnement et supervision ; (D) différer toute commande définitive de matériel jusqu'aux portes de décision G1/G4.

| Modification V0.2 | Motif | Conséquence |
|---|---|---|
| PD/gyro relégué au **contrôleur de référence minimal** | PyPilot Basic contient P, D, DD, PR, FF ; Fenix combine modèle de référence, PID et FF | Comparer les implémentations d'origine avant de concevoir une troisième loi |
| Interface moteur double : **position Fenix / puissance-vitesse PyPilot** | Un convertisseur direct entre les deux modifie le sens physique de la commande | Un adaptateur qui préserve chaque sémantique sur un actionneur physique commun |
| Capteur de position de barre prioritaire | Vérin Firgelli FA-HF-100-12 envisagé sans retour intégré | Prévoir retour externe, calibration et tests de vraisemblance |
| Qualification du simulateur exigée avant classement | SailSim teste une commande PyPilot comme un angle instantané ; patch GPS-track à la place de l'IMU | G2 obligatoire ; ne pas comparer les performances des pilotes avant correction |
| Vérin soumis à une porte thermique | Cycle de service annoncé 20 %, conditions de référence non confirmées | Conception et achats moteur suspendus jusqu'à caractérisation |
| Sécurité indépendante du logiciel de régulation | Actionneur peut rendre la barre difficile à manœuvrer même hors tension | Arrêt moteur matériel, déconnexion mécanique et supervision indépendante |

## 2. Périmètre, hors périmètre et objectifs

**Périmètre :** maintien de cap compas, arrêt/veille, reprise manuelle, essais de modulation de barre, instrumentation, journalisation, banc SIL, tests d'injection de défaut. L'interface mobile ou la cartographie n'est pas nécessaire à la fermeture de la boucle de contrôle.

**Hors périmètre V0.2 :** pilote commercial certifié, navigation autonome sans veille humaine, suivi de waypoints en mer, mode vent opérationnel, conception de PCB de production, garantie d'aptitude à la navigation. Les modes vent et trajectoire restent des objets de recherche.

**Objectifs sans seuil inventé :** précision RMS de cap, maxima transitoires, temps d'établissement, cycles moteur/h, temps sous tension, Wh/h, distance parcourue par le vérin, température, taux de saturation, tests de reprise manuelle et défauts. Les seuils d'acceptation sont à fixer avec le propriétaire après mesure du bateau.

## 3. Architecture fonctionnelle — quatre responsabilités

```text
      ┌────────────────────┐     ┌──────────────────────────┐
      │ Capteurs / mesures │ ──► │ ESTIMATION : cap, lacet, │
      │ IMU, GPS, vent,    │     │ position barre, qualité │
      │ barre, courant     │     └────────────┬─────────────┘
      └────────────────────┘                  │
                                            ▼
      ┌────────────────────────────────────────────────────────┐
      │ COMMANDE CAP : Fenix original | PyPilot Basic original │
      │ | référence PD ; consigne, modèles et états propres    │
      └──────────────────────────┬─────────────────────────────┘
                                 │
                   ┌─────────────┴──────────────────┐
                   │ demandes typées :             │
                   │ position cible OU motor drive  │
                   └─────────────┬──────────────────┘
                                 ▼
      ┌────────────────────────────────────────────────────────┐
      │ ACTIONNEMENT : conversion physique, rampes, course,   │
      │ PWM/sens, mesure, délais, états et limites             │
      └──────────────────────────┬─────────────────────────────┘
                                 ▼
                         Vérin → safran → bateau

      SUPERVISION INDÉPENDANTE → autorisation énergie moteur,
      watchdog, capteurs périmés, arrêt, défaut, réarmement manuel.
```

### 3.1 Contrats de données proposés

| Signal | Unité | Source | Contrôle obligatoire |
|---|---|---|---|
| `heading_rad` | rad, angle replié | IMU/estimation | qualité, âge, alignement, cohérence |
| `yaw_rate_rad_s` | rad/s | gyroscope | signe, biais, bruit, âge |
| `target_heading_rad` | rad | utilisateur/mode | angle replié, horodatage |
| `speed_through_water_m_s` | m/s | loch ou estimation validée | ne pas substituer SOG sans indication |
| `rudder_angle_rad` | rad | capteur de barre | plage, calibration, plausibilité |
| `motor_drive_norm` | [-1, +1] | stratégie PyPilot | commande de puissance/vitesse, **pas** angle de barre |
| `rudder_target_rad` | rad | stratégie Fenix | consigne de position, **pas** vitesse moteur |
| `motor_pwm`, `motor_dir` | 0…255, signe | actionneur | défauts, watchdog, driver |
| `motor_current_a`, `bus_voltage_v` | A, V | carte moteur | surintensité, sous-tension |
| `t_sim_s`, `t_wall_s` | s | banc de test | identifier deux horloges distinctes |

**Convention à décider :** signe bâbord/tribord et références géométriques. Les adaptateurs consignent explicitement conversions degrés↔radians, inversion de signe et offsets. Une donnée absente ou périmée provoque un état sûr : **pas de maintien indéfini de la dernière commande active**.

### 3.2 Principes de sûreté

- Une coupure électrique ne doit pas être confondue avec une libération de la barre : **déconnexion mécanique rapide testée** et accessible sous efforts raisonnables.
- Contacteur/autorisation moteur à repos sûr, STOP matériel indépendant du logiciel, fusible dimensionné selon câbles et appel de courant ; comportement au redémarrage = inactif.
- Superviseur indépendant de la boucle de cap : durée de validité capteurs, position impossible, surintensité, température, temps de marche, tension, perte de communication, CPU bloqué.
- Fins de course et protections mécaniques cohérentes ; jamais butée du gouvernail utilisée pour arrêter systématiquement le vérin.
- Pas de navigation sans veille humaine sur la base de ce dossier ; essais au banc puis à quai et en mer surveillée.

## 4. Références logicielles et fidélité

### 4.1 Fenix — version de référence

**Référence étudiée :** `spascual90/Fenix`, commit `b8410e50fa19bbad649b0d765cecf8aec2a25bc4` mentionné dans l'audit fourni. À recaler et figer dans les fichiers de travail avant exécution.

Fichiers utiles : `Fenix.ino`, `Autopilot.cpp`, `ActuatorManager.cpp`, `PID_v1_ext.cpp`, `FossenReferenceModel.cpp`, `ReferenceFeedforward.cpp`, `WindFeedforward.cpp`, `WavePassiveObserver.cpp`, `OnlineNomotoIdentifier.cpp`, `Fenix_config.h`.

**Constats de code / audit, pas performances prouvées :** modèle de référence Fossen, feedforward de consigne et de vent, observateur de vagues, identification Nomoto, logique d'actionnement avec hystérésis de redémarrage 4× le seuil d'arrêt, rampes et pause à l'inversion. Le PID est conditionné par un pas d'environ 100 ms ; la fonction d'actionnement peut être appelée à la fréquence de la boucle principale. Vérifier précisément les fonctions actives, les cadences et les unités dans le binaire testé.

**Interdiction méthodologique :** présenter les anciennes courbes « Fenix codé » comme performances du firmware complet ; elles omettaient plusieurs modules. Comparer d'abord Fenix tel quel, puis les variantes à partir d'une branche expérimentale séparée.

### 4.2 PyPilot — version de référence

**Référence étudiée :** `pypilot/pypilot`, commit `fdff88ffe59c` selon l'audit fourni (hash abrégé ; compléter avant gel). Fichiers : `pypilot/pilots/basic.py`, `pilots/pilot.py`, `autopilot.py`, `servo.py`, `boatimu.py`, `rudder.py`, `arduino/motor/motor.ino`.

**Constats :** Basic calcule une commande normalisée utilisant P, D, DD, PR et FF ; le terme intégral Basic est commenté. La couche servo applique ses propres temporisations et étalonnages. Les schémas matériels sont dans `pypilot/pypilot_schematics` et ne doivent pas être confondus avec le code du régulateur.

**Interdiction méthodologique :** traiter `servo.command` comme l'angle instantané du safran ; il faut conserver la chaîne de commande moteur et sa dynamique.

### 4.3 Stratégies d'évaluation

- **R0 — référence théorique :** PD/gyro minimal, uniquement pour vérifier la physique et les métriques.
- **R1 — Fenix original :** code source réel et modules actifs selon profil, paramètres consignés.
- **R2 — PyPilot Basic original :** vrai logiciel, comportement servo conservé, IMU simulée cohérente.
- **R3 — variantes optimisées :** seulement une fois les références R1 et R2 reproductibles ; modifications tracées et isolées.

Chaque résultat rapporte `source_sha`, `patch_sha`, `config_sha`, `model_sha`, `scenario_sha`, graine, unités, pas numérique, horloge et version du calculateur de métriques.

**Traçabilité par paramètre (V0.3, L-7) :** chaque gain et chaque seuil porte sa source et son statut, par exemple « P = 0,003, repris de `pypilot/pilots/basic.py:19`, statut hypothèse ». Rien n'est à remplir tant qu'aucun paramètre n'est fixé.

**Identifiants de l'ancien document (V0.3, L-10) :** les identifiants de `conception/architecture-pilote-proposition-2026-10-28.md` (dépôt) s'écrivent avec le préfixe `ARCH:` (par exemple `ARCH:F-08`, `ARCH:Q6`), car plusieurs étiquettes y ont un autre sens qu'ici (Q1, M2, P1, D-3).

## 5. Simulateur SailSim candidat — qualification préalable

**Candidat :** `herostrat/sailsim`, révision lue `ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0`, version du projet 0.1.0 selon `pyproject.toml` ; **non exécuté dans ce travail**. Le moteur comporte un modèle 3-DOF et une extension 6-DOF, des profils de yacht, scénarios, tests et sorties CSV/JSON.

**Bloquants repérés dans le code, avant comparaison :**

1. Dans `src/sailsim/autopilot/pypilot.py`, `servo.command` est affectée directement à une position `rudder_angle = -servo_cmd * rudder_max`, sans intégration de vitesse/durée et sans modèle de moteur.
2. Dans `docker/pypilot/apply_patch.py`, l'absence de cap IMU conduit à prendre `gps.track`, non équivalent au cap vrai/magnétique en dérive/courant.
3. Le modèle avance en pas simulé (`core/runner.py`), mais PyPilot externe utilise son temps d'exécution ; la synchronisation et les délais doivent être mesurés.
4. Le Dockerfile clone PyPilot sans commit figé. Les tests unitaires de l'adaptateur utilisent des interfaces simulées (« mocks ») ; ils ne démontrent pas une exécution complète avec IMU.
5. En déconnexion, l'adaptateur peut conserver la dernière commande moteur : créer un timeout de sécurité et un test de non-maintien de commande active.

**Qualification imposée :** Q0 physique et reproductibilité → Q1 interface PyPilot corrigée et validée → Q2 Fenix en SIL avec code d'origine → Q3 modèle Capri 22 et actionneur calibrés → Q4 comparaison. Détails, procédures et critères dans `Qualification_SailSim_Capri22_V0-2.md`.

**Alternative si échec :** modèle de giration Nomoto mesuré, simulateur discret minimal déterministe avec tests, sans prétention 6-DOF.

## 6. Sous-système mécanique et électrique

**Bateau :** Catalina Capri 22 ; le montage évoque des cotes du Raymarine ST1000+ A = 589 mm, B = 460 mm et cote hors-tout de référence 610 mm. Elles ne prouvent pas l'adéquation d'un vérin tiers. Mesurer les points réels, la course angle→longueur, le bras de levier et les angles des rotules.

**Ajout V0.3 (L-12, décision de Mathieu du 2026-10-30) :** la mécanique ST1000+ est retirée du projet ; sa réutilisation fera l'objet d'un projet séparé après les essais en mer avec le vérin linéaire. Les cotes de montage ST1000+ ci-dessus restent la **référence géométrique de départ** ; les mesures M1 sur le Capri 22 font autorité.

**Vérin candidat :** vérin linéaire 12 V **générique** ; le Firgelli FA-HF-100-12 sert de modèle de référence (V0.3, L-12) et le modèle précis sera choisi d'après le pourcentage d'utilisation en charge mesuré (lot M2). Fiche de référence : Firgelli FA-HF-100-12 (suffixe de course **à confirmer**), 12 V, puissance et vitesse dépendantes de la charge ; annoncé sans capteur de position intégré et avec cycle de service 20 %. La fenêtre temporelle, les conditions de charge et les températures admissibles doivent être confirmées par documentation fabricant. **Aucune conclusion d'aptitude à une utilisation continue du pilote.**

**Chaîne de puissance candidate :** batterie 12 V → fusible et câblage adaptés → autorisation/coupure matérielle → driver moteur réversible dimensionné → vérin, avec alimentation capteur/logique filtrée séparée. Pololu G2 et Cytron MD10C restent *des options*, pas un achat décidé. Vérifier contraintes de courant continu/pointe, thermique, protections réelles, EMI, corrosion et tension batterie.

**Retour de barre :** potentiomètre/capteur angulaire externe à étalonner à la barre, avec détection fil coupé et valeurs hors plage. Ne pas confondre capteur sur actionneur et mesure de barre si le montage présente du jeu.

**Calculateur et IMU :** Arduino Mega (compatibilité Fenix) ou ESP32-S3 (reconception) ; ICM-20948 (chemin Fenix) ou BNO085 (option précédente). Aucune combinaison processeur/IMU n'est validée. Le choix dépend des essais C1/C2 et de la qualification des chaînes d'acquisition.

## 7. Modèle du Capri 22 — identification mesurée plutôt que supposée

Modèle de premier ordre pour l'analyse d'asservissement : `T * dr/dt + r = K * delta + d(t)` ; T en s, r en rad/s, delta en rad, K en s^-1 (convention de signe documentée). Identifier T, K et délais à partir de mouvements **manuels** et d'un capteur de barre, en séparant calibration/validation.

Le profil J/24 déjà présent dans SailSim peut servir de **test de qualification du moteur physique**, pas de substitut au Catalina Capri 22. Créer `capri22_provisoire.toml` avec plage d'incertitude, puis remplacer les coefficients par mesures. La confiance dans un modèle 6-DOF dépendra d'une calibration bien plus exigeante que celle de Nomoto.

## 8. Exigences et portes de décision

| ID | Exigence / porte | Critère de passage (à documenter) | Responsable |
|---|---|---|---|
| G0 | Sources figées | Commits complets, licence, versions et configurations enregistrés | Agent + propriétaire |
| G1 | Mécanique et vérin admissibles | Course, efforts, déconnexion, thermique et courant compatibles et démontrés | Propriétaire + mesures |
| G2 | SailSim qualifié pour le périmètre | Tests de physique, convergence numérique, reproductibilité, limites publiées | Agent + revue |
| G3 | Fenix/PyPilot fidèles | Oracles de sortie, capteurs et horloges conformes ; aucune commande « transmutée » | Agent + revue |
| G4 | Comparaison valide | Scénarios communs, incertitude, coûts énergétiques, sécurité et métriques enregistrés | Propriétaire |
| G5 | Prototype navigable expérimental | Failsafe, reprise manuelle et essais banc/quai réussis ; essais mer surveillés | Propriétaire |

**G1 peut être menée en parallèle de G2/G3, mais G4 dépend de G1+G2+G3. G5 dépend de G4 et des essais matériels.** Aucun seuil de précision ou de durée n'est présenté comme validé avant fixation par le propriétaire.

## 9. Décisions ouvertes (registre unique)

| ID | Question | Options et recommandation provisoire | Statut | Dépendance |
|---|---|---|---|---|
| D-01 | Base code embarquée | Fenix Mega / adaptation modulaire / réécriture ; **Fenix candidat initial, non retenu définitivement** | `[À décider]` | G3, G4 |
| D-02 | Contrat contrôleur→moteur | Évaluer position et vitesse native ; ne pas normaliser les deux prématurément — *recommandation antérieure (ARCH:D-2, 2026-10-28) : position cible + vitesse maximale, parce que le potentiomètre de barre mesure la position ; non retenue à ce stade (V0.3, L-3)* | `[À décider]` | G3, G4 |
| D-03 | Loi de cap | R0 PD minimal, R1 Fenix, R2 PyPilot Basic ; sélection après essais | `[À décider]` | G4 |
| D-04 | Acquisition IMU | ICM-20948 / BNO085 / autre ; essais EMI et calibration ; calibration avec l'outil `Fenix_ICM_20948_Cal` (source n° 209) (V0.3, L-5) | `[À décider]` | G3, G5 |
| D-05 | Vérin | Vérin linéaire 12 V générique (référence Firgelli FA-HF-100-12) ; modèle précis d'après le pourcentage d'utilisation en charge mesuré (M2) ; vérin nautique ou à service continu si la thermique est insuffisante. Mécanique ST1000+ hors projet (V0.3, L-12) | `[À décider]` | G1 |
| D-06 | Driver moteur | Cytron / Pololu / carte PyPilot ; courant, défauts, sécurité | `[À décider]` | G1 |
| D-07 | Gains selon vitesse | Fenix natif / gains fixes / autres lois ; ne rien adopter sans preuve ; mesurer T et K (lot D1) **avant** d'utiliser l'identification en ligne de Fenix (V0.3, L-2, ARCH:D-5) | `[À décider]` | G4 |
| D-08 | Filtrage houle | cap filtré / observateur Fenix / autres ; étudier effet sur activité moteur | `[À décider]` | G4 |
| D-09 | Simulateur principal | SailSim si G2 ; sinon banc Nomoto simple | `[À décider]` | G2 |
| D-10 | Communication/interface | Panneau local et arrêt matériel avant Bluetooth/NMEA/SignalK | `[À décider]` | G5 |
| D-11 | Traitement de l'intégrale | (a) gel tant que la barre est « occupée » (Fenix, ARCH:F-08) ; (b) anti-emballement fondé sur la saturation réelle de la commande ; (c) pas d'intégrale (pypilot `basic`, ARCH:P-02) — *recommandation antérieure (ARCH:D-3) : (b), avec (c) en repli* (ajout V0.3, L-1) | `[À décider]` | G3, G4 |

## 10. Matrice de traçabilité essentielle

| Preuve | Décision / exigence | Test ou document |
|---|---|---|
| Fenix `ActuatorManager.cpp`, `PID_v1_ext.cpp` | D-02, D-03, G3 | F6–F9 / Q2 ; `Plan_execution...V0-4.md` |
| PyPilot `pilots/basic.py`, `servo.py` | D-02, D-03, G3 | Q1, Q4 |
| SailSim `autopilot/pypilot.py` | D-09, G2, G3 | Q1-A, Q1-B |
| SailSim `docker/pypilot/apply_patch.py` | D-04, G3 | Q1-C courant/COG/IMU |
| SailSim `core/runner.py`, `tests/integration/test_simulator_physics.py` | G2 | Q0-1 à Q0-5 |
| Géométrie Capri 22 et fiche vérin | D-05, D-06, G1 | M1/M2 ; BOM V0.2 |
| Relevés en navigation manuelle | D-07, D-08, G4 | D1, Q3, Q4 |
| ARCH:D-3, ARCH:F-08, pypilot `basic.py` | D-11, G3, G4 | Q2 §5.5, Q4 P1 et P1-bis ; `Plan_execution_pilote_Capri22_V0-5.md` |

## 11. Historique, limites et sources

### État des preuves au 29 octobre 2026

- **Confirmé par lecture :** présence des fonctions dans les fichiers indiqués, interfaces internes, configurations SailSim, tests existants.
- **Simulé antérieurement :** courbes E0/P1–P4 ; les métriques concernant Fenix simplifié ne décrivent pas le vrai logiciel complet.
- **Non exécuté pour cette mise à jour :** build SailSim, test PyPilot en conteneur, code Fenix sur Mega, injection virtuelle IMU, actionneur réel.
- **Non mesuré :** hydrodynamique du Capri 22, effort en mer, puissance et échauffement du vérin, performances de maintien de cap sur l'eau.

### Références primaires

- Fenix : https://github.com/spascual90/Fenix/tree/b8410e50fa19bbad649b0d765cecf8aec2a25bc4
- PyPilot : https://github.com/pypilot/pypilot ; schémas : https://github.com/pypilot/pypilot_schematics
- SailSim : https://github.com/herostrat/sailsim/tree/ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0
- SailSim PyPilot : https://github.com/herostrat/sailsim/blob/ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0/src/sailsim/autopilot/pypilot.py
- SailSim repli GPS : https://github.com/herostrat/sailsim/blob/ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0/docker/pypilot/apply_patch.py
- Sources utilisateur : `Texte collé(1).txt` (audit architecture), `Plan_execution_pilote_Capri22_V0-3.md`, `Qualification_SailSim_Capri22_V0-1.md`, `Conception_Pilote_Automatique_V0-1.md`.
- Annexe de preuves (V0.3) : `conception/architecture-pilote-proposition-2026-10-28.md` du dépôt, identifiants préfixés `ARCH:` ; correspondance : `Correspondance_architecture-2026-10-28_vers_V0-2.md` ; essais Q0 : « EXP-002 - Qualification Q0 SailSim (run001) » (données brutes : dépôt GitHub, `essais/Q0-20261030-run001/`).
- Fiche candidate Firgelli : https://www.firgelliauto.com/products/deluxe-rod-actuator ; spécifications et prix **à confirmer avant achats**.

**Avertissement :** dossier de conception expérimental, non procédure de navigation ni certification de sûreté maritime. Une documentation de code ou un test unitaire réussi ne remplace pas l'essai mécanique et la reprise manuelle effective.
