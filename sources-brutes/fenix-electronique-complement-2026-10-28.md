# Fenix — complément à la lecture du 2026-10-28 : points ouverts réglés, carte PCB, interfaces

Rédigé le 2026-10-28, après [`fenix-imu-actionneur-lecture-2026-10-28.md`](fenix-imu-actionneur-lecture-2026-10-28.md)
(commit `409848f`), qui **reste la source d'autorité** sur l'IMU, l'interface moteur et la boucle de vérin.
Ce complément ne répète pas cette fiche. Il fait trois choses : régler ses points ouverts quand le code ou la
carte permettaient de trancher (§2), détailler la carte PCB que la fiche n'avait pas ouverte (§3), et ajouter des
constats qu'elle ne couvre pas (§4). Reste à décider s'il demeure un fichier séparé ou s'il est replié dans la
fiche d'autorité (§5).

**État des dépôts au moment de la lecture**

| Dépôt | Dernier commit | Remarque |
|---|---|---|
| `Fenix` (n° 1) | `b8410e5`, 2026-10-23 | identique à celui de la lecture du jour : rien n'a changé depuis |
| `PCB-for-Fenix` (n° 210) | `9f08b43`, 2021-09-12 | « v1.1-Beta.2 » |
| `Pilote-automatique` | `409848f`, 2026-10-28 | contient la fiche d'autorité |

**Non exécuté :** rien n'a été compilé, téléversé ni testé. Tout ce qui suit est une lecture du code, du fichier
Fritzing et de deux pages web. Les conclusions des §2.1 et §2.2 viennent de **recherches textuelles sur tout le
dépôt Fenix**, pas d'une lecture complète d'`Autopilot.cpp`.

Légende (celle de la fiche d'autorité) : **CONFIRMÉ** = lu dans le code, le dépôt ou une page · **INFÉRENCE** =
déduit de ce qui a été lu · **HYPOTHÈSE** = connaissance générale, non vérifiée dans les sources · **À VÉRIFIER** =
question ouverte.

---

## 1. Fichiers lus

| Source | Fichiers | Lecture |
|---|---|---|
| `Fenix` | `Fenix_config.h`, `Fenix.ino`, `GPSport.h`, `BT.h`, `ActuatorController.cpp`, `CurrentFeedback.cpp`, `RudderFeedback.cpp` | en entier |
| `Fenix` | `BT.cpp`, `IF_NMEA.cpp`, `ICM20948AHRS.cpp` | début du fichier seulement |
| `Fenix` | `ActuatorController.h`, `CurrentFeedback.h`, `Autopilot.h`, `Autopilot.cpp`, `ActuatorManager.*` | passages ciblés par recherche (blocage, côté d'installation, réinitialisation) |
| `Fenix` | historique git (suppression de `LCDKeyPad*`) | lu (50 derniers commits) |
| `PCB-for-Fenix` | `Fenix definitivo.fzz` (archive ouverte, réseaux tracés), `Fenix definitivo_etch_silk_top.pdf` (rendu en image), notes de version | lu |
| `PCB-for-Fenix` | `PCB-for-Fenix.zip` (fichiers de fabrication), autres PDF | **non ouverts** |
| SparkFun | guide « 9DoF IMU (ICM-20948) Breakout Hookup Guide », page *Hardware overview* | lue le 2026-10-28 |
| GitBook Fenix | page « Using track mode » (n° 10) | lue le 2026-10-28 |
| `Virtuino-for-Fenix` (n° 13) | — | existence vérifiée seulement, contenu non lu |

## 2. Points ouverts de la fiche d'autorité : réponses

### 2.1 L'état « bloqué » du vérin : qui le lève ? (fiche §4 et §8.1)

- **CONFIRMÉ** : `setBlocked()` n'est appelée qu'à un seul endroit, sans argument, donc toujours avec la valeur
  « vrai » (`ActuatorManager.cpp:233`). Aucune autre ligne du dépôt n'écrit `_blocked = false` (la seule
  affectation est dans `setBlocked`, `ActuatorController.h:58`, plus la valeur initiale ligne 78).
- **CONFIRMÉ** : à la détection, le vérin s'arrête puis fait un court mouvement inverse (`cal_FBK_move` : un tiers
  de vitesse pendant 500 ms, puis 500 ms d'arrêt, avec `delay()`), soit environ 1 s pendant lequel la boucle
  principale est bloquée (`ActuatorController.h:57-63`, `ActuatorController.cpp:47-54`).
- **CONFIRMÉ** : ensuite le pilote passe en STAND_BY (`Autopilot.cpp:246`), une alarme est levée
  (`Autopilot.cpp:199`), `changeRudder` refuse tout (`ActuatorManager.cpp:210`) et `setSpeed` impose une vitesse
  nulle (`ActuatorController.cpp:81`).
- **CONFIRMÉ** : une réinitialisation logicielle existe (`reset()` : message, attente de 2 s, saut à l'adresse 0,
  `Autopilot.h:771-777`). Elle n'est appelée que dans quatre cas : après la calibration externe de l'IMU
  (`Autopilot.cpp:494`), au lancement d'une calibration (`:626`), à son annulation (`:638`) et après un formatage
  de l'EEPROM (`:1438`). Aucun appel ne dépend de l'état « bloqué ».
- **INFÉRENCE** : après un calage, le vérin reste hors service jusqu'à une remise sous tension. **À VÉRIFIER sur
  banc** : si l'une des quatre actions ci-dessus le débloque (non testé, et ce n'est pas une procédure à retenir).

### 2.2 Le côté d'installation est-il appliqué ? (fiche §5 et §8.1)

- **CONFIRMÉ** : non. La valeur est stockée et renvoyée à l'application, mais aucune logique de commande ne la lit.
  `TODO: Installation side always STARBOARD` (`ActuatorManager.h:33`), lecture initiale marquée TODO
  (`Autopilot.cpp:21`), `Change_instParam` contient `//TODO: change installation side` (`:1147`) : un changement
  venu de l'application ou du NMEA est donc ignoré. `getInstallationSide()` n'est lue qu'à `Autopilot.cpp:1115`,
  pour le rapport envoyé à l'application.
- **CONFIRMÉ** (commentaire du code, `Autopilot.h:166-169`) : la convention par défaut est « tourner à tribord
  demande l'**extension** du vérin à partir du centre » (STARBOARD) ; PORTBOARD serait la rétraction.
- **INFÉRENCE** : le montage doit respecter la convention tribord = extension. Choisir « Port » dans l'application
  ne change rien au comportement. **À VÉRIFIER** : ce qu'il faudrait faire pour un montage inverse (aucune
  inversion trouvée dans le code lu).

### 2.3 Logique 5 V / 3,3 V de l'IMU (fiche §2 et §8.2)

- **CONFIRMÉ** (fichier Fritzing) : le connecteur `JP4-I2C IMU` du Shield reçoit **5 V**, deux GND, SDA et SCL
  directement depuis le Mega. Aucun composant n'est placé sur ces lignes : les deux seules résistances de la
  carte, R1 et R2, sont sur la ligne Bluetooth (§3).
- **CONFIRMÉ** (guide SparkFun) : la carte décrite dans ce guide accepte une alimentation de **1,8 à 5,5 V**, a un
  régulateur intégré et une adaptation de niveau (TXS0108) sur ses entrées-sorties (1,8 à 5,5 V). Ses résistances
  de rappel I²C ne sont pas montées parce que le TXS0108 les intègre. Le guide ne donne aucun avertissement pour
  un Arduino 5 V, mais n'écrit pas non plus « SDA/SCL tolérants 5 V ».
- **À VÉRIFIER** : la référence exacte de la carte SparkFun utilisée. Le `README` de Fenix dit seulement « Sparkfun
  IMU ICM20948 », sans numéro de produit. La conclusion ci-dessus vaut pour la carte du guide.
- **HYPOTHÈSE** (mémoire, non vérifiée) : les commentaires « 3V or 5V logic, 10K pullup » de `Fenix_config.h:118-122`
  reprendraient la documentation d'un autre fabricant. Ils ne prouvent rien sur la carte SparkFun.

### 2.4 `PIN_CURRENT A9` et l'INA260 (fiche §4 et §8.3)

- **CONFIRMÉ** : `PIN_CURRENT A9` n'a qu'un seul usage, renvoyer son nom (`CurrentFeedback.h:64`). Aucune lecture
  analogique de A9 dans le dépôt. Le courant est lu par `ina260.readCurrent()` (`CurrentFeedback.cpp:48`), donc
  par l'I²C. La définition de A9 est un reliquat.
- **CONFIRMÉ** : aucun des 16 réseaux étiquetés du Shield ne mène à A9.
- **INFÉRENCE** : l'INA260 devra partager le bus I²C de `JP4` (ou une soudure sur SDA/SCL) : le Shield n'a pas de
  connecteur qui lui soit dédié.

### 2.5 Dépôt Virtuino (fiche §8.4)

- **CONFIRMÉ** : `https://github.com/spascual90/Virtuino-for-Fenix.git` existe (`git ls-remote`, 2026-10-28 :
  branches `master` et `Virtuino-for-Fenix-V01`). C'est le dépôt du n° 13 du registre. Le nom `Fenix-Virtuino`
  n'existe pas (le serveur réclame des identifiants, ce qui signifie « introuvable »). Contenu non lu.

### 2.6 Carte PCB (fiche §6 et §8.5) : voir §3.

### 2.7 L'hypothèse « BTS7960 incompatible sans adaptateur » (fiche §8.6)

- **INFÉRENCE renforcée, hypothèse non validée** : le Shield n'expose vers le driver que `GND`, `DIR`, `PWM`
  (connecteur `JP6`, §3). C'est cohérent avec un driver à interface PWM + DIR, comme le Cytron MD10C cité par le
  `README` de la carte. Cela ne prouve pas qu'un BTS7960 branché directement ne fonctionnerait pas.

## 3. La carte « Fenix Megashield » : contenu du fichier Fritzing

**Version lue.** La sérigraphie porte « Fenix Megashield VERSION 1.1 ». Le `.fzz`, le PDF de sérigraphie, l'archive
de fabrication et le `README` sont tous du même commit `9f08b43` (« v1.1-Beta.2 », 2021-09-12). **CONFIRMÉ** : la
carte lue est la **v1.1-beta.2**. Le `README` signale la beta.1 comme « non testée » ; il ne dit rien sur le test
de la beta.2.

**Méthode.** Réseaux tracés depuis le fichier `.fzz`, en suivant les pistes de la vue « circuit imprimé » sans passer
par les étiquettes de réseau, puis recoupés avec ces étiquettes : les résultats sont identiques. Les broches du Mega
viennent de la pièce `FENIX001` incluse dans l'archive. Le recoupement avec le firmware (dernière colonne) est
exact pour toutes les broches comparables.

| Connecteur | Étiquettes de la sérigraphie | Broches du Mega | Concordance avec le firmware |
|---|---|---|---|
| `JP6-Eng.Control` (3 broches) | GND, DIR, PWM | DIR = **D7**, PWM = **D6** | `PIN_DIR 7`, `PIN_PWM 6` (`Fenix_config.h:116-117`) |
| `J2-Feedback` (3 bornes) | 5V, FBK, GND | FBK = **A8**, 5 V | `PIN_RUDDER A8` (`:105`) |
| `JP1-Buzzer` + buzzer soudé sur la carte | — | **A12** | `PIN_BUZZER A12` (`:112`) |
| `JP3-BT` (6 broches) | K, 5, G, T1, R1, S | KEY = **D34**, 5 V, GND, module T1 → **D19** (RX1), D18 (TX1) → R1 → module R1, STATE = **D44** | Serial1 sur D18/D19 (`GPSport.h:44-45`) |
| `JP4-I2C IMU` (6 broches) | 5, G, SD, SC, G, x | 5 V, GND, SDA, SCL, GND, 6e broche non relevée | I²C 20/21 (`ICM20948AHRS.cpp:31-33`) |
| `JP2-Keypad` (2 broches) | — | **A0** | module supprimé (§4.3) |
| `J1-Power IN` (2 bornes) | Vin, GND | **VIN** du Mega | alimentation (ligne 6 de la BoM des notes brutes) |
| `JP5-S0` (3 broches) | G, S0 (lecture incertaine sur le rendu) | une broche à GND, les autres sur aucun réseau étiqueté | usage non identifié |

- **INFÉRENCE** : l'ordre de la sérigraphie de `JP6` (GND, DIR, PWM) concorde avec les pistes (DIR sur D7, PWM sur
  D6). C'est la correction annoncée par le `README` pour la beta.2. Cela suppose que l'ordre des étiquettes suit
  l'ordre des broches, ce qui se vérifie sur les autres connecteurs de la carte (par exemple `JP4`).
- **CONFIRMÉ** : dans cette version, PWM et DIR sont sur **D6 et D7**, pas sur D11/D12 comme en v1.0. Cela règle
  le point que la fiche laissait « à vérifier pour la v1.1-beta.2 ».
- **INFÉRENCE** : la puissance du moteur ne passe pas par le Shield. `JP6` n'a que GND/DIR/PWM, et `J1` n'alimente
  que la broche VIN du Mega.
- **CONFIRMÉ** (topologie) : le Bluetooth est protégé par un **diviseur de tension**. D18 passe par R1 (1 kΩ), puis
  le nœud rejoint l'entrée du module et R2 (2,2 kΩ) vers GND. Calcul : 5 V × 2,2 / (1 + 2,2) ≈ 3,4 V. D19 reçoit la
  sortie du module directement.
- **À VÉRIFIER** : le PDF de sérigraphie est un rendu ; le texte de `JP5` y est difficilement lisible, et la
  concordance entre le `.fzz` et les fichiers de fabrication du `.zip` n'est qu'une inférence (même commit, même
  heure d'export).

## 4. Constats nouveaux, non couverts par la fiche d'autorité

### 4.1 Vitesses des ports série

- **CONFIRMÉ** : `Fenix.ino:74` ouvre le port NMEA/USB à **115200** bauds, après que `IF_NMEA::setup()` l'a ouvert
  à 9600 (`Fenix.ino:70`, `IF_NMEA.cpp:23,32`). Le Bluetooth est à **9600** (`BT.cpp:21`). L'historique indique
  « Serial port speed increased to 115200 » (`Fenix_config.h:68`).
- **CONFIRMÉ** : l'exigence AP-20 de `RELEASE.md` parle de NMEA 0183 à **4800** bauds. C'est une exigence, pas
  l'état du code.
- **INFÉRENCE** : la vitesse effective du port USB est 115200 (dernier `begin`). Une source externe (ordinateur,
  Raspberry Pi) doit être réglée à cette vitesse. **À VÉRIFIER sur banc.**

### 4.2 Bluetooth et application

- **CONFIRMÉ** : `KEY` (D34) et `STATE` (D44) sont câblées sur le Shield, mais le firmware n'a aucun `pinMode`,
  `digitalRead` ni `digitalWrite` sur ces broches. Les seules broches numériques pilotées sont PWM, DIR, le buzzer
  et le bus I²C.
- **INFÉRENCE** : le firmware ne peut ni mettre le module en mode de configuration ni lire son état de connexion.
  **HYPOTHÈSE** (connaissance générale) : le nom, le code PIN et la vitesse du module se règlent à part, par
  commandes AT.
- **CONFIRMÉ** : le lien Bluetooth parle le protocole **Virtuino**, pas du NMEA (`BT.cpp:32`). L'application échange
  50 valeurs (`BT.h:98-161`) et 26 boutons (`BT.h:61-93`).

### 4.3 Le clavier LCD (`JP2-Keypad`, A0) n'existe plus dans le firmware

- **CONFIRMÉ** : `LCDKeyPad.*` et `LCDKeyPadArq.*` ont été supprimés au commit `a8faf84` (2026-04-29, « Add current
  monitoring and actuator blockage. Serial port speed increased » ; le message ne mentionne pas la suppression).
  Avant cela, `LCDKeyPad.cpp` était déjà entièrement en commentaires (seul l'en-tête ne l'était pas).
- **CONFIRMÉ** : `LCDKeyPadArq::getButtonPressed` lisait `analogRead(0)` avec des seuils de type « LCD Keypad
  Shield » (moins de 100 pour droite, moins de 200 pour haut, moins de 400 pour bas…), pour cinq touches (haut, bas,
  gauche, droite, sélection). `Fenix.ino:10` garde `//#define HMI_LCDKEYPAD` désactivé.
- **INFÉRENCE** : le connecteur `JP2-Keypad` du Shield n'a aucun usage avec le firmware v4.2. L'ancien code est
  récupérable : `git show a8faf84^:LCDKeyPadArq.cpp`. L'interface active est le Bluetooth (`GPSport.h:43`).

### 4.4 Le portage « UNO R4 WiFi » est inachevé

- **CONFIRMÉ** (lecture) : dans la branche R4 de `Fenix_config.h:124-141`, `PIN_RUDDER` est défini deux fois (A0
  puis A1) et `PIN_BUZZER` vaut A1, donc le buzzer et le potentiomètre se retrouvent sur la même broche. Aucun
  `PIN_CURRENT` n'y est défini alors que `CurrentFeedback.h:64` en a besoin. La branche R4 de `GPSport.h:57-73` ne
  définit ni `HMI_BT` ni `BTPort` : pas d'interface Bluetooth (`Fenix.ino:13`).
- **INFÉRENCE** : cette branche ne compile probablement pas telle quelle, et n'aurait pas de Bluetooth si elle
  compilait. Non testé. Le Mega est la seule cible cohérente du code actuel.

### 4.5 NMEA, mode TRACK et rôle du Raspberry Pi

- **CONFIRMÉ** : l'entrée NMEA est le port USB (`GPSport.h:34`, `gpsPort` = `NeoSerial`). La réception d'une phrase
  APB déclenche la demande de mode TRACK (`IF_NMEA.cpp:214`), et le mode existe dans `Autopilot.h:28`.
- **CONFIRMÉ** (page GitBook, source n° 10) : la route se construit dans l'application de navigation, qui envoie
  des phrases APB (OpenCPN, AVNav ou toute source qui en émet). L'utilisateur confirme, avec le bouton « Next
  Course » de Virtuino (`BT_NEXT_COURSE`, `BT.h:87`), l'entrée en TRACK puis chaque changement de point. La page ne
  décrit ni la liaison physique ni la perte des données.
- **CONFIRMÉ** : le dossier `Serial IF/RPI` du dépôt Fenix ne contient que `Installation.txt`, l'installation de
  PuTTY (terminal série) sur un Raspberry Pi. Le Pi n'est pas le calculateur du pilote : au mieux une source de
  navigation et un terminal série.
- **CONFIRMÉ** : `MAX_APB_TIME 10000` ms (`Fenix_config.h:152`). **À VÉRIFIER** : ce qui se passe à l'expiration
  (non lu).
- **À noter** : la spécification d'interface NMEA du dépôt est une capture de wiki de 2020 qui décrit OpenPlotter
  comme requis pour le mode Nav. La page GitBook, plus récente, accepte d'autres sources.

## 5. Suites proposées (rien n'est appliqué)

1. Mettre à jour la fiche d'autorité avec les réponses des §2 et §3 (ses points §8.1 à §8.5), **ou** garder ce
   complément séparé. **À décider.**
2. Registre `sources-techniques.md` : le n° 210 passerait de « notes de version seulement » à « notes de version,
   fichier Fritzing, sérigraphie » ; le n° 10 (page TRACK) et le n° 13 (Virtuino) ont été touchés de façon partielle
   le 2026-10-28.
3. Les notes brutes du 2026-09-08 n'ont pas besoin d'annotation supplémentaire pour ce complément.

## 6. Points restant à traiter

1. Lire `Autopilot.cpp` en entier : les §2.1 et §2.2 reposent sur des recherches textuelles.
2. Identifier la référence exacte de la carte IMU SparkFun.
3. Valider sur banc : le comportement après un calage, la vitesse effective du port USB, l'effet de la perte d'APB
   après 10 s.
4. Ouvrir `PCB-for-Fenix.zip` et vérifier qu'il correspond au `.fzz`.
5. Identifier l'usage de `JP5-S0` et de la 6e broche de `JP4`.
6. Lire le dépôt `Virtuino-for-Fenix` (n° 13).
7. Valider l'hypothèse « BTS7960 incompatible sans adaptateur ».
