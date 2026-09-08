# Compilation brute — Pelagic & pyPilot (déposée le 2026-09-08)

Contenu conservé tel quel, au-delà des seuls liens (voir méthode dans
`sources-techniques.md`). Non analysé ni trié ici.

Contexte donné par Mathieu : Pelagic (https://pelagicautopilot.com/) est un
« produit qui se vend » — il tente de faire une conception équivalente.
pyPilot est présenté comme l'alternative open-source de référence, avec une
architecture jugée similaire (IMU 9 axes + contrôleur Arduino + vérin
linéaire).

---

## Spécifications techniques Pelagic (telles que fournies)

- Capteurs : 9 axes (gyro 3 axes + accéléromètre 3 axes + magnétomètre 3 axes)
- Interface : 3 boutons + 6 LEDs
- Modes : cap compas, GPS, vent apparent, vent vrai

**Installation tiller**
- Socle bronze à 24-7/16" (621 mm) de la barre (barre centrée)
- Broche de barre à 18" (457 mm) de l'axe du gouvernail
- Câble 20 pieds entre boîtier contrôle et boîtier moteur

**Revue d'utilisation (Veloce Sailing)**
- Interface simple, autonome des instruments
- Données vent via NMEA0183 optionnel
- Virement automatique (80-105°, défaut 90°)

## pyPilot — architecture matérielle typique (TinyPilot)

| Composant | Spécifications | Notes |
|-----------|-----------------|-------|
| Ordinateur | Raspberry Pi Zero W | Distribution TinyPilot (Linux minimal) |
| IMU | ICM20948 (9 axes) | Accéléromètre + Gyro + Magnétomètre |
| Contrôleur moteur | Arduino Nano/Uno + BTS7960 ou IBT-2 | Communication UART 38400 bauds |
| Vérin linéaire | 12V, course adaptée au bateau | Hy-Pro (même fabricant que Pelagic, B&G, Garmin) |
| Capteur de barre | Potentiomètre 10 tours ou Hall sensor | Optionnel mais recommandé |
| Télécommandes | 433 MHz étanches | +10, +1, -1, -10, Auto, Mode |

## Open-Boat-Projects — pyPilot DIY

- 3 modules : IMU + PCB principale + clavier/écran
- Composants standards disponibles
- Manuel complet EN/DE sur GitHub

## Sailing Anne-Mon — DIY autopilot

- Vérin électro-hydraulique
- Arduino + H-bridge
- Raspberry Pi + pyPilot + OpenCPN

## Club Feeling 1090 — installation pyPilot (récit)

- Récit d'installation sur voilier Feeling 1090
- Actionneur Hy-Pro (même que Pelagic)
- Disjoncteur 15A resettable

## Nautinect — version ESP32 simplifiée

- ESP32 (~4$) + driver moteur IBT-2 (~7$)
- IMU ICM20948 (Pimoroni)
- Télécommande 433 MHz
- Firmware flashable via navigateur
- Support NMEA2000, SignalK, Bluetooth

**Câblage ESP32 → IBT-2**

| ESP32 | IBT-2 |
|-------|-------|
| 5V | VCC |
| GND | GND |
| 5V | R_EN, L_EN |
| GPIO 32 | R_PWM |
| GPIO 33 | L_PWM |

**Câblage IMU ICM20948**

| ESP32 | ICM20948 |
|-------|----------|
| 3.3V | VCC |
| GND | GND |
| GPIO 21 | SDA |
| GPIO 22 | SCL |

## Autres projets similaires

- **KastB - Boat Autopilot** : Arduino Mega + Raspberry Pi (proxy server), app Android multi-clients, pour voilier 12 m
- **DC9 - Homemade Sailboat Autopilot** : PLC ou Arduino, algorithme PID + feed forward, simulation et tests détaillés
- **OpenPlotter - pyPilot** : intégration OpenPlotter, IMU + GPS + vent optionnels, contrôleur moteur adapté au drive

## Spécifications techniques communes (style Pelagic)

**Capteurs**
- IMU 9 axes : ICM20948, BNO055, ou MinIMU9v5
- Calibration accéléromètre : 6 orientations (haut/bas/gauche/droite/avant/arrière)
- Calibration compas : rotation 240°+ (calibration 2D/3D)
- Nivellement : bateau à plat, immobile

**Modes de navigation**
- Compass : maintien de cap magnétique
- GPS : suivi de route (waypoints)
- Wind : cap au vent apparent
- True Wind : cap au vent vrai (nécessite vitesse bateau)

**Vitesse de déplacement du vérin**
- Recommandé : 6-8 secondes pour ±30° de barre
- Idéal : 10-15°/seconde (performance optimale)
- Minimum : 10 secondes pour ±30° (acceptable)

**Alimentation**
- 12V ou 24V selon système
- Consommation : ~0.07A (Raspberry Pi Zero, 12V)
- Protection : fusible/disjoncteur 15A recommandé

## Acheter vs DIY (résumé tel que fourni)

- **Pelagic** : produit commercial haut de gamme (Berkeley Marine Center)
- **pyPilot** : alternative open-source complète, architecture similaire (IMU 9 axes + contrôleur Arduino + vérin linéaire), documentation jugée excellente, communauté active
- **Nautinect** : version ESP32 low-cost
- **PCNautic** : système pyPilot complet assemblé (référence donnée comme « mentionné dans » — phrase source incomplète/tronquée, à vérifier)

## Éléments à noter

- Le lien pyPilot « documentation complète » (https://pypilot.org/doc/) a été
  donné deux fois dans le message d'origine : une fois comme page du manuel
  en français (dont le PDF précis n'est pas fourni), une fois comme
  documentation générale. Indexé une seule fois dans le registre (source
  n° 40).
- La référence à PCNautic (https://pcnautic.com/) est accompagnée dans le
  texte source d'une parenthèse tronquée « (mentionné dans ) » — contexte
  d'origine manquant, à vérifier au besoin.
