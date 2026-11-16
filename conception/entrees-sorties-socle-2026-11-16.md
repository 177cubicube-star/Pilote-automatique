
# Entrées-sorties du socle

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `03 - Analyses/Entrées-sorties du socle.md` (type `analyse`, statut `en-cours`). Analyse en cours, rien n'est câblé ni mesuré. Les noms entre « » désignent des notes du vault.

Cette note dresse la liste des **entrées et sorties électriques** qu'exige le socle défini dans « grille-capacites-pilote » (section 16, état du 2026-11-16). C'est le « prochain pas » de « Q-008 - Calculateur et architecture de commande » : connaître les besoins réels avant de comparer les plateformes.

La liste est d'abord **indépendante de la plateforme** (sections 1 à 6). La section 7 montre comment elle se répartirait si « CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé » était retenue ; ce n'est pas un choix.

**Statut.** Analyse de conception, rien n'est câblé ni mesuré. Les types d'interface des composants cités sont des exemples courants, à vérifier sur les fiches techniques des modèles retenus.

## Vocabulaire

| Terme | Signification |
|---|---|
| Entrée analogique (CAN-A) | Lit une tension variable (potentiomètre, sonde, capteur de courant). Ici « CAN-A » pour éviter la confusion avec le bus CAN. |
| Entrée / sortie numérique (GPIO) | Lit ou impose un état tout-ou-rien (bouton, voyant). |
| PWM | Sortie qui module la vitesse du moteur par impulsions. |
| I2C, SPI | Liaisons courtes entre composants d'une même carte (capteurs, écran). Distance pratique : courte, de l'ordre de la carte ou du boîtier. |
| UART (série) | Liaison point à point (GPS, NMEA 0183, liaisons entre cartes). |
| Bus CAN | Réseau robuste à deux fils, base du NMEA 2000. |

## 1. Capteurs

| Élément du socle | Interface probable | Nombre | Capacités servies | Remarques |
|---|---|---|---|---|
| IMU 9 axes | I2C ou SPI (ex. ICM-20948, BNO085) | 1 | Cap compas, alarme d'écart de cap, manœuvres, journal | Placer loin des aimants du moteur et des masses de fer (à vérifier en essai) |
| GPS | UART (phrases NMEA en niveau logique), sortie PPS en option | 1 | Homme à la mer, alarmes de zone et de haut-fond, horodatage du journal | L'heure GPS peut horodater le journal |
| Retour de position de la barre (potentiomètre du vérin) | Entrée analogique | 1 | Barre bloquée à un angle, affichage de l'angle, séquences en angle mesuré | Mesure la tige ; l'angle de barre exige une calibration de la géométrie |
| Accéléromètre séparé (au nez **ou en tête de mât**, précisé par Mathieu le 2026-11-16 ; idée de « CON-006 - Anticipation de la barre par capteurs inertiels ») | LIS3DH, I2C sur l'ESP32 du nœud (« DEC-012 - Accéléromètre séparé - LIS3DH ») | 1 | Seconde source, anticipation | Placé à l'avant : trop loin pour de l'I2C. Voir section 6 |
| Capteur de position de la bôme | **À définir** : capteur d'angle magnétique (I2C ou analogique) ou potentiomètre | 1 | Séquences d'empannage (option) | Placé au vit-de-mulet : distance à couvrir |
| Cellule de charge sur l'écoute de grand-voile | Jauge de contrainte + amplificateur (ex. HX711 : 2 fils numériques) | 1 | Séquences (option), anticipation possible | Amplificateur près de la cellule, le signal brut est très faible |

## 2. Moteur et puissance

| Élément du socle | Interface | Nombre | Capacités servies | Remarques |
|---|---|---|---|---|
| Commande du moteur vers le pont en H | PWM + direction (ou 2 PWM selon le pont) | 2 à 3 sorties | Tous les modes et manœuvres | — |
| Courant du moteur | Entrée analogique (résistance de mesure + amplificateur) | 1 | Mesure de courant, protections, blocage | Leçon de la carte Q218 : son pont n'en avait pas |
| Tension de la batterie | Entrée analogique (diviseur) | 1 | Mesure de tension, sous-tension | — |
| Température du moteur | Entrée analogique (sonde NTC) | 1 | Température du moteur, protection thermique | — |
| Température du contrôleur | Entrée analogique (sonde NTC) | 1 | Protection thermique | **Retenue par Mathieu le 2026-11-16** (proposition de Claude) : la table des défauts vise aussi la surchauffe de l'électronique |
| Fins de course | 2 entrées numériques | 2 | Protections | Proposées comme garde-fou pour la future adaptation au ST ; utiles même si le vérin a les siennes |
| Coupure matérielle de la puissance du moteur | Sortie numérique vers relais ou validation du pont, **plus** interrupteur physique en série | 1 | Veille physique, table des défauts | Registre de conception D-10 : arrêt matériel avant toute liaison sans fil. La veille doit couper même si le logiciel est planté |

## 3. Interface au poste de barre

| Élément du socle | Interface | Nombre | Capacités servies | Remarques |
|---|---|---|---|---|
| Boutons physiques | Entrées numériques (ou matrice) | 6 (Auto, Veille, −1, +1, −10, +10) | Commande, combinaisons pour virement et empannage | Combinaisons gérées par le logiciel |
| Veille physique | Entrée numérique **et** coupure matérielle (section 2) | 1 | Veille indépendante de l'écran | Distincte du bouton Veille logiciel, ou le même bouton câblé aux deux |
| Écran tactile | SPI (ou parallèle) + tactile en I2C ou SPI | 1 | Affichage, édition rapide, confirmation d'empannage | Lisibilité au soleil et usage mouillé à vérifier |
| Affichage simple | Quelques sorties numériques (voyants) ou I2C | 1 | État lisible sans l'écran | Sert de secours si l'écran tactile tombe |
| Avertisseur | Sortie numérique (via transistor) | 1 | Sortie d'alarme au poste de barre | Indépendant de la tablette (« DEC-004 - Prévoir l'évitement de zones et l'interface OpenCPN », disposition 5) |
| Voyant d'alarme | Sortie numérique | 1 | Idem | — |

## 4. Communications

| Élément du socle | Interface | Nombre | Capacités servies | Remarques |
|---|---|---|---|---|
| NMEA 2000 | Bus CAN + émetteur-récepteur (isolé de préférence) | 1 | Connectivité, futurs instruments | Réseau à prévoir : câble principal, deux terminaisons, alimentation 12 V protégée |
| Entrée NMEA 0183 | UART en réception, entrée isolée (optocoupleur) | 1 | Girouette (extension), autres instruments 0183 | — |
| Sortie NMEA 0183 | UART en émission | 1 | Sorties cap, barre, alarme vers un traceur | **Retenue par Mathieu le 2026-11-16** (disposition 4 de DEC-004) |
| Mobile, tablette, PC | Wi-Fi (pages web, Signal K, OpenCPN) | — | Réglages, édition des séquences, cartographie, source de route | Ne commande pas la barre directement |
| Liaisons internes entre cartes | UART (ou Wi-Fi) | selon l'architecture | — | Voir section 7 |

## 5. Mémoire et temps

| Besoin | Moyen probable | Capacités servies |
|---|---|---|
| Journal | Carte microSD ou stockage du calculateur | Journal, réglage, identification des coefficients (« CON-009 - Script d'anticipation de la barre par le vent (spécification) ») |
| Séquences préréglées (3 par manœuvre) et réglages | Mémoire non volatile | Séquences programmables |
| Horodatage | Heure GPS, ou horloge sauvegardée | Journal |

## 6. Capteurs éloignés : un point à trancher

Trois capteurs du socle sont **loin du calculateur** : l'accéléromètre au nez, le capteur de bôme et la cellule de charge. Les liaisons courtes (I2C, SPI) ne portent pas jusque-là de façon fiable.

| Option | Principe | Pour | Contre |
|---|---|---|---|
| **A — Nœuds sur le NMEA 2000** | Un petit microcontrôleur près de chaque capteur, branché sur le réseau NMEA 2000 déjà prévu au socle | Un seul câble réseau, robuste ; ajout de capteurs sans recâbler le calculateur | Un microcontrôleur et un émetteur-récepteur de plus par nœud ; les données de bôme et d'écoute n'ont peut-être pas de message NMEA 2000 standard (format propriétaire à prévoir) |
| **B — Signal analogique ou liaison série longue** | Câble direct vers le calculateur, avec une liaison adaptée aux longues distances (par exemple RS-485) | Pas de nœud intelligent | Un câble par capteur, sensible aux parasites sur de longues distances |
| **C — Sans fil** | Petit nœud sur batterie qui transmet par radio | Pas de câble à tirer | Piles, fiabilité radio, latence : à éviter pour une donnée utilisée en régulation |

**Recommandation de Claude :** l'option A, parce que le réseau NMEA 2000 est déjà au socle.

**Choix révisé de Mathieu (2026-11-16) : option A, nœuds sur le NMEA 2000**, conformément à la recommandation. Le choix initial du même jour (option C, sans fil) est remplacé ; ses conditions sont conservées ci-dessous pour mémoire.

~~Choix initial : option C, sans fil.~~ Conditions proposées pour la rendre sûre, à valider :
- Ces trois capteurs restent **optionnels** : le pilote, les séquences et l'anticipation fonctionnent sans eux (règle déjà fixée par Mathieu pour les séquences).
- Chaque message est **horodaté**, avec un âge maximal : au-delà, la donnée est ignorée et le motif est journalisé.
- Alimentation des nœuds : par le 12 V du bord quand un câble d'alimentation est possible, sinon par batterie, avec alarme de batterie faible.
- Protocole radio à étudier : par exemple ESP-NOW entre ESP32, qui ne demande pas de routeur Wi-Fi *(hypothèse, latence et portée à mesurer)*.
- Pour l'accéléromètre au nez, la **latence** radio doit rester petite devant l'avance attendue (quelques secondes selon CON-006, à mesurer).

## 7. Répartition dans CON-008 (si cette architecture est retenue)

| Bloc | Entrées-sorties qu'il porterait | Remarques |
|---|---|---|
| **Contrôle moteur** (`motor.ino`, ATmega328P) | Commande PWM, courant, tension, température du moteur **et** du contrôleur, position de la barre, 2 fins de course, sortie « embrayage » (utilisable comme validation de puissance, à vérifier) | Le micrologiciel prévoit déjà toutes ces entrées : la correspondance est presque exacte |
| **Cerveau** (pypilot sur Raspberry Pi) | IMU (I2C), GPS (UART ou USB), journal et réglages (stockage), Wi-Fi (Signal K, pages web, OpenCPN), liaison série avec le contrôle moteur | — |
| **Façade** (ESP32) | Écran tactile, affichage simple, 6 boutons, entrée de veille, avertisseur, voyant, bus CAN pour le NMEA 2000, entrée NMEA 0183, liaison avec le cerveau | L'ESP32 a un contrôleur CAN intégré, mais pas d'émetteur-récepteur : il en faut un externe |
| **Nœuds déportés sur le NMEA 2000** (option A, choix révisé de Mathieu) | Accéléromètre au nez, bôme, cellule de charge | Un ESP32 et un émetteur-récepteur CAN par nœud, alimentés par le réseau ; format des messages de bôme et d'écoute à définir (propriétaire) |
| **Hors carte** | Interrupteur de veille en série sur la puissance du moteur | Doit couper même si tous les processeurs sont plantés |

## 8. Bilan provisoire

| Type d'entrée-sortie | Nombre estimé (socle) |
|---|---|
| Entrées analogiques | 5 (position, courant, tension, 2 températures) |
| Entrées numériques | 9 (6 boutons, veille, 2 fins de course) |
| Sorties numériques et PWM | 6 à 7 (commande moteur, coupure, avertisseur, voyant, voyants d'état) |
| Liaisons I2C ou SPI | 2 à 3 (IMU, écran, tactile) |
| Liaisons série (UART) | 2 à 4 (GPS, NMEA 0183, liaisons internes) |
| Bus CAN | 1 (NMEA 2000) |
| Sans fil | Wi-Fi |

Aucune plateforme ne porte tout cela seule de façon confortable. Une architecture en blocs (CON-008 ou une autre) se justifie aussi par cette liste. *Ceci est une interprétation.*

## 9. À décider ou à vérifier

1. ~~Sortie NMEA 0183 vers un traceur~~ : retenue (2026-11-16).
2. ~~Raccordement des capteurs éloignés~~ : nœuds sur le NMEA 2000 (option A, choix révisé le 2026-11-16) ; format des messages des nœuds à définir.
3. Type du capteur de bôme : **à étudier et décider** (Mathieu, 2026-11-16). Emplacement de l'amplificateur de la cellule de charge.
4. ~~Température du contrôleur~~ : ajoutée au socle (2026-11-16).
5. Utilisation de la sortie « embrayage » de `motor.ino` comme validation de puissance : à vérifier dans le code.
6. Longueurs de câble réelles sur le Capri 22 (calculateur, poste de barre, nez, bôme), à relever avec « EXP-003 - Relevé géométrie et appendices Capri 22 (à terre) ».
7. Chiffrage de cette liste face à l'enveloppe de « Q-007 - Usage prioritaire, budget et moyens » : première passe faite le 2026-11-16, [tableur de chiffrage](https://claude.ai/artifact/PRByJFAWh6djKXgfmC81MP).
8. **Format des messages NMEA 2000 des nœuds de bôme et d'écoute** : il n'existe *probablement* pas de message standard pour ces données (non vérifié). Un format propre au projet serait alors à définir. **Reporté à l'étape de conception des nœuds** (Mathieu, 2026-11-16). À vérifier d'abord : la liste des messages standard, au cas où l'un conviendrait.
