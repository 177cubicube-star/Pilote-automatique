# Validation et analyse technique des dépôts open source de pilotes automatiques

Rédigé du 2026-11-01 au 2026-11-02. **Statut : RAPPORT DE SESSION — lecture de code, rien n'est validé.**
Il valide une liste de dépôts GitHub proposée par Mathieu et développe le fonctionnement de ceux qui existent. Cible de référence : pilote de barre franche, voilier ≤ 8 m, vérin linéaire (Catalina Capri 22).

**Non exécuté :** rien n'a été compilé, téléversé ni testé ; les dépôts ont été **lus** (pages GitHub, fichiers sources, manuels), jamais lancés.

**Rangement :** dans `sources-brutes/`, comme les autres rapports de session. Le vault Obsidian reste la référence de travail (voir le README du dépôt) ; sa version de ce rapport est `03 - Analyses/Dépôts open source de pilotes - validation et analyse technique.md`. Autorité sur l'anticipation du vent de Fenix et l'issue n° 13 : la note du vault « Fenix - anticipation du vent (wind feedforward) » et `sources-brutes/fenix-wind-feedforward-explication-2026-10-26.md`. Compléments : `conception/` (concepts et décisions du 2026-11-02) et `essais/zones-opencpn-20261102/`.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

Cette fiche valide une liste de dépôts GitHub proposée dans la conversation, puis développe le fonctionnement technique de ceux qui existent réellement. Cible de référence du projet : pilote de barre franche, voilier ≤ 8 m, vérin linéaire générique.


## Mises à jour postérieures à la rédaction (2026-11-02)

Ces points corrigent ou complètent le texte ci-dessous, qui n'a pas été modifié :

1. **Commentaire sur l'issue #13 de Fenix** : le texte dit « statut de publication inconnu » (3.2.2 « Suite donnée », section 6 point 3). Il a depuis été **publié** (2026-11-01, d'après la note la note du vault « Fenix - anticipation du vent (wind feedforward) »). L'intention de l'auteur reste à obtenir.
2. **Part cible de 80 %** : le texte la dit « non vérifiée » (3.2.2). La note du vault indique `targetFeedforwardShare() = 0.80f` : l'**interprétation « 0,8 = part cible de feedforward » est donc confirmée**. La correction proposée (0,8 ; 1,2) reste un choix indicatif.
3. **« Ratio 0,50 à l'initialisation »** (3.2.1) est **inexact** : 0,50 est la constante `kAir` du modèle de vent ; le **ratio `windFFratio` démarre à 1,0** (borné entre 0,5 et 2,0), comme le dit déjà 3.2.2.
4. **Reste non vérifié** : le feedforward vent agit-il en mode compas, ou seulement dans les modes vent ? La note du vault le suggère (modes vent seulement) ; non confirmé dans le code lu ici.

## 1. Méthode et limites

- Lecture directe des pages GitHub, des fichiers sources accessibles (pypilot : autopilot.py, pilots/basic.py, pilots/pilot.py, pilots/simple.py, pilots/learning.py, boatimu.py ; Fenix : Autopilot.cpp [lignes 1 à 1000], Autopilot.h, ActuatorManager.cpp et .h, ActuatorController.cpp, RudderFeedback.cpp, BearingMonitor.cpp et .h, ICM20948AHRS.cpp, DevICM20948.cpp, PID_v1_ext.cpp [dans `libraries_ext/`], FossenReferenceModel.cpp, ReferenceFeedforward.cpp, WavePassiveObserver.cpp, WindFeedforward.h, IF_NMEA.cpp, emcNMEA.cpp [environ 1 000 des 1 639 lignes], WindFeedforwardEvaluatorSimple.cpp ; Nautinect : autopilot-main.ino, Bluetooth.cpp, Bluetooth.h, Motor.cpp, Motor.h ; Milo.ino ; SimplePilot : README, pilot.ino, heading.ino), de RELEASE.md et de l'issue #13 (Fenix), du manuel pypilot et de recherches web.
- **Informations de seconde main** : la ligne 1775 d'`Autopilot.cpp`, les définitions de `setWindFFratio`/`getWindFFratio` (`WindFeedforward.h`) et l'emplacement de `PID_ext` proviennent d'un compte rendu collé par Mathieu, issu d'une session Claude Code locale qui avait téléchargé les fichiers. Le compte rendu est coupé à quelques endroits ; seules les parties lisibles sont utilisées. La lecture directe de `WindFeedforward.h` et de `PID_v1_ext.cpp` (2026-11-01) concorde avec lui : `setWindFFratio` borne bien le ratio entre 0,5 et 2,0, et `PID_ext` est bien défini dans `libraries_ext/`. La formule de `Cwind` a été lue directement (voir 3.2.2).
- **Les numéros de ligne cités pour `PID_v1_ext.cpp` sont déduits du texte de la page** (numérotation non fiable) : à vérifier dans un éditeur avant de les citer.
- **Non obtenu** : les dates de dernier commit (GitHub bloque la page des commits aux outils automatiques) ; la classe d'identification de Nomoto de Fenix (`nomotoId`, non déclarée dans `ActuatorManager.h`) ; `WindFeedforward.cpp` (table des coefficients Cn) ; la fin d'`Autopilot.cpp` (lignes 1000 à 1780, hors extrait de seconde main) ; la fin d'`emcNMEA.cpp` ; le fichier de configuration du modèle appris du pilote `learning` de pypilot ; le dossier `build/` de Nautinect (non inspecté) ; la définition de `constrain` dans le cœur Arduino ; les conditions de déclenchement de `updateWindFeedforwardEvaluation`. Aucun test n'a été exécuté.
- Un lien « introuvable » signifie : la page ne répond pas ET aucune recherche ne retrouve le dépôt. Ce n'est pas une preuve d'inexistence absolue.

## 2. Verdict de validation

| Élément de la liste initiale | Verdict | Remarque |
|---|---|---|
| pypilot/pypilot | **Vérifié** | Python, GPL v3 (manuel), 280 étoiles, 121 forks, 2 742 commits. L'auteur répond encore sur le forum en juin 2026. |
| sarfata/pypilot, seandepagnier/pypilot | **Non retrouvés** | Le dépôt officiel est pypilot/pypilot. Des forks existent (openplotter/pypilot, arn0/pypilot). |
| free-boat-projects/Sailboat_Autopilot | **Non retrouvé** | Aucune trace. Tout ce qui lui était attribué (FreeRTOS, BNO085, AS5048A, interface PID Wi-Fi) est à considérer comme non validé. |
| spascual90/Fenix | **Vérifié** | C++/Arduino, GPL-3.0, 112 commits, 24 étoiles, 10 issues ouvertes. |
| Fen-X/fenix-autopilot | **Non retrouvé** | Probable confusion avec Fenix de spascual90. |
| pieteroskam/autopilot (« Nautinect ») | **Vérifié, mais le code ne correspond pas au README** | ESP32, 66 étoiles, 12 forks, 82 commits. Le code source lu est un simple relais Bluetooth vers le moteur (voir 3.3). Licence contradictoire. |
| Milo-Autopilot | **Vérifié sous un autre nom** | Dépôt réel : **Milo-Pilot/Milo-Pilot** (23 commits, 6 étoiles). |
| marin-m/SailSim | **Non retrouvé** | Le compte marin-m héberge SongRec, QCSuper, etc. Vrais simulateurs rencontrés : sailsim (PyPI), sails-simulator/sailsd, SITL voilier d'ArduPilot. |
| SignalK/Signalk-Autopilot | **Vérifié, mal décrit** | Dépôt réel : signalk/signalk-autopilot. Ne gère que les pilotes Raymarine (NMEA 2000 et Seatalk 1), pas pypilot ni B&G. |
| ttlappalainen/NMEA2000 | **Vérifié** | C++, licence MIT, 491 commits. Bibliothèque générale ; ne mentionne pas les autopilotes. |
| Dépôts « actionneurs / compas BNO085 » | **Non vérifiable** | Catégories sans noms de dépôts précis. |

## 3. Fonctionnement technique

### 3.1 pypilot (Sean D'Epagnier)

**Architecture.** Un calculateur Linux (Raspberry Pi, Pi Zero W pour la distribution « tinypilot » qui utilise TinyCore Linux en système de fichiers lecture seule ; Debian/OpenPlotter ailleurs) fait tourner des serveurs Python : `pypilot_boatimu` (centrale inertielle), `pypilot_servo` (contrôleur moteur), plus des clients (web Flask, écran LCD, HAT GPIO, plugin OpenCPN, Signal K). Le moteur est piloté par un contrôleur à base d'Arduino relié en série (38 400 bauds, 4 fils, liaison optoisolée). Un utilisateur du forum OpenMarine l'a aussi associé à un module IBT-2 et à un Arduino Nano.

**Capteurs.** IMU 9 axes (ICM-20948 courant, MPU-9255 plus ancien) lu via la bibliothèque RTIMU (fork de l'auteur pour l'ICM-20948). Dans `boatimu.py`, des paramètres de Kalman sont configurés (`KalmanRk`, `KalmanQ`) et la fusion produit un quaternion d'orientation ; échantillonnage matériel à 100 Hz, traitement à 10 ou 20 Hz. Le cap, la gîte (filtrée), les vitesses angulaires et leur dérivée sont tirés du quaternion. Calibration : accéléromètre (6 faces), alignement à plat, compas 2D puis 3D par ajustement d'ellipsoïde, biais du gyroscope sauvegardé toutes les 60 s. Contrôles de santé : réinitialisation si le gyroscope ou le compas sortent de plages plausibles.

**Commande.** Modes compass, GPS, vent apparent, vent réel (et NAV via messages APB). Gains documentés dans le manuel : P (erreur de cap), I (souvent laissé à 0), D (vitesse de lacet, moteur principal de la correction), DD (dérivée seconde), PR (racine de l'erreur), FF (n'agit que pendant les changements de cap). Valeurs de départ du manuel : P = 0,003, D = 0,01. **Point clé : la sortie est une vitesse de moteur** (P = 0,003 signifie 0,3 % de la vitesse max par degré d'erreur). Le retour de barre est optionnel. `autopilot.py` (lu) limite l'erreur de cap à ±30° et intègre l'erreur de façon bornée.

**Pilotes disponibles (dossier `pilots/`).** Trois pilotes lus :
- `basic.py` (le pilote actif de base) : gains par défaut P (0,003), D (0,09), DD (0,075), PR (0,005) et FF (0,6) ; I désactivé (ligne commentée). Entrées : erreur de cap, vitesse de lacet filtrée (`headingrate_lowpass`), sa dérivée filtrée (`headingraterate_lowpass`) et la variation de la consigne de cap. Le second nombre de chaque déclaration de gain n'est pas documenté.
- `simple.py` : **désactivé** (`disabled = True`) ; P = 0,005, I = 0, D = 0,15 ; entrées : erreur de cap, son intégrale, vitesse de lacet filtrée.
- `learning.py` : **expérimental, désactivé et incomplet** (références à des variables non définies). Principe : un modèle de prédiction appris hors ligne (TensorFlow Lite) reçoit l'historique de capteurs et une séquence candidate de commandes de barre (−1, 0 ou +1) sur un horizon d'environ 0,4 s ; une fonction de coût (erreur de cap prédite, vitesse de lacet prédite lissée, amplitude de la commande) choisit la meilleure séquence et seule sa première action est appliquée. Sans modèle ou sans historique suffisant, il délègue au pilote `basic`. Les capteurs d'entrée sont listés dans un fichier de configuration du modèle non lu.

**Calcul de la commande** (`AutopilotPilot.Compute` et `AutopilotGain`, `pilots/pilot.py`, lus) : chaque gain a une valeur persistante bornée (et « profilable »), et une contribution par défaut égale à `entrée × gain` ; `Compute` **additionne simplement** les contributions de tous les gains. **Aucune saturation ni pas de temps dans ce code** : la conversion en commande de servo et les bornes éventuelles sont ailleurs (non lues).

**Paramètres du servo.** `servo.max_current` (4 à 7 A pour les pilotes à vérin ; 15 à 20 A pour l'hydraulique), `slew_speed`/`slew_slow` (rampes, 15 à 30), `period` (0,3 à 0,4 s), vitesses min/max, frein, embrayage (pleine puissance 200 à 300 ms puis PWM de maintien).

**Limites.** Pile logicielle lourde. En 2026, des utilisateurs signalent des échecs d'installation sur OpenPlotter 4 (paquet absent, dépendance swig, fork RTIMU). Activité réelle mais packaging fragile.

### 3.2 Fenix (spascual90)

**Architecture.** Sketch Arduino en C++ : `Autopilot`, `ActuatorManager` (qui hérite de `PID_ext`, `RudderFeedback`, `ActuatorController` et `CurrentFeedback`), `BearingMonitor`, `ICM20948AHRS`/`DevICM20948`, `IF_NMEA`/`emcNMEA`, `BT`. Carte Arduino : le modèle précis n'est pas indiqué dans les pages lues. Matériel : IMU Sparkfun ICM-20948 (seule IMU supportée depuis v4.0.B1), vérin 12 V à potentiomètre de retour (recommandation : 300 mm de course, 30 mm/s), shield dédié, application Android (Virtuino) en Bluetooth. La boucle principale (`Fenix.ino`) lit le GPS, rafraîchit les interfaces (NMEA, écran LCD à touches, Bluetooth selon les options) puis appelle `MyPilot.Compute()`.

**Commande (d'après Autopilot.cpp).** L'erreur de cap est calculée entre le cap cible et le cap courant ; le calcul utilise un cap « pour le contrôle » filtré des effets de vagues. Le résultat est une **consigne d'angle de barre** (le mode veille force la barre à 0), asservie en position grâce au potentiomètre du vérin. Un facteur de vitesse du bateau (limité à 0,4–1,6) adapte la réponse. Un identificateur de modèle de Nomoto (modèle simple de la réponse en lacet d'un bateau, paramètres K et T) s'adapte en continu quand les conditions sont calmes (erreur < 10°, barre < 5°). Un mécanisme de détection de blocage repasse en veille avec alarme.

**PID et vent.** RELEASE.md : anti-windup, limitation et remise à zéro de l'intégrale, filtre sur la dérivée (v3.5), intégrale/dérivée adaptées à la vitesse (v3.6), prédiction du lacet « pour information seulement » (v4.1). Le feedforward vent existe dans le code même si RELEASE.md n'en parle pas : voir 3.2.2 et 3.2.3.

**Modes.** Veille, Compas (virement de 100° possible), Nav (suivi de waypoint), Vent (avec source externe).

**Limites.** Documentation algorithmique dispersée ; l'autotune PID a été abandonné en v4.1.

#### 3.2.1 Chaîne de commande lue dans le code (ActuatorManager, ActuatorController, RudderFeedback)

Ajout du 2026-11-01. La chaîne comporte trois étages.

1. **Étage cap vers angle de barre** (`ActuatorManager::Compute`) : un modèle de référence (`FossenReferenceModel`) fournit cap désiré, vitesse et accélération de lacet ; un feedforward de Nomoto (`ReferenceFeedforward`) en tire une consigne de barre, plafonnée à ±10° par `ActuatorManager` ; le PID (`PID_ext`, sortie bornée entre barre min et max) travaille sur l'erreur de cap. La contribution du vent (`windFF`, ratio 0,50 à l'initialisation d'après `ActuatorManager.cpp` — **voir la mise à jour n° 3 en tête de fiche : 0,50 est `kAir`, le ratio démarre à 1,0**) est transmise au PID avec le facteur de vitesse du bateau. Détails de ces composants en 3.2.3. Valeurs de départ fixées dans `ActuatorManager.cpp` : Nomoto `setDirectDeltaParams(6,51 ; 2,65)` (voir correction en 3.2.3), `setLimits(3° /s ; 0,5° /s²)`, `setReferenceModelParams(0,3 ; 1,0 ; 0,1)`.
2. **Étage angle de barre vers vitesse du vérin** (`controlActuator`) : **ce n'est pas un PID**. On calcule l'écart entre la consigne de barre et la position lue. Sous un seuil (au moins 1°, lié à l'erreur de mesure du capteur), la vitesse passe à 0 ; un vérin arrêté ne repart que si l'écart dépasse 4 fois ce seuil (hystérésis). Au-dessus, la vitesse vaut `SPEED_CRUISE`, ou son tiers quand l'écart est sous 30. La vitesse change par pas de 5 par cycle (rampe). Une machine à états impose un temps d'arrêt (`ACTUATOR_STOP_TIME`, 300 à 500 ms typique d'après un commentaire) à chaque inversion de sens, avec une double vérification de la lecture du potentiomètre.
3. **Étage puissance** (`ActuatorController::setSpeed`) : PWM sur une broche (`analogWrite`) et une broche de sens, avec lissage exponentiel (5 % de la consigne, 95 % de la valeur précédente) et collage à 0 sous 30 ou à la vitesse max au-dessus de 220.

**Retour de position** (`RudderFeedback`) : lecture directe du potentiomètre par `analogRead` (10 bits), **sans filtrage**. Calibration par l'utilisateur : on fait sortir puis rentrer le vérin, le code retient les valeurs min et max. Les bornes effectives sont rétrécies de deux fois l'erreur de mesure à chaque extrémité. Conversion linéaire : étendue de la barre divisée par l'étendue utile en comptes. Le centre se déduit de la longueur utile, avec un décalage réglable. Le bruit est mesuré par 500 lectures espacées de 10 ms.

**Protections** : fins de course logicielles (la vitesse est forcée à 0 si on pousse contre une limite) ; blocage détecté par le maximum du courant sur 100 appels, avec seuil `getMaxCurrent()` (commentaires : environ 1 184 mA à vide, 1 300 mA pour le blocage) ; passage en veille avec alarme.

**Mode « actionneur virtuel »** (`VIRTUAL_ACTUATOR`) : la position est estimée sans capteur, en intégrant dans le temps la vitesse commandée. Sert au simulateur et montre qu'une estimation sans potentiomètre est prévue dans le code (précision non évaluée).

**Observations.** (a) Une variable `deadband` est déclarée mais jamais utilisée dans `controlActuator`. (b) La fonction `IBIT()` de l'actionneur utilise des `delay()` bloquants, au démarrage seulement. (c) Les valeurs des constantes (broches, vitesses) sont dans des en-têtes non lus. (d) Le `constrain` de l'issue #13 ne se trouve pas dans ces fichiers : voir 3.2.2.

#### 3.2.2 Feedforward vent et issue #13 (vérifié par lecture du code, non exécuté)

**Historique de la vérification.** Une version précédente de cette fiche situait le `constrain` « probablement dans `WindFF` ou `PID_ext` ». C'était faux : il est dans `Autopilot.cpp`, ligne 1775, que la première lecture (lignes 1 à 1000) ne couvrait pas.

**L'issue** (ouverte le 2026-10-26 depuis le compte de Mathieu, sans réponse du mainteneur, sans assigné ni pull request liée). Elle signale, dans `Autopilot::updateWindFeedforwardEvaluation()`, la ligne introduite par le commit b8410e5 :

`setWindFFratio (constrain (result.Cwind, 0.8f,-0.8f)*getWindFFratio());`

**Ce qui est établi par lecture du code :**
- La ligne 1775 est bien celle-ci (copiée par Mathieu depuis sa version locale). Aucune occurrence de `PID_ext` n'y figure (la seule dans `Autopilot.cpp` est à la ligne 1068, dans `Autopilot::SetTunings`).
- Calcul de `Cwind` (`WindFeedforwardEvaluatorSimple.cpp`, lu directement et recoupé par la session locale) : valeur par défaut `result.Cwind = 1.0f` (ligne 447), puis, si le feedforward moyen appliqué n'est pas nul, `Cwind = 0,8 × (meanStaticRudderDeg / meanAppliedFeedforwardDeg)` (ligne 472), avec `meanStaticRudderDeg = meanAppliedFeedforwardDeg + meanIntegralRudderDeg` (lignes 460 à 462). Aucun bornage de `Cwind` dans ce fichier ; il peut être négatif si la part intégrale s'oppose au feedforward.
- `setWindFFratio` (`WindFeedforward.h`, lu directement) : borne le ratio entre 0,5 et 2,0 ; valeur initiale 1,0 (ligne 208, seconde main). Dans `WindFeedforward.h`, `getWindFF()` n'utilise pas ce ratio : celui-ci s'applique dans `ActuatorManager::Compute` (`windFF.getWindFF() × windFF.getWindFFratio()`).
- Avec la macro Arduino habituelle `constrain(x, a, b) = x < a ? a : (x > b ? b : x)`, des bornes (0,8 ; −0,8) donnent 0,8 si x < 0,8 et −0,8 sinon. Exemples : x = 0,5 → 0,8 ; x = 0,8 → −0,8 ; x = 1,0 → −0,8. À noter : `getWindFF()` utilise, lui, des bornes dans le bon ordre : `constrain(-_yawMoment*0.1f, -10, 10)`.
- Conséquence : le ratio est multiplié par +0,8 (il baisse) ou par −0,8 (il devient négatif, puis `setWindFFratio` le ramène à 0,5). **Dans les deux cas le ratio ne peut que baisser ou tomber à 0,5 ; il ne peut jamais monter.** Le plafond de 2,0 est inatteignable.
- Une simple inversion des bornes, `constrain(x, -0.8f, 0.8f)`, ne corrigerait pas ce défaut : le multiplicateur resterait ≤ 0,8.

**Lecture de l'intention (inférence, non confirmée à l'écriture ; l'interprétation de la part cible est confirmée depuis : voir mise à jour n° 2).** Le rapport `meanStatic / meanApplied` vaut 1 + (part intégrale ÷ part feedforward) : il dépasse 1 quand le terme I doit compenser un feedforward trop faible, et passe sous 1 quand le feedforward est trop fort. Multiplié par 0,8, `Cwind` vaut exactement 1 quand le feedforward fournit 80 % de la barre nécessaire et l'intégrale les 20 % restants (et 0,8 quand l'intégrale n'ajoute rien). Le 0,8 ressemble donc à une **part cible de feedforward de 80 %**, et `Cwind` à un **multiplicateur centré sur 1** (1 = rien à corriger). Deux indices vont dans ce sens : la valeur par défaut de `Cwind` est 1,0 (élément neutre d'une multiplication), et le ratio lui-même démarre à 1,0. Si cette lecture est juste, **tout bornage correct doit contenir 1,0**, ce que ni (0,8 ; −0,8) ni (−0,8 ; 0,8) ne font, alors que la proposition de l'issue (0,8 ; 1,2, soit ±20 % par estimation) le fait. La valeur 1,2 reste un choix indicatif. À la valeur par défaut (1,0, « neutre »), la ligne actuelle fait tomber le ratio à 0,5 : le comportement serait donc l'inverse de la neutralité.

**Effet pratique possible (non mesuré).** Après une première estimation terminée, la contribution du vent serait réduite de moitié ou plus et ne pourrait plus remonter. On ne sait pas à quelle fréquence `updateWindFeedforwardEvaluation` s'exécute ni dans quelles conditions (non lu). Le ratio sert à adapter le modèle de vent au bateau (voir 3.2.3, point sur la table Cn).

**Non vérifié :** la définition de `constrain` dans le cœur Arduino pour la carte utilisée (F12 dans VS Code) ; l'exécution réelle ; l'intention de l'auteur ; la cible de 80 % (`targetFeedforwardShare()` non lue à l'écriture, confirmée à 0,80f depuis) ; les lignes 464 à 485 du fichier de l'évaluateur (code commenté, signalé par la session locale comme une ancienne régression abandonnée) ; les remarques secondaires de l'issue (faible confiance).

**Suite donnée.** Un commentaire a été rédigé pour l'issue #13 (tableau de valeurs de `constrain`, origine de `Cwind`, effet sur le ratio, question sur l'intention). Il devait être publié par Mathieu lui-même ; statut à l'écriture inconnu, **publié depuis** (voir mise à jour n° 1).

#### 3.2.3 Composants de régulation lus le 2026-11-01

**`PID_v1_ext.cpp`** (dans `libraries_ext/`) : PID calculé à chaque période d'échantillonnage, en mode automatique seulement.
- Erreur = consigne − mesure, corrigée d'une **zone morte** (`error_eff = error − deadband × signe`). P : `kp_eff × error_eff`. I : `ki_eff × error_eff` accumulé, borné par la sortie max divisée par `I_MAX_COEFICIENT`.
- Adaptation à la vitesse du bateau : `kp` et `ki` multipliés par `facteur²`, `kd` divisé par `facteur`.
- D agit sur la **mesure** (et non sur l'erreur) avec un filtre passe-bas.
- **Feedforwards** : `FF = getRefFeedForward() × 10` et `windFF = getWindFeedForward() × 10` ; sortie libre = P + I + D + FF + windFF. Le facteur 10 convertit des degrés en « unités de barre » : **une unité vaut donc un dixième de degré** (déduction de la conversion).
- **Anti-windup** : l'intégration est bloquée quand la sortie est saturée du même côté que l'erreur, ou quand l'actionneur est occupé, ou pendant la zone morte, ou quand un feedforward est actif ; dans ce cas l'intégrale décroît de 1 % par cycle (le commentaire du code parle de « back-calculation », ce que le code ne fait pas).
- **Zone morte automatique** (`AUTODB`) : le calcul existe mais l'appel est en commentaire dans `Compute` ; la zone morte n'est donc jamais recalculée (cohérent avec RELEASE.md : « deadband automatique, non implémenté »).
- Les constantes (`ALFA_*`, `MAX_PID_TURN`, `I_MAX_COEFICIENT`, etc.) sont définies ailleurs, valeurs inconnues.

**`FossenReferenceModel.cpp`** : génère une trajectoire de cap désirée du troisième ordre (cap `psi_d`, vitesse `r_d`, accélération `a_d`) vers le cap cible, par intégration d'Euler, avec saturations. Paramètres de `setReferenceModelParams(0,3 ; 1,0 ; 0,1)` : pulsation de bande passante `ω_b` (donne la pulsation naturelle `ω_n`), amortissement `ζ` et facteur du gain intégral. Limites : vitesse de lacet 3° /s et accélération 0,5° /s² (valeurs fixées par `ActuatorManager`). **Les gains du PID en sont dérivés** : `Kp = 10 ω_n²`, `Kd = 10 × 2ζ ω_n`, `Ki = 10 × facteur_intégral × ω_n³` ; le code précise que c'est un point de départ à ajuster au bateau. Défaut relevé : `computeWnFromWb()` est déclarée `float` sans instruction `return` (comportement indéfini en C++, même si `ω_n` est assigné).

**`ReferenceFeedforward.cpp`** : feedforward de Nomoto inversé, `delta_ff = Kff × (accélération de lacet désirée + vitesse de lacet désirée / T)`. `Kff` joue le rôle de 1/K de Nomoto (interprétation). **Correction d'une lecture antérieure** : les valeurs 6,51 et 2,65 de `setDirectDeltaParams` sont **Kff et T**, et non K et T. La sortie est en radians ; ses limites par défaut sont ±90°, ramenées à ±10° par `ActuatorManager`. Un gain de barre (−5 à +5) module le feedforward. Les commentaires mentionnent une saturation de `tau_ff` qui n'existe pas dans le code.

**`WavePassiveObserver.cpp`** (membre `waveObserver` de `BearingMonitor`) : le fichier ne mentionne pas Fossen. Observateur à deux composantes avec correction par l'innovation de cap : un modèle basse fréquence de type Nomoto avec biais lent, et un oscillateur du second ordre pour la vague. États : cap et vitesse de lacet basse fréquence, composante de vague, biais, pulsation de vague. **Entrées : cap mesuré, position de barre et, en option, vitesse de lacet de l'IMU. Roulis, tangage et accélérations ne sont pas utilisés.** La période de vague est estimée par passages par zéro (acceptée entre 2 s et 15 s) avec un indice de confiance. Défauts de départ : `Tnomoto = 5 s`, `Knomoto = 0,25`. Le drapeau d'activité du filtre est exposé mais non utilisé dans la mise à jour.

**`WindFeedforward.h`** : moment de lacet dû au vent, `tauWind = kAir × Vaw² × Cn(angle)`, avec une table de 36 coefficients (pas de 10°). **Le fichier précise que les valeurs de la table sont des exemples à remplacer par des coefficients identifiés pour le bateau.** Sortie : `getWindFF() = constrain(−moment × 0,1, −10, +10)`, en degrés de barre, avec filtre d'entrée de 1 s et hystérésis du vent (0,6 / 0,4 m/s). Si la mesure du vent devient invalide, la sortie décroît vers zéro en 1,5 s. Incohérence de nommage relevée : la documentation cite `WIND_FF_INVALID_DECAY_TIME_S`, la macro définie est en millisecondes.

**`DevICM20948.cpp`** : n'expose en fonctionnement que le cap, la vitesse de lacet et un indicateur lié au magnétomètre ; ni roulis, tangage ni accélération. Gère la calibration (gyroscope, accéléromètre en 6 positions, magnétomètre en huit) et son stockage en EEPROM. `getCalibrationStatus()` est déclarée `bool` sans `return` (comportement indéfini).

### 3.3 Nautinect / pieteroskam/autopilot

**Correction importante (2026-11-01).** Les versions précédentes de cette fiche décrivaient Nautinect d'après son README, et le présentaient comme un système où « un seul ESP32 fait tout ». **C'est faux pour le code source lu** : voir 3.3.1.

**Contenu du dépôt (liste vue sur GitHub).** `autopilot-main.ino`, `Bluetooth.cpp/.h`, `Motor.cpp/.h`, `README.md`, `LICENSE` et un dossier `build/esp32.esp32.esp32doit-devkit-v1` (non inspecté). Matériel annoncé : ESP32, pilote de moteur IBT-2 (jusqu'à 40 A d'après le README) ou L298N. Application mobile Android/iOS reliée en BLE.

**Fonctions annoncées dans le README, non retrouvées dans le code source lu.** Sources de cap : boussole interne (gyro et magnétomètre calibrables), cap et GPS du téléphone (le téléphone exécute alors la boucle de contrôle), vent apparent/réel, boussole externe via PGN 127250. Gains : global, P, I, D, DD, FF, précision (zone morte). Mode TRACK : consigne = relèvement + gain × écart transversal, limitée à ±45°. Retour de barre : aucun, tension ou impulsions (commande 36). NMEA 0183 en RS-422 (4 800 bauds) ou UDP Wi-Fi ; NMEA 2000 par PGN propriétaires et PGN standard ; canal N2K binaire sur BLE depuis le firmware 4.4.1. Verrouillage par PIN.

**Observations.** Le vocabulaire des gains et le guide de réglage reprennent visiblement ceux de pypilot. Licence contradictoire : GPL-3.0 (fichier LICENSE) contre CC BY-NC-SA 4.0 non commercial (section du README) ; l'auteur vend aussi des unités (95 €). Le README cite `autopilot_ble.ino`, absent de la liste des fichiers. Puce IMU non nommée dans les pages lues.

#### 3.3.1 Code source open source lu (autopilot-main.ino, Bluetooth.cpp/.h, Motor.cpp/.h)

**Rôle réel de ce code : un relais Bluetooth vers le moteur.**

- `autopilot-main.ino` : `setup()` initialise le port série, le moteur (`Motor::setup()`) et le Bluetooth (`Bluetooth::setup()`) ; **`loop()` est vide**. Les appels `compass_setup()`, `ota_wifi_setup()`, `button_setup()` et `display_setup()` sont en commentaire.
- `Bluetooth.cpp` : une commande `motor<valeur>` reçue par BLE devient `Motor::set(|valeur|, sens)` (valeur négative = sens 0, sinon sens 1) ; une commande `apOn,0` met la broche GPIO 15 à LOW (embrayage), toute autre valeur la met à HIGH ; à la déconnexion, `Motor::set(0, 0)`. Aucune limite de vitesse min/max, **aucune durée ni temporisation de sécurité** sur une commande. `FIRMWARE_VERSION = 2` (`Bluetooth.h`). Les commandes numérotées du README (7, 8 à 13, 36, 43, 61, 62) n'apparaissent pas.
- **Aucune boussole, IMU, régulateur, gain ni retour de barre** dans aucun des cinq fichiers sources. La boucle de cap n'est donc pas dans ce firmware : d'après le code et le README (source de cap « téléphone »), elle tourne dans l'application mobile, dont le code n'est pas dans le dépôt.
- **Hypothèse non vérifiée** : les fonctions riches du README (gains, retour de barre, NMEA, firmware 4.4.1) correspondent à un firmware plus récent que la version 2 du code source, peut-être distribué compilé (dossier `build/`, unités vendues). À vérifier.

**Chaîne moteur (Motor.cpp, Motor.h).**
- `Motor::set(vitesse, sens)` : PWM 8 bits (0 à 255) sur `RPWM_PIN = 33` ou `LPWM_PIN = 32` selon le sens, l'autre broche à 0. Le tableau de câblage du README donne l'inverse (R_PWM sur GPIO 32, L_PWM sur GPIO 33) : désaccord de nommage à garder en tête au câblage (une inversion ne fait que renverser le sens).
- **Aucune rampe** de vitesse et **aucun délai à l'inversion de sens**. Pas de zone morte (un commentaire cite seulement 50 % de PWM comme vitesse de démarrage correcte).
- **Courant.** `Motor::max_current = 2000` (commentaire : « should be 500 », unités non précisées) ; si `current > max_current`, le moteur s'arrête et le drapeau de fin de course du sens concerné est levé, jusqu'à une commande en sens inverse. **Mais la ligne qui mesure le courant est en commentaire** (`//current = current*0.99+analogRead(CS)*0.01;`) et **rien dans les cinq fichiers sources n'écrit `Motor::current`** : il reste à 0 et la protection ne peut jamais se déclencher. `CS_PIN = 35` est déclaré dans `Motor.h`. Le README laisse par ailleurs les broches R_IS et L_IS de l'IBT-2 non branchées. Les butées sont purement logicielles.
- **Défauts mineurs relevés** : à vitesse nulle, l'état « en marche » est remis à vrai après l'arrêt ; une vitesse négative n'est pas bornée.
- **Observation de sécurité (d'après la lecture)** : tant que la liaison BLE reste connectée, la dernière commande moteur reste appliquée, sans temporisation. Seule la déconnexion arrête le moteur.
- **Conclusion prudente** : dans le code source lu, Nautinect est un relais sommaire ; il est utile comme exemple de protocole BLE et d'interface téléphone, pas comme référence de régulation ni de protection du moteur.

### 3.4 Milo (Milo-Pilot/Milo-Pilot)

**Architecture.** Arduino Nano compatible, IMU Bosch BMX055, pont en H, bibliothèque BMX055 modifiée ; code dans le dossier `Milo` (Milo.ino version 7) plus une bibliothèque locale (ce n'est donc pas un fichier unique au sens strict).

**Commande (Milo.ino).** `Command = KHEAD × écart + KDERIV × vitesse de lacet du gyroscope` avec KHEAD = 1,0 et KDERIV = 4,0 : c'est un régulateur **proportionnel-dérivé** (le README dit « PID sans I »). Bande morte de base 7°, qui se réduit jusqu'à environ 3° quand l'écart reste faible sur une fenêtre de 100 échantillons. Le moteur est commandé **en tout-ou-rien** (pas de PWM). Le cap est un filtre complémentaire : 90 % du gyroscope intégré, 10 % du magnétomètre. Protection : si le courant dépasse un seuil, sorties coupées 3 s puis reprise seulement dans le sens opposé. Calibration : deux cercles, centrage min/max du magnétomètre, offsets en EEPROM.

**Faiblesses relevées dans le code.** Terme dérivé non projeté sur la verticale (faussé par la gîte), délais bloquants (50 ms et 3 000 ms), pas de cadence de boucle fixe, pas de licence visible.

**Mécanique.** L'affirmation « moteur sur la barre entraînant une drosse en boucle » **n'est confirmée ni par le dépôt ni par la page d'accueil du site**. Le site indique : barre franche, débrayable, silencieux, utilisable comme verrou de barre, **brevet FR3124791**. À vérifier avant de s'inspirer de la mécanique.

### 3.5 Signal K et NMEA2000

- **signalk/signalk-autopilot** : interface graphique émulant une télécommande Raymarine et API PUT (cap cible, angle de vent cible, état standby/auto/wind/route, virement). Supporte uniquement Raymarine NMEA 2000 et Seatalk 1. Le serveur Signal K dispose aussi d'une API Autopilot générique avec plugins « fournisseurs » ; pypilot passe par un plugin fournisseur distinct.
- **ttlappalainen/NMEA2000** : bibliothèque C++ gérant les exigences obligatoires de la norme NMEA 2000 ; il faut fournir un pilote CAN hors Arduino. Brique utile seulement si le pilote doit lire le vent ou la vitesse sur un bus N2K.

### 3.6 Chaîne moteur comparée

| | Qui décide / qui pilote le moteur | Interface du pilote moteur | Retour de position de barre | Rampe de vitesse | Délai à l'inversion | Courant mesuré et utilisé |
|---|---|---|---|---|---|---|
| Nautinect (code source lu) | L'application du téléphone décide ; l'ESP32 relaie les ordres au moteur | Deux PWM (un par sens) vers un IBT-2 | Aucun dans le code lu (le README annonce aucun/tension/impulsions) | Non | Non | Non (jamais écrit) |
| pypilot | Raspberry Pi décide, carte Arduino dédiée pilote | Liaison série 38 400 bauds | Optionnel | Oui (`slew_speed`, `slew_slow`) | Non vérifié | Oui (`max_current`) |
| Fenix | Un seul Arduino | Une PWM et une broche de sens | Obligatoire (potentiomètre) | Oui (pas de 5 par cycle) | Oui (300 à 500 ms, commentaire) | Oui (détection de blocage) |
| Milo | Un seul Nano | Marche/arrêt sur deux entrées | Aucun | Non (tout-ou-rien) | 50 ms | Oui (coupure 3 s) |

### 3.7 Gîte, accélérations et NMEA : relevé du code (2026-11-01)

**Question posée : la gîte agit-elle sur la commande de barre ?** Réponse, dans les fichiers lus : **non, ni dans pypilot ni dans Fenix**.

**pypilot.**
- `autopilot.py`, `pilots/basic.py`, `pilots/simple.py`, `pilots/learning.py` et `pilots/pilot.py` ne contiennent aucune occurrence de `heel`, `roll` ni `pitch`. La commande dépend de l'erreur de cap, de la vitesse de lacet filtrée, de sa dérivée filtrée et de la variation de la consigne (3.1). Le pilote expérimental `learning` pourrait utiliser d'autres capteurs via son fichier de configuration, non lu.
- La gîte est calculée dans `boatimu.py` (filtre passe-bas simple, alerte au-delà de 35° de roulis ou de tangage, correction d'inclinaison du compas) et publiée vers Signal K : d'après un extrait de `signalk.py` cité sur le forum OpenMarine, `navigation.attitude` (pitch, roll, yaw), `navigation.headingMagnetic` et `navigation.rateOfTurn` sont issus de l'IMU.
- Selon un message du forum (auteur non affiché dans l'extrait), pypilot ne calcule pas en interne le pilonnement, l'avance ni la dérive latérale, mais le terme `imu.accel_residuals` (accélération débarrassée de la gravité) les contiendrait, à faire pivoter selon la pose avant usage. Non vérifié dans le code.
- Non lus : la conversion de `command` en commande de servo (bornes éventuelles) et d'éventuels autres pilotes du dossier `pilots/`.

**Fenix.**
- `ICM20948AHRS.cpp` : filtre de Mahony (Kp = 50, Ki = 0) ; le cap vient directement du quaternion ; **roll et pitch sont calculés mais servent uniquement à projeter la vitesse de rotation du capteur sur la verticale** (`psi_dot`), puis ne sont exposés par aucune fonction. Cap et vitesse de lacet sont filtrés (constantes de temps de 0,1 s et de 0,5 s ; vitesse de lacet bornée à ±20°/s environ). Cette projection sur la verticale est justement ce qui manque à Milo (3.4).
- `DevICM20948.cpp` : n'expose en fonctionnement que cap, vitesse de lacet et un indicateur du magnétomètre. **Pour faire agir la gîte sur la commande, il faudrait donc d'abord exposer le roulis déjà calculé dans `ICM20948AHRS.cpp`.**
- `BearingMonitor.cpp` et `WavePassiveObserver.cpp` : aucune utilisation de roll, pitch ni accélérations. L'observateur de vagues sert à ne pas réagir aux oscillations, pas à anticiper (3.2.3).
- `PID_v1_ext.cpp` : la sortie libre est la somme P + I + D + FF + windFF (3.2.3), ce qui montre où un terme de plus (par exemple un terme de gîte) pourrait s'ajouter. Hypothèse de conception, non testée.
- Non lu : la fin d'`Autopilot.cpp` (hors extrait de seconde main).

**Précédents hors dépôts étudiés.**
- Le guide de réglage du pilote B&G H5000 (copie hébergée par un site de classe J/109) décrit un réglage « Heel Compensation » : protection contre l'auloffée causée par le roulis par mauvaise mer ou rafales, en appliquant la bonne compensation de barre **avant** que l'événement ne devienne dangereux ; désactivé par défaut (0), niveau 1 (faible) si utilisé ; il recommande d'attendre environ une minute après l'engagement du pilote pour que la tendance à remonter au vent se stabilise avant de régler le gain de gîte.
- Deux brevets anciens décrivent la même famille d'idées : un pilote marin avec compensation de roulis agissant sur le signal de barre (US5152239) et un pilote dont le gain du terme dérivé s'adapte à la fréquence de roulis pour réduire l'usure de la barre (US5179905). Statut juridique non vérifié ; je ne suis pas juriste.

**NMEA.**
- **Fenix, trames reçues** (`IF_NMEA.cpp`, `emcNMEA.cpp`) : APB (route), HDG et HDT (cap externe), MWV et VWR (vent apparent, vent vrai), vitesse fond (analyseur : RMC, VTG), et trames propriétaires `$PEMC` (requêtes et réglages). **Le caractère propriétaire des trames `$PEMC` est vérifié.** Types lus : 01 et 02 (cap, barre), 03 et 04 (installation), 05 et 06 (gains PID), 07 et 08 (informations du pilote), 09 (calibration IMU), 11 (sauvegarde), 14 (valeurs de calibration de l'ICM-20948), 99 (réinitialisation EEPROM).
- **Fenix, trames émises** : RSA (angle de barre), HDG (si pas de cap externe), `$PEMC` 03, 05, 07, 12 et 13, et une ligne de télémétrie non NMEA sur le port de debug (contributions Kp, I, Kd, anticipation de barre, anticipation de vent). APB existe mais n'est pas appelée dans le fichier lu.
- **Aucune trame de roulis, tangage, gîte ou attitude** dans ce que j'ai lu de Fenix (`emcNMEA.cpp` : environ 1 000 des 1 639 lignes).
- **pypilot** : l'attitude passe par Signal K (`navigation.attitude`). Un utilisateur a dû la convertir via Node-RED en phrase propriétaire Furuno pour la lire sur un traceur, ce qui laisse penser qu'il n'y a pas de phrase NMEA 0183 standard commode pour cela (déduction, non vérifiée sur la norme).
- **Conséquence pratique** : si la gîte est mesurée par l'IMU du pilote lui-même, le NMEA n'intervient pas ; il ne servirait qu'à importer la gîte d'un autre instrument ou à l'exporter.

### 3.8 SimplePilot (offgridsystems/SimplePilot) et raccordement d'un joystick

**Dépôt.** Pilote de barre de moteur hors-bord, ESP32, IMU ICM-20948 en mode DMP (fusion faite par la puce), vérin linéaire, joystick 2 axes, sortie DAC pour l'accélérateur (« cruise »). 18 commits, 0 étoile, **aucune licence indiquée**, première activité visible en avril 2026. Le README indique un codage et un débogage assistés par des IA (Gemini et freebuff). Écart de version entre le fichier `.ino` (v2.12) et la documentation (v2.14).

**Régulation (pilot.ino, lu).** P + I sur l'erreur de cap (plafonnée à `MAX_ERROR_DEG`), avec intégrale bornée et bloquée dans l'hystérésis (3°, valeur du README). Sortie : vitesse = `MIN_AUTO_SPEED + |sortie PI|` (bornée) et durée d'impulsion = `|sortie PI| × PULSE_GAIN` (20 ms minimum). **Aucun terme sur la vitesse de lacet dans le code lu**, et **aucune connaissance de la position du vérin** (ni capteur, ni butées, ni mesure de courant dans ce fichier). Sens choisi par appel de `moveRight()`/`moveLeft()`, définies ailleurs. Valeurs des constantes non fournies.

**Cap (heading.ino, lu).** Cap tiré du quaternion DMP, plus la déclinaison ; protection contre les valeurs invalides (NaN). Le fichier ne normalise pas le quaternion et ne contient pas les protections « saut de 15° », « plafond de 45° » ni « délai de 5 s » annoncées par le README (qui renvoie à la v2.14) : écart à vérifier.

**Reprise de main.** Si le joystick sort de sa zone morte, le moteur passe à pleine vitesse (255), l'intégrale est remise à zéro et la cible de cap est recalée sur le cap actuel ; au relâchement le pilote reprend. Le README annonce aussi une rampe et une protection d'inversion ; elles n'apparaissent pas dans `pilot.ino`.

**Raisonnement (non testé) sur le terme I.** Quand le régulateur commande la vitesse du vérin, la position de la barre est déjà l'intégrale de ces ordres : le terme P agit comme un terme intégral sur la barre, et un vrai terme I s'ajoute en double intégration, ce qui favorise les oscillations. pypilot, qui commande aussi une vitesse, laisse I presque toujours à 0 (manuel et pilote de base).

**Brancher un joystick ou une manette à pypilot ou à Fenix (faisabilité).**
- **pypilot** : accepte des commandes externes par son interface réseau interne (`pypilot_client ap.heading_command=180`). Un projet tiers (`marcobergman/pypilot_ray`) pilote pypilot avec un clavier GPIO sur ce principe : en veille, des touches envoient `servo.command` ; à l'engagement, la consigne est fixée au cap actuel (`ap.heading_command`), puis `ap.enabled` est activé. Sur le forum (février 2024), l'auteur indique la marche à suivre : désactiver le pilote (`ap.enabled = False`), puis envoyer `servo.command` (vitesse, de −1 à 1) ou `servo.position_command` (angle absolu, avec retour de barre), puis réactiver le pilote une fois la barre centrée ; il dit envisager de gérer ce type de joystick, donc non géré en natif. La question de savoir si le servo s'arrête de lui-même aux butées n'a pas de réponse claire dans l'extrait lu.
- **Fenix** : pas d'interface réseau équivalente ; il faudrait ajouter un module au programme. Fonctions publiques lues dans `Autopilot.h` : `changeRudder(delta)` (déplacement **relatif**), `setCurrentMode(STAND_BY)`, `Start_Stop(CURRENT_HEADING ou CURRENT_TARGET)`, `setTargetBearing`. Les actions `INC_RUDDER_1`, `INC_RUDDER_10`, `DEC_RUDDER_1`, `DEC_RUDDER_10` et `STOP_RUDDER` existent (pas courts et longs) ; leur traitement n'a pas été lu. Une lecture de joystick analogique sur Arduino serait sur 10 bits (centre autour de 512) ; broches libres du shield non vérifiées.
- **Points de sécurité à prévoir** : fins de course ; arrêt du moteur si le programme du joystick cesse d'envoyer des commandes ; désengagement puis réengagement propre sur le cap actuel ; éventuelle coupure matérielle indépendante du logiciel (piste générale, vue dans aucun des dépôts).
- Rien n'est décidé quant au type de joystick ni à la plateforme.

## 4. Trois philosophies de commande (constat central)

| Approche | Sortie du régulateur | Retour de barre | Exemple |
|---|---|---|---|
| Vitesse du moteur | Vitesse moteur proportionnelle à erreur et vitesse de lacet | Optionnel | pypilot |
| Angle de barre (asservissement en position) | Angle de barre visé, vérin asservi par potentiomètre | Obligatoire | Fenix |
| Tout-ou-rien avec bande morte | Marche avant/arrière/arrêt | Aucun (mesure de courant) | Milo |

Nautinect n'entre pas dans cette grille pour son code source lu : le régulateur y est absent (il serait dans l'application). SimplePilot commande la vitesse et la durée d'impulsion du vérin sans connaître sa position (proche de la première ligne, avec un P + I et sans retour).

## 5. Décisions et propositions

### Décision de Mathieu (2026-11-01)

- **Le vérin linéaire est la partie commune du projet** : tous les systèmes étudiés, sauf Milo, s'organisent autour de lui. **Milo sera un projet distinct** si Mathieu décide de le pousser. → formalisée (proposée) dans `conception/decisions-et-dispositions-2026-11-02.md (DP-01)`.
- La session reste une **phase d'exploration à intérêts diversifiés** : aucun choix de plateforme, de joystick ni de dimensionnement n'est demandé ni pris.

### Propositions (rien de décidé)

- **Fenix** reste la référence la plus proche (barre franche, vérin linéaire à potentiomètre, ≤ petit voilier, GPL-3.0) ; Mathieu l'a déjà identifiée comme source. Les paramètres de départ de Fenix (modèle de vent à table d'exemple, Nomoto de départ, valeurs de `Autopilot.cpp` calées pour un bateau de 12 m) devront être réidentifiés pour un petit bateau.
- **pypilot** : source d'idées pour la calibration IMU, les paramètres de servo (courant max 4 à 7 A pour un pilote à vérin) et la méthode de réglage des gains ; son pilote expérimental `learning` (prédiction par modèle appris) est un précédent de contrôle anticipatif, non abouti. Pas une architecture à copier (Linux, sans interface téléphone souhaitée).
- **Milo** : référence minimaliste de loi de commande et de protection en courant ; mécanique à ne pas copier sans vérifier le brevet. Idée évoquée en conversation : lui ajouter un retour de position de barre pour s'approcher de Fenix. Cette piste relève maintenant du projet distinct décidé plus haut.
- **Nautinect** : dans son code source lu, un relais BLE vers le moteur dont le « cerveau » est dans le téléphone, à l'opposé du choix de ne pas utiliser le téléphone comme interface ; sa couche moteur est la plus sommaire des quatre (3.6). Intérêt limité : exemple de protocole BLE et de commande d'embrayage (broche GPIO 15).
- **SimplePilot** : à retenir comme idée la chaîne minimale (ESP32 + centrale), la reprise de main instantanée au joystick avec recalage de la cible, et l'interface physique sans téléphone. Comme il n'a pas de licence et un code jeune assisté par IA, il ne peut servir que d'inspiration, pas de base de code.
- **Retour de position avec le vérin** : la piste la plus simple est un vérin à potentiomètre intégré, que Fenix suppose. Capteur d'angle sur le pivot et estimation sans capteur restent des alternatives non retenues. Le dimensionnement du vérin (course, vitesse, force) dépend de la longueur de barre, du déplacement du bateau et du type de safran, non encore fournis.
- **Anticipation par capteurs inertiels (gîte, accélérations)** : voir `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md` et 3.7.

## 6. À vérifier ensuite

1. Confirmer la définition de `constrain` pour la carte utilisée (F12 sur `constrain` dans VS Code).
2. Comprendre quand `updateWindFeedforwardEvaluation` s'exécute (la cible de 80 % est confirmée : voir mise à jour n° 2).
3. ~~Publier (ou non) le commentaire sur l'issue #13~~ — publié (mise à jour n° 1) ; l'intention de l'auteur reste à obtenir de lui avant tout correctif.
4. Nautinect : inspecter le dossier `build/` et chercher où se trouve le firmware 4.x que décrit le README (hypothèse d'un firmware compilé distribué à part).
5. Fenix : lire la classe d'identification de Nomoto (`nomotoId`), `WindFeedforward.cpp` (table Cn) et la fin d'`Autopilot.cpp` ; vérifier les numéros de ligne de `PID_v1_ext.cpp` ; modèle d'Arduino requis, pilote moteur recommandé, fin d'`emcNMEA.cpp`.
6. pypilot : conversion de `command` en commande de servo (bornes éventuelles), contrôleur moteur (délai d'inversion, arrêt aux butées, temporisation si les commandes cessent), fichier de configuration du pilote `learning`.
7. SimplePilot : lire `simplepilot_v2.12.ino` et les fichiers de mouvement (`moveRight`, `moveLeft`, `StopActuator`) pour confirmer rampe, protection d'inversion et cinq protections annoncées.
8. Statut réel du brevet FR3124791 avant toute inspiration mécanique (je ne suis pas juriste).
9. Dates de dernier commit de chaque dépôt (non obtenues).
10. Valeurs des constantes de l'actionneur Fenix (vitesses, broches, courants) dans les en-têtes.
11. Dimensionnement du vérin (course, vitesse, force) : longueur de barre, déplacement du bateau, type de safran.
12. (Ajout) Le feedforward vent agit-il en mode compas ou seulement dans les modes vent ?

## Sources

- https://github.com/pypilot/pypilot (autopilot.py, pilots/basic.py, pilots/pilot.py, pilots/simple.py, pilots/learning.py, boatimu.py) et https://github.com/pypilot/workbook/wiki
- https://github.com/spascual90/Fenix (Fenix.ino, Autopilot.cpp [début], Autopilot.h, ActuatorManager.cpp/.h, ActuatorController.cpp, RudderFeedback.cpp, BearingMonitor.cpp/.h, ICM20948AHRS.cpp, DevICM20948.cpp, libraries_ext/PID_v1_ext.cpp, FossenReferenceModel.cpp, ReferenceFeedforward.cpp, WavePassiveObserver.cpp, WindFeedforward.h, WindFeedforwardEvaluatorSimple.cpp, IF_NMEA.cpp, emcNMEA.cpp [partie visible], Order.h, RELEASE.md), https://github.com/spascual90/Fenix/issues/13 et https://fenix-autopilot.com/
- Compte rendu de la session Claude Code locale de Mathieu (ligne 1775, `WindFeedforward.h`, `PID_v1_ext`) : seconde main
- https://github.com/pieteroskam/autopilot (README, autopilot-main.ino, Bluetooth.cpp, Bluetooth.h, Motor.cpp, Motor.h)
- https://github.com/Milo-Pilot/Milo-Pilot (Milo.ino) et https://www.milo-autopilot.com
- https://github.com/offgridsystems/SimplePilot (README, pilot.ino, heading.ino)
- https://github.com/SignalK/signalk-autopilot
- https://github.com/ttlappalainen/NMEA2000
- https://forum.openmarine.net (fils pypilot 2024 et 2026, dont les échanges sur `navigation.attitude`, `imu.accel_residuals` et la commande manuelle du servo) et https://github.com/marcobergman/pypilot_ray
- Guide de réglage du pilote B&G H5000 (copie sur vs.j109.org) ; brevets US5152239 et US5179905
- https://pypi.org/project/sailsim/ et https://github.com/sails-simulator/sailsd
