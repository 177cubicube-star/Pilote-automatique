# Fenix — IMU ICM20948, boucle de vérin et carte PCB : lecture de situation

Rédigé le 2026-10-28 à partir d'une lecture du code Fenix (dépôt `spascual90/Fenix`, source n° 1)
et de deux dépôts voisins : `Fenix_ICM_20948_Cal` (n° 209) et `PCB-for-Fenix` (n° 210).
Cette fiche est **la source d'autorité** pour les corrections signalées dans
`fenix-liens-et-notes-2026-09-08.md` ; les notes brutes pointent ici au lieu de répéter le contenu.

**Non exécuté :** rien n'a été compilé, téléversé ni testé. Tout ce qui suit est une lecture de code.
Les lignes de `Autopilot.cpp` au-delà d'environ la 780e dernière n'ont pas été lues.

Légende : **CONFIRMÉ** = lu dans le code ou le dépôt · **INFÉRENCE** = déduit de ce qui a été lu ·
**HYPOTHÈSE** = connaissance générale, non vérifiée dans les sources · **À VÉRIFIER** = question ouverte.

---

## 1. Fichiers lus

| Dépôt | Fichiers | Lecture |
|---|---|---|
| `Fenix` | `Fenix_config.h`, `DevICM20948.h`, `ICM20948AHRS.cpp`, `ActuatorController.cpp/.h`, `ActuatorManager.cpp/.h` | en entier |
| `Fenix` | `Autopilot.h`, `Autopilot.cpp` | partielle (la dernière partie, environ 780 lignes, non lue) |
| `Fenix_ICM_20948_Cal` | outil de calibration Python et son README | lu |
| `PCB-for-Fenix` | notes de version (v1.0, v1.1-beta.1, v1.1-beta.2) | lu ; fichiers Fritzing `.fzz` et PDF de gravure **non ouverts** |
| `Fenix-Virtuino`, GitBook | — | non lus |

## 2. IMU : l'ICM20948 est le seul pris en charge

- **CONFIRMÉ** : `Fenix_config.h` définit `#define ICM20948`, avec `IMU_ORIENTATION 0`.
- **CONFIRMÉ** (historique des versions) : l'ICM20948 apparaît en v3.4-beta1 ; la v4.0-beta1 déclare le MinIMU9v5
  obsolète. Dans le code lu pour le firmware v4.x, l'ICM20948 est le **seul** IMU géré.
- Conséquence sur les notes brutes du 2026-09-08 : la BoM (lignes 4a BNO055, 4b MinIMU9v5) et la liste de
  firmwares (`FenixVxxBNO055_Ext.hex`, `FenixVxxMinIMU9V5.hex`) décrivent une **génération antérieure**.
  La mention « ICM20948 recommandée » des points clés est cohérente avec le code ; la mention
  « BNO055 discontinuée et moins fiable » reste cohérente avec l'abandon de ce capteur.

### Fusion de capteurs

- **CONFIRMÉ** : le cap vient d'un filtre **Mahony** (AHRS, version de S.J. Remington) exécuté dans le firmware
  Arduino, **pas** du DMP interne de la puce. Le cap et la vitesse de rotation sont filtrés ; la vitesse de
  rotation est limitée à ±0,35 rad/s.

### Calibration

- **CONFIRMÉ** : outil externe `Fenix_ICM_20948_Cal` (Python 3.12.4 ; tk, pyserial, numpy, matplotlib, scipy).
  Il produit les matrices `A_B`, `A_Ainv`, `M_B`, `M_Ainv` et le décalage `G_offset`, envoyés au firmware sous forme
  de phrases NMEA et enregistrés en EEPROM.
- Différence avec les notes brutes : la procédure « dessiner des 8, Status 3 » décrit la calibration du BNO055
  (HYPOTHÈSE, connaissance générale : ce capteur s'auto-calibre). Pour l'ICM20948 la calibration passe par cet outil Python.

### Niveau logique 5 V / 3,3 V

- **CONFIRMÉ** : la puce fonctionne en 3,3 V ; des commentaires du code indiquent 5 V ou 3,3 V (logique 3V/5V
  acceptée), hérités des exemples SparkFun.
- **À VÉRIFIER** : la fiche technique SparkFun, avant de câbler l'IMU directement sur le Mega (5 V).

## 3. Interface moteur : PWM + DIR, pas BTS7960

- **CONFIRMÉ** (`Fenix_config.h`, `ActuatorController.cpp`) : `PIN_PWM 6` (`analogWrite`) et `PIN_DIR 7`
  (`digitalWrite`) ; potentiomètre de barre sur `A8` ; mesure de courant `A9` ; buzzer `A12`.
- Driver recommandé dans le projet : **Cytron MD10C** (interface PWM + DIR).
- **Écart avec les notes brutes** : le tableau de câblage BTS7960 (D6 → LPWM, D7 → RPWM, D4/D5 → L_EN/R_EN)
  suppose deux entrées PWM et deux entrées d'activation. Le firmware lu envoie un seul PWM (D6) et un sens (D7).
- **HYPOTHÈSE** (connaissance générale, non vérifiée) : un BTS7960 branché directement ne fonctionnerait pas
  avec ce firmware sans adaptateur logique. À valider avant tout achat de driver.

## 4. Boucle de position du vérin (`controlActuator`)

- **CONFIRMÉ** : deux vitesses (255 puis 85), seuils exprimés en dixièmes de degré, zone morte avec
  hystérésis de redémarrage ×4, rampe propre de ±5 par cycle, machine à états sur changement de sens.
- **INFÉRENCE** : le seuil « 30 » correspond à 3° (le commentaire du code dit « grados »), pas à 30°.
- **CONFIRMÉ** : `ACTUATOR_STOP_TIME 1800` ms (`ActuatorManager.h`). Un changement de sens attend donc au
  moins ~1,8 s (≥ ~2 s avec le reste du cycle).
- Le lissage exponentiel de `setSpeed` (`ALFA_05` / `ALFA_95`) n'est **pas** la « rampe v4.1 » : `controlActuator`
  appelle toujours `setSpeed(..., true)` avec sa propre rampe de ±5.

### Protections

- **CONFIRMÉ** : contrôle des limites par le potentiomètre ; détection de calage par le capteur de courant
  INA260 — **optionnel** : s'il n'est pas détecté, il n'y a pas de protection contre le calage.
- **CONFIRMÉ** : paramètre `maxCurrent` ; le commentaire de l'auteur cite ~1,18 A à vide et ~1,3 A bloqué.
- **À VÉRIFIER** : l'état « bloqué » (`_blocked`) semble verrouillé jusqu'à une réinitialisation ; qui l'efface,
  s'il existe un autre chemin, se trouve peut-être dans la partie non lue d'`Autopilot.cpp`.
- **À VÉRIFIER** : `Fenix_config.h` définit `D_MAX_CURRENT 1020.0` et `PIN_CURRENT A9` (lecture analogique), alors
  que l'INA260 est un capteur I²C. Le lien entre les deux n'est pas établi.

### Deux points ouverts, résolus par la lecture

| Question | Réponse | Niveau |
|---|---|---|
| Désynchronisation du signal DIR | Réelle dans le code, mais probablement sans effet pratique : l'état bloqué est verrouillé et une réinitialisation resynchronise | INFÉRENCE |
| Rôle de `DELAY_DIRCHANGE` | Reliquat : la vraie protection est le temps d'arrêt de 1,8 s | INFÉRENCE |

## 5. Architecture logicielle

- **CONFIRMÉ** : `Autopilot` hérite d'`ActuatorManager` et contient un `BearingMonitor` ; `ActuatorManager`
  regroupe `PID_ext`, `RudderFeedback`, `ActuatorController` et `CurrentFeedback`.
- **CONFIRMÉ** : modèle de référence de Fossen, anticipation de Nomoto (valeurs par défaut pour un bateau de
  12 m), anticipation du vent, PID.
- **CONFIRMÉ** : le côté d'installation (tribord / bâbord) est marqué `TODO: Installation side always STARBOARD`
  dans `ActuatorManager.h`. Le paramètre « Installation Side » des notes brutes n'est donc **pas appliqué** dans le code lu.
  **À VÉRIFIER** dans la partie non lue d'`Autopilot.cpp`.

## 6. Carte PCB (`PCB-for-Fenix`)

- Shield pour Arduino Mega : fichiers Fritzing et PDF de gravure.
- **CONFIRMÉ** (notes de version) : v1.0 câble PWM/DIR sur D11/D12 (erreur) ; v1.1-beta.1 est un correctif non
  testé ; v1.1-beta.2 corrige les libellés.
- Lien avec la partie 3 : D11/D12 de la v1.0 ne correspondent pas à `PIN_PWM 6` / `PIN_DIR 7` du firmware lu.
  **À VÉRIFIER** pour la v1.1-beta.2 en ouvrant le fichier Fritzing.

## 7. Versions Fenix repérées

| Version | Changement relevé |
|---|---|
| v3.4-beta1 | introduction de l'ICM20948 |
| v4.0-beta1 | MinIMU9v5 déclaré obsolète |
| v4.1 | rampe de l'actionneur et limite de 35° |
| v4.2-beta3 | série à 115200, INA260, vent AWA/TWD |

## 8. Points restant à traiter

1. Lire la fin d'`Autopilot.cpp` (effacement de `_blocked`, application du côté d'installation).
2. Fiche SparkFun : tolérance 5 V des broches I²C.
3. Lien entre `PIN_CURRENT A9` et l'INA260.
4. Cinquième dépôt de l'écosystème Fenix : non identifié. Le dépôt Virtuino n'a pas été lu (son nom exact n'est pas confirmé ; l'adresse essayée n'a pas répondu).
5. Ouvrir le `.fzz` et les PDF de la carte.
6. Valider l'hypothèse « BTS7960 incompatible sans adaptateur ».
