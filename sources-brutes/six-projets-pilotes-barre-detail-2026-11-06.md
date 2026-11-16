---
type: analyse
statut: en-cours
verification: a-verifier
date: 2026-11-06
aliases: [six projets pilotes, comparatif détaillé pilotes open source, six projets à code public]
---

# Six projets DIY de pilotes automatiques à code public — techniques, fonctionnement, particularités, possibilités et limites

Cette note approfondit la liste de six projets établie le 6 novembre 2026 (pypilot, Fenix, The Plot Device de Jeff Burright, YAAAP, Jack Edwards Autopilot, KastB boat_autopilot). Pour chacun, elle décrit les techniques employées, la chaîne de fonctionnement, ce qui le distingue, ce qu'on pourrait en tirer de plus, et ses limites. Une dernière section met les six côte à côte au regard de la cible du projet : **barre franche, voilier ≤ 8 m, vérin linéaire générique, NMEA/OpenCPN souhaité, mode vent prévu**. *Mise à jour du 6 novembre 2026 : un mobile ou une tablette **dédiés** au pilote sont désormais une option possible d'interface (le critère « sans téléphone » des comparaisons ci-dessous reste utile, mais n'est plus éliminatoire).*

Pour pypilot et Fenix, l'analyse du code est déjà faite en profondeur dans [[Validation et analyse technique des dépôts open source de pilotes automatiques]] (fiche `analyse-depots-open-source-pilotes`). Ici, je n'en reprends que l'essentiel, et j'ajoute surtout les possibilités et limites. Les quatre autres projets ont été lus pour cette note.

## 0. Méthode, niveaux de preuve et limites

**Ce qui a été lu directement (6 novembre 2026).**
- The Plot Device : README, `Autopilot_ESP32_2.1.ino` (déclarations), `PIDtiller.ino`, `Output.ino` ; fil CruisersForum de l'auteur.
- YAAAP : README, `yaaap/yaaap.ino` ; fil francophone du forum Arduino.
- Jack Edwards : page du dépôt CoyoteWaits (README non lisible par l'outil) ; reportage de 2013 (blog *The Marine Installer's Rant*) ; article Hackaday de 2014 ; article Firgelli d'une reproduction.
- KastB : README, `autopilot.ino`, `libraries/PID/PID.cpp`.

**Recherche complémentaire (6 novembre 2026, second passage).** Nomenclatures officielles (Fenix, PDF de pièces de The Plot Device, manuel pypilot, documentation OpenPlotter), forums (OpenMarine, Arduino, CruisersForum, Seabreeze), articles. **Reddit** : aucune discussion utilisable trouvée pour ces six projets. **YouTube** : je peux repérer les vidéos citées dans les forums, mais pas les visionner ; leur contenu n'est donc pas résumé ici.

**Ce qui vient d'une analyse antérieure.** pypilot et Fenix : fiche du 2 novembre 2026 (code lu fichier par fichier), plus le comparatif collé par Mathieu le 6 novembre (nomenclature Fenix).

**Non lu.** Classes `Motor` et `IMU` de KastB, onglets `PID.ino`, `Keypadtiller.ino` et `WiFi.ino` de The Plot Device, bibliothèque `CalLib` de YAAAP, code complet de Jack Edwards, dates de dernier commit. Aucun code n'a été compilé ni exécuté.

**Licences : ce que dit GitHub, et la position retenue.** Seuls pypilot (GPLv3) et Fenix (GPL-3.0) ont une licence libre identifiée ; d'où le titre « à code public » plutôt que « open source ». Trois dépôts n'ont pas de licence formelle (The Plot Device, YAAAP, KastB) et celle de Jack Edwards n'est pas établie. Selon la documentation de GitHub, sans licence, le droit d'auteur s'applique par défaut : l'auteur garde tous ses droits, et les conditions de GitHub permettent seulement de **consulter et de forker** le dépôt sur la plateforme, ce qui n'est pas une licence. Personne n'a alors le droit de reproduire, distribuer ou créer des œuvres dérivées ; la page ne traite pas explicitement de l'usage privé. **Position de Mathieu (novembre 2026) :** il ne voit aucun problème à utiliser personnellement le contenu de ces dépôts. En pratique, le risque est faible pour un usage privé non diffusé, et les idées et algorithmes peuvent toujours être réécrits librement ; mais ce n'est pas une autorisation juridique. Avant toute **redistribution** (dépôt public, fork partagé, mélange avec du code GPL publié), il faudrait demander à l'auteur ou réécrire le passage, et vérifier aussi les licences des bibliothèques utilisées. Principe général, pas un avis juridique.

**Révision du 6 novembre 2026 (après audit).** Deux documents critiques fournis par Mathieu (un audit et une version révisée) ont été vérifiés point par point avant intégration : licence (documentation GitHub relue), vitesse angulaire (phrase OpenPlotter relue, erreur de calcul corrigée), pilote `basic` et programme moteur de pypilot, chaîne de courant de Fenix (descriptions du shield Cytron consultées), calculs de dimensionnement (refaits). Les corrections acceptées sont intégrées dans le texte ; la recommandation finale est reformulée en 7.4.

**Convention de cette note.** Les affirmations sans mention sont des **faits lus** dans une source citée. Les passages marqués *(inférence)* sont mes déductions. Les passages marqués *(proposition)* sont des idées pour le projet, rien n'est décidé.

---

## 1. pypilot (Sean D'Epagnier)

**Identité.** Dépôt `pypilot/pypilot`, Python, licence GPLv3. Projet à l'activité publique la plus visible des six (forum OpenMarine, où l'auteur répond encore en 2026, et plusieurs constructions indépendantes rapportées). L'activité publique ne mesure pas à elle seule la fiabilité d'une installation donnée.

### 1.1 Techniques utilisées

- **Calculateur Linux** : Raspberry Pi (ou Pi Zero W avec la distribution « tinypilot », système en lecture seule). Plusieurs serveurs Python communiquent entre eux : centrale inertielle, contrôleur moteur, clients (Web, écran LCD, plugin OpenCPN, Signal K).
- **Contrôleur moteur séparé** : un Arduino dédié, relié en série à 38 400 bauds par une liaison optoisolée. *Optoisolée* veut dire que le signal de données passe par la lumière (un optocoupleur) au lieu d'un fil électrique. Cela limite la propagation des parasites du moteur vers le calculateur, **à condition** que le reste du câblage et des alimentations conserve cette séparation ; cela ne remplace pas les protections de l'alimentation (fusible, protection contre l'inversion de polarité, filtrage).
- **Fusion de capteurs** : IMU 9 axes (ICM-20948 en général) lue par la bibliothèque RTIMU, avec un filtre de Kalman qui produit un **quaternion** (une façon compacte et sans ambiguïté de représenter l'orientation dans l'espace). Cap, gîte et vitesse de rotation en sont tirés.
- **Calibration avancée** : compas 2D puis 3D par ajustement d'ellipsoïde (on fait tourner le capteur, les mesures forment un ellipsoïde déformé par les masses métalliques, et on calcule la correction qui le ramène à une sphère).

### 1.2 Fonctionnement

Le calculateur compare le cap voulu au cap mesuré et calcule une **vitesse de moteur** (et non un angle de barre). Les gains portent des noms précis : P (erreur de cap), D (vitesse de rotation du bateau, c'est lui qui fait l'essentiel du travail), DD (accélération de rotation), PR (racine de l'erreur), FF (n'agit que lors d'un changement de consigne), et I, dont la déclaration et l'usage sont **en commentaire dans le pilote `basic` consulté** (ce constat vaut pour ce pilote et cette version, pas pour tous). Le contrôleur Arduino reçoit cette vitesse et pilote le pont en H, avec ses propres protections : limite de courant, rampes, embrayage, et **entrées optionnelles de fins de course et de retour de barre** prévues dans `motor.ino`. La protection réelle dépend de ce qui est câblé et configuré.

Modes : compas, GPS, vent apparent, vent réel, et navigation (suivi de route envoyé par un traceur via la trame APB).

### 1.3 Particularités

- **Le retour de position de barre est optionnel.** Comme la sortie est une vitesse, le système peut fonctionner sans capteur d'angle de barre.
- **Architecture en deux étages** : le « cerveau » (Pi) et la « force » (Arduino) sont séparés physiquement et électriquement.
- **Écosystème** : intégration native avec OpenCPN, Signal K et OpenPlotter.

### 1.4 Possibilités supplémentaires

- Mode vent et suivi de route avec OpenCPN déjà présents, ce qui correspond à deux souhaits du projet (NMEA/traceur, mode vent).
- Commande externe par son interface réseau (`ap.heading_command`, `servo.command`) : une tête de commande physique ou un joystick peuvent s'y brancher (un projet tiers, `pypilot_ray`, le fait avec un clavier).
- Pilote expérimental `learning` (modèle de prédiction appris) : un précédent de commande anticipative, non abouti.
- *(proposition)* Le contrôleur moteur Arduino de pypilot peut servir d'inspiration pour l'étage de puissance de n'importe quel autre projet (protections, rampes, embrayage).

### 1.5 Limitations

- Pile logicielle lourde : Linux, Python, dépendances. En 2026, des utilisateurs signalent des installations ratées sur OpenPlotter 4.
- Plus de consommation électrique qu'un microcontrôleur seul : le calculateur pypilot annonce environ 180 mA au repos et 280 mA au maximum sous 5 V, soit environ 0,9 à 1,4 W avant les pertes du convertisseur *(calcul)*. À comparer au budget énergétique du bateau, encore à établir.
- La gîte n'agit pas sur la commande dans le code lu (elle est calculée et publiée, mais pas utilisée par les pilotes).
- Interface : des commandes physiques existent déjà dans l'écosystème documenté (écran LCD et clavier du HAT, panneaux RF 7 et 8 touches, télécommandes RF et IR, boutons sur GPIO). Un boîtier de commande personnalisé à la barre peut néanmoins demander du travail.

### 1.6 Liste de matériel

D'après le manuel pypilot (copie hébergée sur Hisse et Oh), la documentation OpenPlotter et un message de l'auteur sur le forum (configuration minimale : Arduino Nano, ICM-20948, Raspberry Pi).

| Fonction | Composant | Précisions |
|---|---|---|
| Calculateur | Raspberry Pi Zero (tinypilot) **ou** Raspberry Pi 4/5 (OpenPlotter) | Le boîtier « pypilot computer » consomme environ 180 mA au repos et 280 mA au maximum, sous 5 V USB-C. Le pypilot HAT ne fonctionne qu'avec un Pi 4 (pas encore de Pi 5). |
| Centrale inertielle | ICM-20948 | Recommandée ; MPU-9250/9255 encore pris en charge mais abandonnés. |
| Contrôleur moteur | Arduino Nano + pont en H (programme `motor.ino`), ou contrôleur du commerce pypilot | Standard : 12 V, 7 A continus (15 A crête), fusible 10 A, sans sortie d'embrayage. Mid : 9–32 V, 15 A. High : 9–32 V, 30 A. Les deux derniers ont une sortie d'embrayage. |
| Liaison calculateur ↔ contrôleur | Câble 4 fils (3V3, TX, RX, GND), 38 400 bauds | Optoisolée côté contrôleur. |
| Retour de barre (optionnel) | Capteur angulaire à effet Hall MLX90316 (version pypilot) ou potentiomètre existant de 1 à 100 kΩ | Entrée « Rudder » du contrôleur. |
| Fins de course (optionnel) | Deux contacts vers la masse | Entrées dédiées du contrôleur. |
| Sonde de température moteur (optionnel) | NTC 10 kΩ | Entrée « Motor Temp ». |
| Vérin | Vérin de barre franche du commerce ou vérin linéaire générique | Documentation OpenPlotter : moteur qui va typiquement de −30° à +30° en 6 à 8 s, soit **7,5 à 10 °/s en moyenne** *(calcul)* ; c'est un repère, pas une prescription. (Le résumé du manuel obtenu par mon outil mentionnait aussi 15 à 20 °/s, ce qui est incohérent avec la durée ; je ne retiens que la phrase vérifiée.) `servo.max_current` de 4 à 7 A pour un vérin de barre franche. |
| Interface (au choix) | Écran LCD du calculateur, pypilot HAT (LCD, clavier, IR, RF, NMEA RS-422 isolé), télécommande RF 433 MHz, panneaux RF 7 ou 8 touches (12/24 V), télécommande IR, interface Web, plugin OpenCPN | La télécommande RF 433 MHz est fiable et rapide, mais n'est pas vraiment étanche (OpenPlotter). |
| Alimentation | Convertisseur 12 V → 5 V | À placer **loin du calculateur** pour ne pas perturber le compas. |
| Boîtiers | Presse-étoupes PG7, connecteurs à joint torique | Les boîtiers imprimés 3D proposés ne sont pas étanches. |

### 1.7 Retours terrain (forums, YouTube)

- **Vérins de barre franche utilisés par les membres d'OpenMarine.** Un membre indique qu'une course standard de 300 mm, fixée à environ 18 pouces (46 cm) du pivot, est la norme pour une barre franche ; son propre vérin fait 45 mm/s et 300 N. Un autre rapporte un vérin AliExpress de 300 mm à 170 mm/s qui fait tout le débattement en 1,5 s, sans chauffer, avec la remarque que le safran décroche au-delà d'environ 25°.
- **Moteur réversible ou non.** Dans un fil sur un prototype de barre franche, Sean D'Epagnier explique qu'un vérin qu'on peut faire reculer à la main hors tension sera aussi repoussé par les efforts de navigation, et consommera du courant rien que pour tenir la barre. C'est un critère de choix important pour ton vérin : un vérin à vis sans fin (non réversible) tient la barre sans courant, mais oblige à le décrocher pour barrer à la main.
- **Calibration du compas sur un pilote de barre franche.** Un utilisateur dont la centrale est dans le boîtier du vérin (qui pend quand il est décroché) a dû **verrouiller la calibration**, sinon l'auto-calibration se faussait chaque fois qu'il remettait le vérin en place.
- **Engagement sur la barre.** Un autre membre décrit la manœuvre : raccourcir le vérin, passer en « auto », puis le poser vite sur la barre. C'est une gêne d'usage qui plaide pour une commande « recentrer » et une tête de commande proche de la barre *(proposition)*.
- **Résultats rapportés.** Un Beneteau 343 équipé d'un tinypilot et d'un vérin intérieur Garmin Class A (Jefa LD100) donne au propriétaire l'impression d'être « sur des rails » au près, là où l'ancien pilote remontait au vent. Un article de Bateaux.com raconte le remplacement d'un ST7000 en panne par pypilot pendant un voyage.
- **YouTube.** Plusieurs vidéos sont citées dans les fils (essais de Sean avec un moteur d'essuie-glace, vidéo d'un pilote de barre franche Raymarine converti) ; je ne peux pas les visionner, seulement noter leur existence.

---

## 2. Fenix Autopilot (spascual90)

**Identité.** Dépôt `spascual90/Fenix`, C++/Arduino, GPL-3.0. Conçu explicitement pour la barre franche avec vérin linéaire. Mathieu y a ouvert l'issue #13 (bornes de `constrain` dans le feedforward vent).

### 2.1 Techniques utilisées

- **Microcontrôleur unique** : Arduino Mega R3 (ATmega2560), confirmé par la nomenclature officielle (voir 2.6).
- **IMU ICM-20948** avec filtre de **Mahony** (un filtre de fusion simple et léger, qui corrige la dérive du gyroscope à l'aide de l'accéléromètre et du magnétomètre).
- **Vérin 12 V à potentiomètre** intégré : la position de la tige est connue en permanence.
- **Modèles de navire issus de la littérature** : modèle de **Nomoto** (le bateau est représenté par deux nombres, un gain K et une constante de temps T, qui décrivent comment il tourne quand on bouge la barre) ; **modèle de référence de Fossen** (il génère une trajectoire de cap « douce » vers la consigne, au lieu d'un saut brutal) ; **observateur de vagues** (il sépare le mouvement lent du bateau des oscillations dues à la houle, pour ne pas corriger chaque vague).
- **Feedforward vent** : une estimation du couple que le vent exerce sur le bateau, ajoutée à la commande avant même que le cap ne dérive. *Feedforward* signifie « anticipation » : on agit sur la cause connue plutôt que d'attendre l'erreur.

### 2.2 Fonctionnement

Trois étages en cascade :
1. **Cap → angle de barre** : PID étendu + feedforward de Nomoto + feedforward vent, avec adaptation à la vitesse du bateau.
2. **Angle de barre → vitesse du vérin** : comparaison consigne/position lue au potentiomètre, zone d'arrêt avec hystérésis, rampe, temps d'arrêt à chaque inversion de sens.
3. **Puissance** : PWM et broche de sens vers le pilote moteur (shield Cytron 10 A recommandé, d'après le comparatif).

Modes : veille, compas (avec virement de 100°), navigation vers un waypoint, vent (source externe NMEA).

### 2.3 Particularités

- **Asservissement en position** : le régulateur vise un angle de barre, ce qui rend le comportement prévisible et permet des butées logicielles, à condition de **détecter aussi une défaillance du potentiomètre**.
- **Protection par le courant : logique présente, chaîne matérielle non démontrée.** Le code lu le 2 novembre contient une détection de blocage par le courant (`CurrentFeedback`). Mais la nomenclature ne liste aucun capteur de courant, et les descriptions du shield Cytron SHIELD-MD10 consultées ne mentionnent pas de sortie de mesure de courant. Il faut vérifier l'acquisition, l'activation, le seuil, le délai et l'arrêt effectif.
- **Identification en ligne** : le modèle de Nomoto s'ajuste quand la mer est calme.
- **NMEA riche** : réception APB, HDG/HDT, MWV/VWR, RMC/VTG ; émission RSA (angle de barre) et HDG ; trames propriétaires `$PEMC` pour régler le pilote à distance.
- Démarche guidée : nomenclature précise (vérin de référence 300 mm de course, environ 27 à 30 mm/s).

### 2.4 Possibilités supplémentaires

- Interfaçage OpenCPN déjà prévu (suivi de route via APB), donc compatible avec le souhait « traceur ». L'évitement de zones est une **décision d'intention** de Mathieu (à prévoir dès la conception, implantation dans un chantier ultérieur). *(proposition, non validée)* il pourrait être calculé côté traceur ou Signal K, Fenix ne recevant que la route corrigée ; mais recevoir une route ne prouve pas qu'un évitement fiable existe, et cette fonction reste hors de la première version.
- Le roulis est déjà calculé dans `ICM20948AHRS.cpp` : l'exposer permettrait d'ajouter un terme de gîte dans la somme P + I + D + FF + windFF *(piste de recherche, prématurée)*. Il faudra distinguer deux choses : corriger le cap mesuré quand le capteur est incliné, et compenser le moment de lacet dû à la gîte. Avant d'ajouter une commande, mesurer s'il existe une corrélation utile.
- Mode « actionneur virtuel » pour simuler sans matériel.

### 2.5 Limitations

- Documentation des algorithmes dispersée ; plusieurs paramètres de départ calés pour un bateau de 12 m (table de vent marquée « exemple ») : à réidentifier pour un Capri 22.
- Défauts relevés dans le code (bornes inversées de l'issue #13, fonctions sans `return`, zone morte automatique non branchée).
- Interface d'origine sur Android (Virtuino, dont la licence est distincte de celle de Fenix) : contraire au choix « pas de téléphone », il faudra une tête de commande à soi.
- Communauté réelle mais plus petite que celle de pypilot.

### 2.6 Liste de matériel

Nomenclature officielle (page « Build of materials » du site fenix-autopilot.com). Aucun prix n'y figure.

| # | Composant | Précisions de la nomenclature |
|---|---|---|
| 1 | Arduino Mega R3 (ATmega2560) | Clones bon marché jugés généralement fiables ; câble USB A/B. **Confirme le modèle Mega.** |
| 2 | Shield moteur Cytron 10 A | 7 à 30 V, 10 A continus, 15 A crête ; cavaliers sur D6 et D7 ; seul modèle testé. |
| 3 | Vérin linéaire 12 V à potentiomètre | Course 300 mm, rapport minimum 300 N / 27 mm/s ; **doit avoir 5 fils** (moteur + potentiomètre). |
| 4a | IMU ICM-20948 (SparkFun 9DoF, alternative Adafruit 4554) | Recommandée ; calibration avec l'application Python `Fenix_ICM_20948_Cal`. |
| 4b | ou IMU Pololu MinIMU-9 v5 (LSM6DS33 + LIS3MDL, alternative Adafruit 4485) | Calibration plus simple, depuis l'application. Une seule IMU à la fois. |
| 5 | Module Bluetooth HC-05 | Ne pas prendre le HC-06. |
| 6 | Convertisseur abaisseur LM2596 | Sortie réglée entre 8,5 et 12 V, **idéalement 9 V** : trop bas, l'Arduino bascule sur l'USB et redémarre. |
| 7 | Fenix Shield (circuit imprimé) | Connecteurs empilables, borniers à vis 2 et 3 pôles, buzzer 5 V, résistances 1 kΩ et 2,2 kΩ, câble Qwiic 150 mm pour l'IMU ; Gerbers sur GitHub (v1.1-beta.1). |
| — | Disjoncteur 10 A max sur le +12 V | Recommandé. |

À noter : la nomenclature déclare le **BNO055 obsolète** pour Fenix, ce qui rejoint les mauvaises expériences rapportées sur le forum YAAAP.

### 2.7 Retours terrain (forums, YouTube)

- **Peu de retours publics.** Le seul fil trouvé (Seabreeze, Australie, mai 2023) contient deux messages : la documentation est jugée claire ; un membre critique l'**interface sur téléphone**, avec beaucoup de petits boutons et de texte, difficile à lire sans lunettes ou en plein soleil, et imagine plutôt un écran e-paper avec des boutons physiques. Cette critique va dans le même sens que ton choix d'une tête de commande physique.
- Le guide utilisateur (GitBook) confirme la manœuvre d'engagement : stabiliser le bateau sur le cap, poser la tige sur l'ergot de barre (en l'allongeant ou la raccourcissant au besoin), puis passer de veille à auto.
- Un fork (`JoergSH/Fenix`) montre qu'au moins une autre personne a travaillé le code.
- La chaîne YouTube du projet (mentionnée dans ton comparatif) n'a pas été visionnée.

---

## 3. The Plot Device / Autopilot_ESP32_wifi (Jeff Burright)

**Identité.** Dépôt `jeff-burright/Autopilot_ESP32_wifi`, Arduino/C sur ESP32. Dérivé déclaré du pilote de Jack Edwards (crédité dans l'en-tête du programme). **Aucune licence formelle** : seule la mention « use at your own risk ». Environ 150 $ par version selon l'auteur.

### 3.1 Techniques utilisées

- **ESP32** (devkit) : un microcontrôleur avec Wi-Fi intégré, qui sert à la fois de calculateur et de serveur Web.
- **Compas** : centrale Pololu MinIMU-9, composée d'un **LSM303** (accéléromètre + magnétomètre) et d'un **L3G** (gyroscope) ; c'est l'ensemble qui fait 9 axes. Les fichiers `Compass.ino`, `DCM.ino`, `Vector.ino`, `I2C.ino` et `Output.ino` sont repris du programme AHRS de Pololu pour MinIMU-9 *(inférence forte : mêmes noms de fichiers et contenu d'`Output.ino` identique à une routine d'affichage AHRS ; le PDF de pièces confirme le couple LSM303 + L3G, voir 3.7)*. La fusion se fait donc par **DCM** (*Direction Cosine Matrix* : une matrice 3 × 3 qui représente l'orientation et que l'on corrige en continu avec l'accéléromètre et le magnétomètre). Le code évoque aussi un BNO055 comme option.
- **Compensation de gîte** : choix de la méthode d'inclinaison par la variable `LSMLib` ; avec `LSMLib = 0`, le capteur doit être monté face vers le bas.
- **Pont en H IBT-2** piloté en PWM (`ledcWrite`).
- **Serveur Web embarqué** : l'ESP32 crée son propre point d'accès Wi-Fi (adresse 192.168.4.1, sans Internet), avec mise à jour du programme « par les airs » (OTA, via ElegantOTA).
- **ESP-NOW** : un protocole radio d'Espressif, sans routeur, qui permet à deux ESP32 de s'échanger des messages directement ; utilisé ici pour une montre Lilygo T-Watch.

### 3.2 Fonctionnement (lu dans `PIDtiller.ino` et les déclarations)

1. **Erreur de cap** = cap à suivre − cap mesuré, ramenée entre −180° et +180°.
2. **Loi de commande** (mode par défaut `PID_MODE = 3`) : `PID_output = K_global × (K_cap × erreur − K_diff × vitesse_de_lacet + intégrale)`. Gains par défaut (jeu `PIDvals = 1`) : global 1, cap 0,6, différentiel 2, intégral 0. L'intégrale, quand on l'active, ne s'accumule qu'au-delà de la zone morte et est bornée à ±10° ; l'auteur la destine à compenser la barre « tenue » au près.
3. Le résultat est une **consigne d'angle de barre** (`rudder_command`).
4. **Asservissement de la barre** : erreur de barre = consigne − position lue au potentiomètre. Si elle dépasse la zone morte (2°), le moteur tourne dans le bon sens à une vitesse proportionnelle à l'erreur (pleine vitesse à 30° d'écart), avec un plancher (`motorspeedMIN = 75` sur 255). Sous la zone morte, arrêt.
5. **Butée** : si la barre dépasse `Maximum_Rudder` (40°), arrêt — seulement avec le potentiomètre.
6. **Sans potentiomètre** (`RUDDER_MODE = 1`), la position est forcée à 0 : le moteur tourne alors tant que la consigne sort de la zone morte. C'est une boucle ouverte *(inférence : le comportement devient proche d'un pilote « vitesse », sans connaissance de la position réelle)*.

Boucle de fusion visée à 50 Hz (`G_Dt = 0,02 s`).

### 3.3 Particularités

- **Multi-interface** sans application : navigateur Web, bouton physique, écran LCD 16 × 2, télécommande infrarouge, montre ESP-NOW.
- **Deux installations réelles de l'auteur** : barre franche sur Northwest 21 (vidéo sous voile) et barre à roue sur Islander 36 (pour celle-ci, il a remplacé une poulie tendue par une boîte moteur sur charnière).
- Code récemment maintenu : passage à ESP32 Arduino Core 3 en janvier 2026, interface 1.3 en février 2026.
- Une variable `DODGE_MODE` (esquive) est déclarée, sans logique visible dans l'extrait lu.

### 3.4 Possibilités supplémentaires

- *(proposition)* L'ESP32 a du Wi-Fi : il pourrait recevoir du NMEA par UDP depuis OpenCPN ou Signal K, ce qui ouvrirait le suivi de route et le mode vent. **Rien de tel n'existe dans le code lu** : c'est à développer.
- *(proposition)* L'IMU LSM303 est ancienne ; le passage à un ICM-20948 ou à un capteur NXP demanderait de remplacer la partie DCM.
- La tête de commande physique (bouton, écran) est déjà prévue, ce qui rejoint le choix « pas de téléphone ».
- Le mode `PID_MODE = 1` (la commande s'ajoute à elle-même à chaque cycle) montre une variante où la sortie se comporte comme une vitesse *(inférence)*.

### 3.5 Limitations

- **Licence absente** : sans conséquence pour un usage personnel ; à clarifier avec l'auteur seulement si du code copié devait être redistribué (voir section 0).
- **Maintien de cap seulement** (ni GPS, ni vent, ni NMEA dans la version lue).
- Compilation fragile : trois modifications manuelles de bibliothèques nécessaires avec Core 3 (dont le remplacement des `%` par `$` dans ESPAsyncWebServer).
- Pas de mesure de courant visible dans les fichiers lus : la protection en fin de course repose sur les fins de course internes du vérin conseillé ou sur le capteur de barre (voir 3.7).
- Réglages faits dans l'interface Web perdus à chaque mise sous tension (voir 3.7).
- Wi-Fi exposé : la sécurité dépend du mot de passe choisi dans le code.
- Aucune construction indépendante confirmée.

### 3.6 Liste de matériel

D'après le PDF `Autopilot parts list_ESP32.pdf` du dossier `documentation` (2023, notes jusqu'en 2026). Prix de l'auteur en dollars américains, liens eBay ; prix historiques, hors boîtier, protections et temps d'intégration, donc pas un budget actuel.

| Composant | Prix | Précisions |
|---|---|---|
| ESP32 devkit | 9 $ | |
| Convertisseur 12 V → 5 V | 1 $ | Sortie vers l'ESP32 par un câble micro-USB coupé. |
| IMU 9 axes **LSM303 + L3G** | 15 $ | Monté soit à distance (câble USB de moins de 2 m, dans une boîte de Tic Tac au centre du bateau), soit collé sous l'ESP32. |
| Pont en H BTS7960 (IBT-2) | 13 $ | + pastille thermique optionnelle (3 $). À éloigner du compas. |
| **Vérin linéaire (version barre franche)** | 86 $ | **300 mm de course, 300 N, 45 mm/s**, avec fins de course internes. |
| Fixation de barre | — | Bande d'aluminium de 1,5 po, boulon 1/4 po et deux étriers en U ; ancrage côté banquette : boulon 1/4 po avec bague caoutchouc dans un bloc de bois collé sous le coffre, écrou noyé dans l'époxy. |
| Moteur d'essuie-glace (version roue) | 35 $ | + kit de transmission de moto à courroie 1:4 (45 $), courroie HTD 5 mm (15 $), boîte à charnière en bois ; essais d'une boîte imprimée en 3D en 2026. |
| Capteur d'angle de barre (optionnel) | 18 $ | Utile pour les fins de course si le vérin n'en a pas ; demande une résistance de 1 kΩ sur un troisième fil. |
| Écran LCD 2 lignes I2C (optionnel) | 7 $ | |
| Récepteur et télécommande IR (optionnel) | 5 $ | Les codes varient selon les télécommandes. |
| Bouton (optionnel) | 0,50 $ | |
| Fils Dupont, colliers, fil 14/16 AWG | 6 $ + 6 $ | |
| **Total** | **164 $** (roue, toutes options) ; **37 $** (minimum : ESP32, IBT-2, IMU) | Hors boîtier, bois et quincaillerie. |

**Câblage relevé** : IMU et LCD sur SDA 21 / SCL 22 ; IBT-2 LPWM 32, RPWM 33, L-EN et R-EN au +5 V ; capteur de barre sur la broche 34 ; bouton sur la broche 5 ; récepteur IR sur la broche 27.

### 3.7 Retours terrain et informations nouvelles

- **Correction de la section 3.1** : le PDF confirme le capteur **LSM303 + L3G** (bibliothèques `LSM303.h` et `L3G.h`), ce qui appuie fortement la filiation avec le programme AHRS Pololu MinIMU-9.
- **Fins de course** : le vérin conseillé a des fins de course internes ; le capteur de barre n'est « recommandé » que pour un moteur d'essuie-glace ou un vérin sans fins de course. Cela répond en partie à la question de la protection en butée (section 3.5).
- **Réglages non mémorisés** : d'après le PDF, les gains PID, la zone morte et la déclinaison réglés dans l'interface Web **se perdent à chaque mise sous tension** ; pour les garder, il faut modifier le code et le téléverser de nouveau.
- **Le plus difficile** selon l'auteur : la liaison mécanique moteur-barre (« tinker engineering »), surtout pour la version à roue.
- **Réseau Wi-Fi** : le mot de passe par défaut est vide.
- **Forums** : le fil CruisersForum ne contient aucun retour d'autres constructeurs. Je n'ai pas pu retrouver la discussion Reddit citée dans ton comparatif. La courte vidéo YouTube de la version barre franche en navigation est citée dans le fil, mais je ne peux pas la visionner.

---

## 4. YAAAP — Yet Another Arduino AutoPilot (FilBip, Philippe Leclercq)

**Identité.** Dépôt `FilBip/yaaap`, 15 commits, 12 étoiles. Copyright 2016 Philippe Leclercq, **aucune licence explicite**. Fil francophone actif sur le forum Arduino.

### 4.1 Techniques utilisées

- **Arduino Pro Mini** (ATmega328P) : l'auteur indique que le code tient « de justesse » dans les 32 ko de mémoire.
- **IMU MPU9250** avec la bibliothèque **RTIMUlib** (modifiée pour sauvegarder le biais du gyroscope). Le poids du magnétomètre dans la fusion est volontairement très faible (`setSlerpPower(0.001)`) : le cap repose surtout sur le gyroscope, le compas ne le corrige que lentement. *SLERP* est une interpolation entre deux orientations ; une puissance faible signifie « faire peu confiance à la nouvelle mesure du compas à chaque pas ».
- **Pilote moteur TB6612FNG** (deux canaux en parallèle, environ 2 A continus) et **capteur de courant ACS712** (capteur à effet Hall qui mesure le courant sans résistance de mesure en série).
- **Commande par impulsions** au lieu du PWM : l'auteur rapporte de mauvais résultats en PWM avec ce petit moteur ancien.
- Visualisation sur PC via **Processing** (dossier `YaaapProcessing`).

### 4.2 Fonctionnement (lu dans `yaaap.ino`)

1. Toutes les 200 ms, le cap moyenné est comparé au cap visé.
2. Si l'erreur est sous la moitié de la zone morte (zone morte 4° par défaut, donc ±2°), rien ne bouge.
3. Sinon, commande **PD** : `cmd = Kp × erreur + Kd × variation de l'erreur`, avec Kp = 3 et Kd = 30 par défaut (remplacés par les valeurs en EEPROM). La dérivée est calculée sur l'erreur de cap, pas sur le gyroscope. Saturation à ±100.
4. **Pas de terme intégral**, et c'est voulu : l'auteur explique que la position de la barre, qui s'accumule à chaque impulsion, joue déjà ce rôle. C'est son raisonnement ; l'intégration mécanique ne suffit pas à elle seule à garantir l'absence d'erreur permanente du système complet.
5. La commande devient une **durée d'impulsion** de 20 à 200 ms ; à 100, le moteur tourne en continu. Le signe donne le sens.
6. **Surcharge** : au-delà de 2 400 mA, la commande dans le même sens est bloquée 5 s ; le sens inverse reste autorisé immédiatement. C'est ainsi que les fins de course sont détectées, **sans capteur de position**.

Virement : 100° (appui long sur deux boutons). Calibration en traçant un 8 avec l'appareil.

### 4.3 Particularités

- **Récupération d'un vérin commercial** (Autohelm 2000) : seule l'électronique est remplacée.
- **Interface minimale** : trois boutons et un LCD, aucun téléphone ni ordinateur. Logique de boutons complète (clic, appui long, combinaisons).
- Coût matériel annoncé d'environ 30 €.
- **Le fil du forum est une mine d'expérience** sur les capteurs : plusieurs participants jugent le BNO055 trop instable sur un voilier à cause de son auto-calibration ; un autre passe à un capteur NXP avec filtre de Madgwick. Le cap faussé par la gîte revient souvent.

### 4.4 Possibilités supplémentaires

- *(hypothèse de réglage, à tester)* Le raisonnement « pas de I parce que le moteur intègre déjà » revient chez pypilot et SimplePilot. C'est une piste de départ quand on commande en vitesse, pas une règle : seuls des essais diront si une erreur permanente subsiste (par exemple au près, barre tenue).
- La détection de fin de course par le courant est une solution de secours intéressante, même avec un vérin à potentiomètre (double protection) *(proposition)*.
- Portage sur ESP32 évoqué par l'auteur (pour échantillonner plus vite), mais **non réalisé** ; un autre participant objecte que la constante de temps d'un bateau (plusieurs secondes) ne justifie pas des fréquences très élevées.

### 4.5 Limitations

- Forte contrainte mémoire signalée par l'auteur (code tenant « de justesse » dans 32 ko) : ajouter NMEA, GPS ou vent paraît difficile sur cette carte, mais la marge réelle est à chiffrer par une compilation avant de conclure.
- Composants anciens (MPU9250 en fin de vie, RTIMUlib non maintenue).
- Sans capteur de position, pas de limite d'angle programmable, seulement les butées mécaniques du vérin.
- Petit écart entre le README (impulsions de 10 ms minimum) et le code lu (20 ms minimum) : le code fait foi pour la version lue.
- Pas de licence : aucun obstacle pour un usage personnel ; redistribution à clarifier (voir section 0).
- Une seule installation documentée (celle de l'auteur).

### 4.6 Liste de matériel

D'après le README, le code et le fil du forum Arduino (coût matériel annoncé d'environ 30 €, hors vérin).

| Composant | Précisions |
|---|---|
| Arduino Pro Mini (ATmega328P) | Mémoire presque pleine. |
| IMU MPU9250 | Des clones (module GY-91) répondent avec l'identifiant 0x73 au lieu de 0x71 : il faut modifier `MPU9250_ID` dans RTIMULib (erreur −6 sinon). |
| Pilote moteur TB6612FNG, deux canaux en parallèle | Environ 2 A continus, 6 A crête. L'auteur conseille un IBT-2 (BTN7970B) pour un moteur plus fort ; un participant confirme qu'un IBT-2 ne chauffe pas. |
| Capteur de courant ACS712 (version 5 A, 185 mV/A) | Seuil de surcharge à 2 400 mA. |
| Écran LCD I2C 16 × 2 | |
| Trois boutons | Bibliothèque OneButton. |
| Vérin récupéré | Autohelm 2000 (moteur Omron 2332, 12 V, environ 1,6 A) ; l'auteur cite aussi un vérin ST2000, et un participant teste un ST4000 (environ 2,5 A au blocage). |

### 4.7 Retours terrain (forum Arduino)

- **Conseil de méthode de l'auteur** : tester d'abord l'Arduino et la centrale seuls, avec un petit programme qui écrit chaque étape sur le port série, avant de tout assembler.
- **Réglage** : l'auteur dit qu'un PID classique a donné de moins bons résultats que son approche empirique PD.
- **Le GPS n'aide pas contre les vagues** : selon l'auteur, il sert à fournir la consigne de cap depuis le logiciel de navigation, pas à corriger plus vite.
- **Pour un nouveau projet, l'auteur lui-même conseille pypilot** sur Raspberry Pi Zero.
- **Pièges rencontrés par les constructeurs** : appel de la calibration du compas commenté dans `setupMenu.ino` ; boutons inversés selon le câblage ; un constructeur trouve que le vérin suit mal les changements de cap.
- **Capteurs** : un participant utilise un CMPS11 (compas avec fusion intégrée) qui ne dériverait pas à la gîte.
- Aucune vidéo YouTube de YAAAP trouvée.

---

## 5. Jack Edwards Autopilot

**Identité.** Projet historique (vers 2012–2014), construit pour un Nordic 40 de 1983 (« Wile E. Coyote »). Une archive existe sur GitHub (`CoyoteWaits/Jack_Edwards_Autopilot`, 2 commits, un dossier `Autopilot_JNE_RF24_bno055_J11A`), sans licence visible. La documentation d'origine était distribuée par Dropbox et par courriel.

### 5.1 Techniques utilisées

- **Deux Arduino Mega 2560** reliés en série avec la bibliothèque **EasyTransfer** (qui envoie des structures de données entières entre deux Arduino) : l'un ne fait que traiter le GPS, l'autre gère tout le reste.
- **Compas** : IMU Pololu 9 axes dans la version de 2013 ; le nom du dossier GitHub et la reproduction Firgelli indiquent un **BNO055** dans la version J11 *(le passage au BNO055 est une inférence appuyée par deux indices)*. Le nom du dossier suggère aussi une radio nRF24 *(inférence)*.
- **Retour de barre** : capteur à effet Hall Honeywell, 0,5 à 4,5 V pour environ ±45°.
- **Actionneur** : pompe hydraulique Wagner existante (environ 11 A), avec une électrovanne qui libère la barre manuelle quand elle est ouverte.
- **Puissance** : contrôleur série **Pololu Qik 2s12v10**.
- **Affichage** : LCD 20 × 4.

### 5.2 Fonctionnement

Quatre modes par boutons : cap compas, guidage GPS vers un waypoint, virement réglable, vent (inachevé en 2013, via un convertisseur SeaTalk vers NMEA). En mode GPS, le système calcule le cap origine-destination (BOD) et l'**écart de route** (XTE, *cross track error* : la distance latérale entre le bateau et la ligne idéale), puis corrige le cap à suivre pour revenir sur la ligne. Un mode « bouton de barre » (*knob steering*) permet de barrer au potentiomètre. Un gain et une limitation de vitesse de réponse servent à ménager la pompe.

### 5.3 Particularités

- **Plus de 400 milles parcourus** à l'été 2013 en modes cap et GPS, avec un trajet complexe d'une quarantaine de milles suivi selon un blogue de 2017.
- **Ancêtre** de The Plot Device (filiation déclarée par Jeff Burright) et d'autres projets.
- **Une reproduction indépendante documentée** : l'article Firgelli décrit un montage avec Arduino Mega, BNO055, Pololu Qik et un vérin linéaire de 9 pouces, mais **sur la direction d'un moteur hors-bord**, pas sur une barre franche de voilier. Modes utilisés : cap, potentiomètre, joystick pour l'accostage. Zone morte réglée à 2°.

### 5.4 Possibilités supplémentaires

- Le suivi GPS avec correction d'XTE est une référence simple pour comprendre le mode « route » avant de passer par OpenCPN.
- Le principe « un processeur dédié par tâche lente » (GPS à part) préfigure l'architecture en deux étages de pypilot *(inférence)*.
- La reproduction Firgelli donne des retours concrets sur la mécanique d'un vérin linéaire : longueur de bielle critique pour les fins de course, grippages, **bruit électrique du pilote moteur qui perturbe le compas** (câbles séparés et blindés, condensateurs).

### 5.5 Limitations

- Problèmes signalés par l'auteur en 2013 : virage déclenché seulement à l'arrivée au waypoint (dépassement sur la branche suivante), gels du système après une route, GPS à 1 Hz trop lent, vent non terminé.
- Versions dispersées, documentation hors GitHub, bibliothèques anciennes.
- Conçu pour une **pompe hydraulique** : l'adaptation à un vérin de barre franche est à faire (même si la reproduction Firgelli montre que c'est possible avec un vérin).
- Licence non établie : le texte historique destine le logiciel à ceux qui veulent construire leur pilote, ce qui couvre l'usage personnel ; redistribution à clarifier (voir section 0).

### 5.6 Liste de matériel

**Version d'origine (2013, reportage du blog)**

| Composant | Précisions |
|---|---|
| 2 × Arduino Mega 2560 | Un pour le GPS, un pour le reste ; liaison série EasyTransfer. |
| IMU Pololu 9 axes (MinIMU-9) | À environ 1 m de tout métal ferreux ; calibration initiale. Le dossier GitHub J11 et la reproduction Firgelli indiquent ensuite un BNO055. |
| GPS NMEA (trame RMC) | 1 Hz, jugé trop lent ; 10 Hz envisagé. |
| Capteur d'angle à effet Hall Honeywell | 0,5 à 4,5 V pour environ ±45°. |
| Contrôleur Pololu Qik 2s12v10 | Contrôleur série de moteur à courant continu. |
| Pompe hydraulique Wagner PV100-12-TR (environ 11 A) + électrovanne | Matériel existant du bateau ; l'électrovanne libère la barre manuelle. |
| Écran LCD Adafruit 20 × 4 | Gradation PWM et réglage du contraste. |
| Boutons de mode + pavé de réglage | Quatre boutons de mode. |
| Convertisseur SeaTalk → NMEA | Pour le vent (inachevé en 2013). |

**Reproduction Firgelli (moteur hors-bord, prix indicatifs de l'article)** : vérin linéaire 12 V de 9 pouces à fins de course internes (150 à 200 $), Arduino Mega (35 à 50 $), BNO055 (35 à 45 $), Pololu Qik (40 à 50 $), clavier à membrane, potentiomètre, interrupteur de mode et joystick (15 à 25 $), acier et quincaillerie (20 à 30 $), rotules à dégagement rapide (25 à 40 $), câblage marin (15 à 25 $). Total annoncé : environ 300 à 350 $ (prix de l'article, non comparables à un budget actuel).

### 5.7 Retours terrain (forums, YouTube)

- **Vidéo de l'auteur** sous voile avec visite du matériel et des modes, citée sur le forum Arduino (fil « Auto Pilot for Tiny Yacht ») ; non visionnée.
- Sur le même fil, un propriétaire de C&C 33 se dit inspiré pour construire le sien et pose des questions sur la centrale Pololu ; l'auteur s'y offre à aider ceux qui veulent adapter le projet.
- Un blogue de 2017 rapporte qu'un trajet complexe d'une quarantaine de milles a été suivi ; l'intégration du vent et du retour de barre y est annoncée comme étape suivante.
- La reproduction Firgelli ajoute des conseils pratiques : s'entraîner à repasser en barre manuelle au quai, faire les premiers essais par temps calme, séparer et blinder les câbles du moteur pour protéger le compas.

---

## 6. KastB / boat_autopilot

**Identité.** Dépôt `KastB/boat_autopilot`, 131 commits, 23 étoiles, voilier de 12 m, utilisé plusieurs années selon l'auteur. **Aucune licence visible.**

### 6.1 Techniques utilisées

- **Arduino Mega** comme calculateur et concentrateur de capteurs ; **Raspberry Pi** comme serveur intermédiaire (*proxy* : il reçoit les données de l'Arduino et les redistribue à plusieurs clients en même temps).
- **Ordonnanceur à minuteries** : chaque module (IMU, moteur, SeaTalk, GPS, PID, interface, capteurs d'alimentation) hérite d'une classe « timer » et tourne à sa propre période. Dans `autopilot.ino`, le PID est instancié avec 500 et l'IMU avec 10 (unités non précisées, probablement des millisecondes *(inférence)*).
- **IMU MPU9150** (MPU6050 + magnétomètre AK8975), avec autocalibration.
- **Lecture SeaTalk 1** (bus Raymarine ancien, 4 800 bauds) : vent, vitesse, profondeur, température. En lecture seule.
- **Encodeur incrémental** fabriqué avec les barrières lumineuses d'une vieille souris à boule, lu en signal brut, plus trois boutons de référence (fins de course et neutre).
- **Motorisation de porte de garage** 24 V alimentée en 12 V, pilotée par un Olimex BB-VNH3SP30, PWM à environ 10 kHz.
- **Journalisation CSV** pour tracer des courbes de réglage.

### 6.2 Fonctionnement (lu dans `PID.cpp`)

1. **Erreur** : en mode compas, consigne − cap ; en mode vent, angle de vent apparent − consigne.
2. **Gain P variable** : 2 quand l'erreur est sous 5° (pour bouger le moins possible la barre quand le cap est tenu), 4 jusqu'à 10°, puis croissant avec l'erreur. Au près serré (consigne sous 45° du vent), P est majoré de 10 %.
3. **Terme D quadratique** : `D × vitesse × |vitesse|`. Il amortit peu les petites rotations et beaucoup les rotations rapides.
4. **Terme I** gelé pendant 7 s après chaque changement de consigne ou virement, et suspendu quand le bateau tourne vite ou que le moteur est bloqué.
5. La somme passe dans un **filtre passe-bas** du premier ordre (1 Hz par défaut), puis devient une **position de barre visée** envoyée au moteur (`gotoPos`).
6. **Virement** : en mode vent, la consigne change simplement de signe (même angle de l'autre bord) ; en mode compas, la consigne est décalée de deux fois l'angle du vent apparent filtré.

Gains par défaut du constructeur : P = 4, P2 = 2, I = 0,2, D = 3. L'en-tête mentionne d'autres valeurs (Kp = 27, Ki = 1,67) : incohérence non résolue.

### 6.3 Particularités

- **Mécanique de récupération** très originale : motorisation de porte de garage, glissières pour convertir le mouvement, **déverrouillage d'urgence de la porte réutilisé comme embrayage** (découplage mécanique complet en cas de panne).
- **Le seul des six à lire directement un bus SeaTalk 1** (vent, vitesse, profondeur) dans le calcul. pypilot et Fenix reçoivent aussi des données d'instruments, mais par NMEA ou Signal K.
- Le **virement en mode compas calculé à partir du vent** est une astuce élégante.
- Plusieurs clients simultanés (Bluetooth/Android, télécommande 433 MHz, port série).

### 6.4 Possibilités supplémentaires

- La loi de commande (P réduit près du cap, D quadratique, I gelé après une manœuvre, filtre de sortie) est un **catalogue d'idées pour limiter les mouvements de barre**, donc la consommation et l'usure *(pistes à expérimenter une par une)*. Elles ne se copient pas telles quelles : unités, fréquences et nature de la sortie diffèrent ; un filtre ajoute du retard ; une dérivée quadratique peut amplifier le bruit. Chaque modification serait à comparer à un réglage de référence.
- Le gel de l'intégrale après virement peut limiter une cause classique de dépassement (l'intégrale accumulée pendant la manœuvre) ; il ne remplace pas la gestion de la saturation, de la consigne et de la vitesse de rotation.
- La journalisation CSV est un bon modèle pour les futurs essais de réglage *(proposition)*.

### 6.5 Limitations

- Réglages « au moins pour notre configuration » : calé pour un 12 m.
- Problèmes connus signalés dans le code : sauts en lacet attribués au PID, valeurs NaN de l'IMU qui persistent.
- Pas de saturation de la commande dans `PID.cpp` (elle serait dans la classe `Motor`, non lue).
- Encodeur **relatif** : la position absolue dépend des boutons de référence.
- SeaTalk 1 seulement, en lecture ; application Android annoncée mais code non visible.
- Transmission mécanique à concevoir entièrement pour une barre franche.
- Pas de licence : aucun obstacle pour un usage personnel ; redistribution à clarifier (voir section 0).

### 6.6 Liste de matériel

D'après le README et `autopilot.ino` (aucun prix publié).

| Fonction | Composant | Précisions |
|---|---|---|
| Calculateur | Arduino Mega | PWM à environ 10 kHz (Timer4) ; ports série : PC 115 200, GPS 9 600, SeaTalk 4 800 bauds. |
| Serveur intermédiaire | Raspberry Pi | Module `nmea_proxy`, scripts de démarrage, VNC. |
| IMU | MPU9150 (MPU6050 + AK8975) | Autocalibration. |
| Pilote moteur | Olimex BB-VNH3SP30 | |
| Actionneur | Motorisation de porte de garage 24 V alimentée en 12 V | Glissières pour convertir le mouvement ; déverrouillage d'urgence utilisé comme embrayage. |
| Position de barre | Encodeur incrémental fait avec les barrières lumineuses d'une vieille souris + 3 boutons de référence | Fins de course, neutre et point de ralentissement. |
| Instruments | Interface SeaTalk 1 (lecture seule, circuit simple) | Vent, vitesse, profondeur, température. |
| GPS | Module NMEA | |
| Commandes | Bluetooth (application Android), télécommande 433 MHz 4 boutons, port série | Infrarouge et clavier prévus mais désactivés dans le code. |
| Mesures d'alimentation | Module `PowerSensors` | Deux entrées analogiques. |

### 6.7 Retours terrain

- Aucun fil de forum, aucune discussion Reddit et aucune vidéo YouTube trouvés sur ce projet. Le seul témoignage reste celui du README (plusieurs années d'utilisation sur un 12 m).

---

## 7. Synthèse comparative

### 7.1 Philosophies de commande

| Projet | Sortie du régulateur | Retour de barre | Terme intégral | Protection fin de course |
|---|---|---|---|---|
| pypilot | Vitesse moteur | Optionnel | En commentaire dans `basic` | Courant + fins de course et retour de barre optionnels (`motor.ino`) |
| Fenix | Angle de barre | Obligatoire (potentiomètre) | Oui, avec anti-windup | Butées logicielles ; courant dans le code, chaîne matérielle à vérifier |
| Plot Device | Angle de barre (avec pot) ; quasi vitesse (sans) | Optionnel | Désactivé par défaut, borné à ±10° | Angle max 40° (avec pot) |
| YAAAP | Durée d'impulsion | Aucun | Non (volontaire) | Courant 2,4 A, blocage 5 s |
| Jack Edwards | Commande de pompe (détail non lu) | Capteur Hall | Non établi | Non établi |
| KastB | Position de barre filtrée | Encodeur relatif + références | Oui, gelé 7 s après manœuvre | Boutons de référence |

### 7.2 Adéquation avec la cible du projet

| Critère | pypilot | Fenix | Plot Device | YAAAP | Jack Edwards | KastB |
|---|---|---|---|---|---|---|
| Licence libre explicite | Oui (GPLv3) | Oui (GPL-3.0) | Non | Non | Non établie | Non |
| Usage personnel du code | Oui | Oui | Oui | Oui | Oui | Oui |
| Barre franche + vérin linéaire | Oui (vérins du commerce) | Oui (conçu pour) | Oui (Northwest 21) | Oui (vérin Autohelm) | Indirect (reproduction hors-bord) | À concevoir |
| NMEA / OpenCPN | Oui | Oui | Non | Non | GPS seulement | SeaTalk + GPS |
| Mode vent | Oui | Oui | Non | Non | Inachevé | Oui |
| Sans téléphone (critère non éliminatoire depuis le 6 nov.) | Oui (claviers, panneaux, LCD documentés) | À développer (calibration comprise, à vérifier) | Oui, partiel (réglages par navigateur) | Oui | Oui | Possible |
| Utilisateurs indépendants | Nombreux | Quelques-uns | Non confirmé | Partiels | Une reproduction | Non confirmé |

### 7.3 Vérins rencontrés (utile pour le chantier actionneur)

| Source | Course | Force | Vitesse | Remarque |
|---|---|---|---|---|
| Nomenclature Fenix | 300 mm | ≥ 300 N | ≥ 27 mm/s | Potentiomètre obligatoire (5 fils). |
| PDF de The Plot Device | 300 mm | 300 N | 45 mm/s | Fins de course internes ; environ 86 $. |
| Membre OpenMarine (pypilot) | ~300 mm | 300 N | 45 mm/s | Fixé à environ 46 cm du pivot de barre. |
| Membre OpenMarine (pypilot) | 300 mm | 50 N annoncés (valeur douteuse pour ce débit) | 170 mm/s | Débattement complet en 1,5 s, moteur froid. |
| Reproduction Firgelli (Jack Edwards) | 9 po (~23 cm) | 200 à 400 lb annoncés | non précisée | Hors-bord, fins de course internes, 5 à 10 A en mouvement. |
| Repère OpenPlotter / manuel pypilot | — | — | 6 à 8 s de −30° à +30° (7,5 à 10 °/s) | Courant max conseillé 4 à 7 A pour un vérin de barre franche. |

*(inférence)* Deux projets indépendants convergent vers le même gabarit (300 mm, 300 N), avec une vitesse de 27 à 45 mm/s. Ce sont des références de montage, pas une validation pour le Capri 22 (voir 7.5). La vitesse angulaire réelle dépend de la distance de fixation sur ta barre, encore inconnue. La question « vérin réversible ou non » soulevée sur OpenMarine (1.7) est à ajouter aux critères de choix.

### 7.4 Lecture d'ensemble *(propositions, rien de décidé)*

**Deux finalistes : pypilot et Fenix.** Les deux critiques reçues le 6 novembre (audit et version révisée) ont fait évoluer cette lecture. Le classement ci-dessous est un jugement d'adéquation, pas un résultat d'essai comparatif.

- **pypilot** est le candidat le plus direct si la priorité est d'obtenir les fonctions souhaitées (compas, vent, route, OpenCPN) avec des **commandes physiques déjà documentées**. Mon ancienne remarque « tête physique à développer » était déséquilibrée. Points à vérifier : démarrage, consommation totale, dépendances logicielles, comportement en cas de coupure ou de perte de liaison.
- **Fenix** est le candidat naturel si la priorité est de **maîtriser et développer** un ensemble sur microcontrôleur, en acceptant de construire sa propre tête de commande. Points à vérifier : modes et trames de la version retenue, anomalies relevées (issue #13 et autres), chaîne réelle de mesure du courant, gestion des pannes de capteur, utilisation complète sans Android (calibration comprise). Une loi de commande plus élaborée n'est pas, à elle seule, la preuve d'une meilleure tenue de cap.
- **État des décisions (mis à jour le 6 novembre 2026)** : le vérin linéaire reste la pièce commune retenue. **Fenix n'est plus le choix arrêté** : la plateforme est de nouveau ouverte. Mathieu va d'abord déterminer l'étendue des capacités du pilote (fonctions de navigation et aides) avant de choisir la puissance du contrôleur. Avec l'option d'un mobile ou d'une tablette dédiés, l'interface Android de Fenix (Virtuino) et les interfaces Web de pypilot et de The Plot Device redeviennent recevables.
- **Les quatre autres projets** restent des références ciblées : The Plot Device pour une tête de commande sur ESP32 ; YAAAP pour la simplicité et la rénovation d'un ancien pilote ; KastB pour la journalisation et la réduction des mouvements de barre ; Jack Edwards et sa reproduction Firgelli pour les retours de terrain. Leur intérêt ne justifie pas de reprendre leur architecture complète ni leurs composants historiques.
- Le choix définitif devrait suivre le dimensionnement mécanique, la vérification des protections et un essai d'interface.

### 7.5 Dimensionner le vérin avant de l'acheter *(calcul simplifié, hypothèses explicites)*

Les valeurs 300 mm / 300 N / 27 à 45 mm/s sont des **références de montage**, pas une validation pour le Capri 22. Il faut d'abord connaître la distance entre l'axe de la mèche et le point de fixation sur la barre, la position de l'ancrage fixe, les angles utiles, les efforts réels et la vitesse sous charge. Les cotes de montage de la ST1000+ restent une référence géométrique utile pour ce relevé.

**Exemple chiffré** (calculs vérifiés ; la distance de 460 mm est celle d'un membre du forum OpenMarine, pas celle de ton bateau) :
- **Course.** Pour un vérin à peu près perpendiculaire à la barre, la course entre deux angles symétriques vaut environ `s ≈ 2 × r × sin(θ)`. Avec `r = 460 mm`, une course de 300 mm donne `sin(θ) ≈ 0,33`, soit **environ ±19°**. Atteindre ±30° demanderait environ 460 mm de course dans cette approximation. Autrement dit, à cette distance, un vérin de 300 mm ne couvre pas un débattement de ±30° ; il faudrait se fixer plus près de la mèche (au prix de plus d'effort) ou accepter un débattement plus faible.
- **Couple.** `C = F × r × sin(α)`, où α est l'angle entre la barre et l'axe de poussée. 300 N à 0,46 m donnent au maximum **138 N·m** quand la poussée est perpendiculaire ; moins dès que l'angle s'écarte. Cette valeur ne dit pas si l'effort demandé par le safran est couvert : il faut le mesurer.
- **Temps.** À vitesse nominale, 300 mm prennent environ **11,1 s à 27 mm/s** et **6,7 s à 45 mm/s** ; la vitesse sous charge peut être plus faible. Le repère « −30° à +30° en 6 à 8 s » correspond à 7,5 à 10 °/s en moyenne.
- La géométrie exacte des deux articulations devra remplacer ce modèle simplifié.

**Avant achat, relever** : courbe force/vitesse, courant en charge et au blocage, facteur de service admissible, étanchéité, efforts latéraux autorisés, et **maintien hors tension** (vérin réversible ou non). La non-réversibilité ne se déduit pas du seul mot « vérin » ni du type de transmission : elle se vérifie sur la fiche technique ou au banc. Prévoir un dégagement mécanique rapide, accessible même sous charge.

### 7.6 Architecture et validation *(propositions issues de la version révisée, non décidées)*

Ces propositions touchent le chantier « sécurité et conduite en navigation », **encore non ouvert**. Elles sont notées comme pistes, pas comme exigences.

**Première version possible.**
- Mode compas seul, interface locale lisible, commande de veille dédiée et reprise manuelle simple. Les commandes de déplacement manuel s'arrêtent au relâchement ; un recentrage éventuel reste volontaire et supervisé.
- Le contrôleur moteur limite les mouvements en cas de commande périmée, de capteur invalide ou de défaut de position ; un redémarrage revient en veille.
- Fins de course, limitation de courant et butées logicielles ont des rôles complémentaires : une mesure de courant ne distingue pas à elle seule une butée normale d'un grippage.
- La veille électrique ne libère pas forcément la barre : le dégagement mécanique est une fonction distincte, à vérifier.
- Interface NMEA : préciser le transport et l'adaptation électrique ; tester unités, signes bâbord/tribord, cap magnétique ou vrai, validité et âge des données. Une trame reçue ne garantit pas une route bien suivie.
- Ordre d'introduction : compas, puis vent, puis suivi de route ; chaque perte de source produit un état prévu et affiché. L'évitement de zones (décision d'intention) vient dans un chantier ultérieur.

**Améliorations à prioriser.** Reproductibilité (figer code, bibliothèques, carte, schéma, paramètres et commit) ; observabilité (journaliser cap demandé et mesuré, vitesse de lacet, commande moteur, position, courant, tension, âge des données, défauts) ; référence de réglage simple avant toute adaptation, anticipation du vent ou compensation de gîte ; comparaison mesurée (erreur de cap, dépassement, énergie, activité du vérin) ; coût complet (interface, protections, boîtiers, connecteurs, fixations, temps de mise au point).

**Validation par étapes.**

| Étape | Essai | Condition de passage |
|---|---|---|
| Banc, sans charge | Sens moteur, arrêt, redémarrage, commandes périmées | Aucun mouvement involontaire ; retour en veille vérifié |
| Banc, charge maîtrisée | Courant, échauffement, butées, défaut du retour de position | Réaction conforme aux limites écrites du matériel |
| À quai | Géométrie complète, fixation, dégagement, perturbation du compas moteur en marche | Pas de coincement ; reprise manuelle démontrée |
| Eau libre, temps calme | Petits changements de cap, réglages progressifs | Réponse stable, pas de saturation persistante |
| Conditions élargies | Gîte, vagues, charge et durée croissantes | Comportement reproductible, limites documentées |
| Vent, puis route | Perte de source, données invalides, transitions de mode et de waypoint | Réaction prévue et compréhensible pour le barreur |

Les seuils (erreur, délai d'arrêt, température) seront à fixer avant les essais, à partir du matériel retenu.

## 8. À vérifier ensuite

1. Plot Device : lire `PID.ino`, `Keypadtiller.ino` et les fonctions `Right_Rudder`/`Left_Rudder`/`Rudder_Stop` pour confirmer l'absence de protection en courant.
2. KastB : lire les classes `Motor` (saturation, `gotoPos`, blocage) et `IMU` (autocalibration) ; comprendre l'incohérence des gains (constructeur contre en-tête).
3. YAAAP : lire `CalLib` et la gestion de l'ACS712 en conditions réelles.
4. Jack Edwards : obtenir le README complet de l'archive et confirmer la version J11 (BNO055, radio nRF24).
5. Dates de dernier commit des six dépôts.
6. Visionner les vidéos citées (Jack Edwards, The Plot Device en barre franche, chaîne Fenix, essais pypilot) : je ne peux pas le faire moi-même.
7. Vérifier si le vérin choisi sera réversible ou non (voir 1.7 et 7.3).
8. Rattacher les descriptions de code de cette note à un **identifiant de commit** pour chaque dépôt, puis les revérifier avant toute reprise de code (les branches consultées n'étaient pas figées).
9. Fenix : vérifier la chaîne réelle de mesure du courant avec le shield Cytron (capteur, broche, seuil, arrêt effectif).
10. YAAAP : chiffrer la marge mémoire par une compilation.
11. Relever les cotes de montage réelles sur le Capri 22 (distance mèche-fixation, ancrage, débattement utile) pour refaire le calcul de 7.5.

## Sources

- pypilot : https://github.com/pypilot/pypilot ; analyse du 2026-11-02 (fiche `analyse-depots-open-source-pilotes`) ; manuel pypilot (copie : https://apps.hisse-et-oh.com/store/medias/sailing/66c/48e/bcb/original/66c48ebcb6681b6f0131eae7.pdf) ; https://openplotter.readthedocs.io/4.x.x/pypilot/pypilot_app.html ; https://github.com/pypilot/workbook/wiki/The-hardware-component ; forum OpenMarine : https://forum.openmarine.net/printthread.php?tid=4108, https://forum.openmarine.net/showthread.php?pid=28521, https://forum.openmarine.net/showthread.php?pid=22526, https://forum.openmarine.net/printthread.php?tid=3492, https://forum.openmarine.net/showthread.php?pid=10805, https://forum.openmarine.net/showthread.php?tid=3201, https://forum.openmarine.net/printthread.php?tid=3595 ; https://www.bateaux.com/article/40676/pypilot-le-pilote-de-secours-open-source-qui-a-sauve-notre-voyage
- Fenix : https://github.com/spascual90/Fenix ; même fiche ; https://fenix-autopilot.com/build-of-materials/ ; https://spascual90.gitbook.io/fenix-autopilot ; https://www.seabreeze.com.au/forums/Sailing/General/Fenix-Autopilot ; https://github.com/JoergSH/Fenix
- The Plot Device : https://github.com/jeff-burright/Autopilot_ESP32_wifi (README, `Autopilot_ESP32_2.1.ino`, `PIDtiller.ino`, `Output.ino`, `documentation/Autopilot parts list_ESP32.pdf`) ; https://www.cruisersforum.com/forums/f13/yet-another-arduino-autopilot-for-wheel-or-tiller-150-a-276530.html
- YAAAP : https://github.com/FilBip/yaaap (README, `yaaap/yaaap.ino`) ; https://forum.arduino.cc/t/yaaap-un-pilote-automatique-pour-bateau/385917 et page 2
- Jack Edwards : https://github.com/CoyoteWaits/Jack_Edwards_Autopilot ; https://themarineinstallersrant.blogspot.com/2013/12/the-arduino-autopilot-that-jack-built.html ; https://hackaday.com/2014/01/08/ride-captain-ride-aboard-your-arduino-controlled-autopiloted-sailboat ; https://classicwoodboat.blogspot.com/2017/04/arduino-weds-raspberry-freeboard-project.html ; https://www.firgelliauto.com/blogs/news/making-a-boat-autopilot-using-a-linear-actuator-for-under-350 ; https://forum.arduino.cc/t/auto-pilot-for-tiny-yacht/188972?page=2
- Licences : https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- pypilot (compléments de l'audit) : https://github.com/pypilot/pypilot/blob/master/pypilot/pilots/basic.py ; https://github.com/pypilot/pypilot/blob/master/arduino/motor/motor.ino
- Shield Cytron SHIELD-MD10 : https://ca.robotshop.com/products/cytron-10a-dc-motor-driver-arduino-shield ; https://makerselectronics.com/product/cytron-shield-md10-dc-motor-driver/
- Documents critiques fournis par Mathieu le 2026-11-06 : audit du comparatif et version révisée
- KastB : https://github.com/KastB/boat_autopilot (README, `autopilot.ino`, `libraries/PID/PID.cpp`)
