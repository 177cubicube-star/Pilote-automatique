# Compilation brute — liens et notes Fenix Autopilot (déposée le 2026-09-08)

Ce document conserve **tel quel** le contenu déposé par Mathieu dans la
conversation, au-delà des seuls liens : listes de composants, câblage,
procédures de calibration, points clés. Conformément à la méthode du projet
(voir `sources-techniques.md`), ce contenu n'est **pas analysé ni trié** ici
— il est simplement mis en réserve pour l'étape d'analyse à venir, qui
alimentera le vault Obsidian.

Chaque lien individuel de cette compilation est aussi indexé comme source
séparée dans `sources-techniques.md` (n° 4 et suivants). Ce fichier-ci sert
de contexte détaillé pour ces sources quand le lien seul ne suffit pas à
retrouver l'information (specs de composants, câblage, formules, procédures).

---

## Liste des composants (Bill of Materials) — telle que fournie

| # | Composant | Spécifications | Notes |
|---|-----------|-----------------|-------|
| 1 | Arduino Mega R3 | ATmega2560, 256KB Flash | Câble USB A/B requis |
| 2 | Driver moteur DC | BTS7960 ou Cytron 10A Shield | Supporte 7-30V, 10A continu |
| 3 | Vérin linéaire 12V | Course 300mm, avec potentiomètre | 5 fils (2 moteur + 3 pot), min 300N |
| 4a | IMU BNO055 | CJMCU-055 (Aliexpress) | Oscillateur cristal à souder |
| 4b | IMU MinIMU9v5 | Pololu (LSM6DS33 + LIS3MDL) | Alternative, calibration plus simple |
| 5 | Module Bluetooth | HC-05 (pas HC-06!) | PIN: 1234 |
| 6 | Convertisseur DC-DC | M2596, sortie 8.5-12V (recommandé: 9V) | Pour alimenter l'Arduino |
| 7 | Fenix Shield PCB | PCB personnalisé | Voir repo GitHub pour fichiers |


> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — les lignes 4a (BNO055) et 4b (MinIMU9v5) correspondent à une génération antérieure : le firmware v4.x lu ne gère que l'ICM20948 (SparkFun). La ligne 2 (BTS7960) est à confronter à l'interface PWM + DIR du firmware (le driver recommandé dans le code est un Cytron MD10C). Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).

## Firmware (releases GitHub)

- `FenixVxxBNO055_Ext.hex` : pour IMU BNO055 (algorithme externe, recommandé)
- `FenixVxxMinIMU9V5.hex` : pour IMU Pololu MinIMU9v5
- `SIMULATOR.hex` : mode simulation (test sans bateau)


> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — les noms `…BNO055_Ext.hex` et `…MinIMU9V5.hex` relèvent d'une génération antérieure ; pour la v4.x, l'IMU géré est l'ICM20948. Nom du fichier `.hex` correspondant non relevé. Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).

## Application Android (Virtuino)

- Installer Virtuino Viewer V6 depuis Google Play Store
- Charger le fichier `Fenix.vrt` dans l'app
- Appairer HC-05 (PIN: 1234)

## Vérin linéaire avec potentiomètre (feedback)

- Calibration min/max (ex : 44–951 sur ADC 10-bit)
- Filtrage du signal (moyenne mobile 5-10 échantillons)
- Formule de position : `Position = (Current ADC - Min ADC) / (Max ADC - Min ADC) × Stroke Length`

## Driver moteur BTS7960 — câblage typique

| Arduino | BTS7960 |
|---------|---------|
| D6 PWM | LPWM |
| D7 PWM | RPWM |
| D4/D5 | L_EN, R_EN |
| 5V | VCC (logique) |
| GND | GND |
| 12V externe | VMS (moteur) |


> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — ce câblage suppose deux entrées PWM et deux entrées d'activation. Le firmware lu envoie un PWM sur D6 et un sens sur D7 (interface PWM + DIR). Branchement direct d'un BTS7960 : incompatibilité probable (hypothèse, non vérifiée). Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).

## Calibration et essais

**Calibration IMU (compas)**
- Procédure : dessiner des « 8 » avec le bateau/IMU
- Status 3 = capteur entièrement calibré
- Sauvegarder les offsets dans l'EEPROM


> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — cette procédure (« 8 », Status 3) décrit le BNO055. Pour l'ICM20948, la calibration passe par l'outil externe `Fenix_ICM_20948_Cal` (source n° 209) ; les matrices sont enregistrées en EEPROM. Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).

**Calibration vérin linéaire**
- Étendre complètement → noter valeur ADC max
- Rétracter complètement → noter valeur ADC min
- Définir position centrale (barre au centre)
- Régler l'angle maximum de barre (ex: 40°)

**Paramètres d'installation**
- Centered Tiller Position : position ADC de la barre centrée
- Maximum rudder angle : angle max de barre (ex: 40°)
- Installation Side : Starboard (S) ou Portboard (P)


> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — dans le code lu, le côté d'installation est marqué `TODO: Installation side always STARBOARD` (`ActuatorManager.h`). Application réelle du paramètre à vérifier. Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).
- Rudder Damping : amortissement (ex: 3)
- Magnetic Variation : déclinaison magnétique locale
- Heading Alignment : alignement avec compas externe
- Off course alarm angle : alarme d'écart de cap

**PID et autotune**
- Mode Autotune : propose des valeurs PID basées sur les performances du bateau
- Deadband : 1–5° (min, max, auto)
- Ajuster les gains via l'app ou interface série (`$PEMC,06,...`)

## Premiers essais en mer — modes de navigation

- STAND BY : attente, calibration possible
- AUTO : maintien de cap (±1° ou ±10°)
- TRACK : suivi de route GPS (waypoints)
- WIND : mode vent (à partir de v2.6.B2)

**Procédure de mise en route**
1. Stabiliser le bateau sur le cap désiré
2. Engager la tige du vérin sur la broche de barre
3. Passer de STAND BY → AUTO
4. Utiliser l'app pour ajuster le cap (±1°, ±10°, virement)
5. Pour revenir en manuel : désengager la tige

## Interface série (débogage) — repère dans le repo

- Documentation interface série : dossier « Serial IF » dans le repo GitHub Fenix (sous-dossier de la source n° 1, pas une source distincte)
- Codes `$PEMC` : configuration et calibration via commandes texte
- Calculateur de checksum : inclus dans le repo

## Points clés à retenir (tels que formulés par Mathieu / sa source)

- IMU recommandée : MinIMU9v5 (Pololu) ou ICM20948 (Sparkfun) — BNO055 est présentée comme discontinuée et moins fiable
- Vérin avec pot : jugé obligatoire pour le feedback de position (5 fils, pas 2)
- Alimentation : 12V batterie → DC-DC 9V → Arduino (éviter reset USB)
- Bluetooth : HC-05 uniquement (HC-06 ne fonctionnerait pas en maître)
- Calibration : IMU ET vérin avant première utilisation
- Filtrage : moyenne mobile 5-10 échantillons pour le pot (réduit le bruit moteur)

## Éléments mentionnés sans lien exploitable

Ces éléments ont été cités dans le dépôt d'origine mais sans URL directe et
fiable à indexer ; à retrouver au besoin depuis leurs sources parentes.

- **PCB Fenix (fichiers de production)** — mentionné comme « GitHub - PCB-for-Fenix », dépôt distinct probable du même auteur (`spascual90`), URL non fournie

> **Annotation du 2026-10-28** (texte d'origine ci-dessus inchangé) — dépôt retrouvé : https://github.com/spascual90/PCB-for-Fenix, indexé sous le n° 210 du registre. Voir [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md).
- **Vidéos de démonstration** — section « Videos » du site officiel https://fenix-autopilot.com/, page précise non fournie
