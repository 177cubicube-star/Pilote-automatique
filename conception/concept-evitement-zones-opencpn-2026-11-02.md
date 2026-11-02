# Concept : Évitement de zones (contours du lac, hauts-fonds) avec un traceur type OpenCPN

Rédigé le 2026-11-02. **Statut : CONCEPT EXPLORATOIRE — PROPOSITION. Aucune décision de conception n'est validée** ; les décisions de Mathieu sont dans `conception/decisions-et-dispositions-2026-11-02.md` (DP-02), qui fait autorité. Cette note les développe sans les modifier.

**Non exécuté :** aucun essai. Les sources sont des lectures (ODraw/ODAPI, Watchdog, Signal K, Freeboard-SK, pypilot, Fenix) ; les essais à terre sont **reportés** (`essais/zones-opencpn-20261102/README.md`).

**Rangement :** `conception/`, choix **à confirmer par Mathieu**. Version du vault : `05 - Concepts/CON-007 - Évitement de zones avec un traceur type OpenCPN.md` ; recoupe, sans fusion, les règles du vault de limites de commande, de reprise manuelle et de chien de garde (L-12, D-05, D-10/G5).

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

## 1. L'intention (décidée par Mathieu, 2026-11-02)

- Pouvoir **marquer les contours du lac et les hauts-fonds** dans un traceur (OpenCPN ou équivalent), pour que le système déclenche une **alarme** et, par exemple, un **changement de direction**.
- **Prévoir cette fonction dès la conception** (niveau « manœuvre automatique »), **en plus** du suivi d'itinéraire classique avec OpenCPN.
- L'**implantation** sera un chantier ultérieur de recherche et de codage. Ce n'est pas décidé : la plateforme, l'ordre de réalisation et les limites de la manœuvre automatique.
- Mathieu a convenu que suivre un itinéraire ou une zone n'évite pas les obstacles et que le chantier « sécurité et reprise de commande » prend de l'importance.

## 2. Ce qui est établi (lu dans les sources, rien n'est testé)

**Côté OpenCPN : dessin et alarmes.**
- Le plugin **ODraw** permet de placer sur la carte des points et des tracés repérés géographiquement, dont un type **« Boundary »** (limite). Source : description du paquet pkgsrc.
- Le plugin **Watchdog** (de Sean D'Epagnier, l'auteur de pypilot) implémente des alarmes configurables sur les conditions autour du bateau, une alarme de « veilleur » (deadman) et une alarme d'ancre améliorée, et il communique avec ODraw. Un utilisateur du forum de pypilot parle de « zones d'exclusion » de Watchdog, qu'il juge lourdes à utiliser. Le détail du réglage des alarmes de limite n'a pas été lu.
- Ces alarmes **avertissent l'utilisateur** (son, affichage). Je n'ai trouvé aucune fonction d'OpenCPN qui calcule seule une manœuvre pour éviter une zone.
- Pratique professionnelle : sur les cartes marines électroniques des navires, on dessine à la main des zones interdites, et s'en approcher déclenche une alarme visible et sonore pour le navigateur (présentation INTERTANKO à l'OHI). C'est une alarme pour l'humain.
- Le plugin **Autopilot Route** (autopilot_route_pi, du même auteur) produit des phrases RMC et APB depuis une route OpenCPN ; elles sont transmises à pypilot par une connexion TCP. Le plugin offre un algorithme de suivi de route plus élaboré que le comportement standard (« Route Position Bearing »).

**Côté OpenCPN : comment les zones peuvent sortir (recherche du 2026-11-02).** OpenCPN ne les transmet pas directement à un programme externe. Quatre voies ont été examinées :
- **Voie A, par un plugin (interface ODAPI d'ODraw).** ODraw expose aux autres plugins d'OpenCPN, par des messages JSON (destinataire `OCPN_DRAW_PI`) et par une interface C++ rapide (`ODAPI.h`), des fonctions lues dans l'en-tête : `OD_FindPointInAnyBoundary` (la position donnée est-elle dans une limite ? renvoie type, état, nom et identifiant), `OD_FindClosestBoundaryLineCrossing` et `OD_FindFirstBoundaryLineCrossing` (à partir d'un point de départ et d'un point d'arrivée, où le segment croise-t-il une limite, à quelle distance ?), la liste de tous les tracés et points, ainsi que la création et la suppression de limites et de points. L'en-tête définit trois types de limites : **exclusion, inclusion ou aucune des deux** (`EXCLUSION_BOUNDARY`, `INCLUSION_BOUNDARY`, `NEITHER_BOUNDARY`). Watchdog s'en sert pour la distance et le temps avant une limite (notes de version d'ODraw 1.2). L'unité de la distance de croisement n'est pas précisée dans l'en-tête. **Un programme externe ne peut pas appeler cette interface : il faudrait écrire un plugin en C++** qui sert de passerelle. Un plugin d'essai de l'interface existe dans le catalogue des plugins.
- **Voie B, par un fichier.** OpenCPN charge au démarrage ses objets de navigation depuis un fichier `navobj.xml` (ligne de journal d'un utilisateur). Savoir si les limites d'ODraw y sont aussi enregistrées, et à quel moment le fichier est mis à jour, n'a pas pu être vérifié (le manuel d'ODraw est bloqué à la lecture automatique). Ce n'est de toute façon pas une lecture en direct.
- **Voie C, par le serveur REST d'OpenCPN.** Il existe (la page de manuel d'OpenCPN décrit une option qui affiche l'adresse du serveur REST local, par exemple `http://localhost:8000`, et une option pour envoyer des commandes à une instance en marche). Ses points d'accès n'ont pas été trouvés : ce qu'il permet de lire, y compris les zones, est inconnu.
- **Voie D, par les connexions de données.** OpenCPN lit et écrit du NMEA en série, en Bluetooth, en TCP ou en UDP, et peut se comporter en serveur TCP. Ces flux transportent des phrases NMEA standard : **elles ne contiennent pas de zones**.

**Côté Signal K (alternative documentée pour un programme externe).**
- Le serveur Signal K a une interface de ressources avec un type **`regions`** (zones), à côté des routes, waypoints, notes et cartes. **Freeboard-SK**, un traceur qui s'affiche dans un navigateur sur tout appareil, permet de **dessiner des régions** et d'y attacher des notes.
- Freeboard-SK expose une interface d'**alarmes de zone** (spécification OpenAPI 2.18) : `POST /signalk/v2/api/alarms/area` pour définir une zone d'alarme avec `trigger` valant `entry` (entrée) ou `exit` (sortie), `geometry` valant `polygon`, `circle` ou `region`, des coordonnées (ou un centre et un rayon en mètres) ; `PUT` sur `/signalk/v2/api/alarms/area/{id}` pour modifier la zone ou y utiliser une région existante ; `DELETE` pour l'annuler ; et une route pour mettre l'alarme en silence. L'authentification se fait par cookie ou par jeton JWT. La spécification ne précise ni les notifications émises, ni leurs chemins, ni la version minimale requise.
- pypilot s'intègre à Signal K (vérifié dans l'analyse des dépôts). Fenix n'a pas de lien direct avec Signal K ; il faudrait un pont entre ses trames NMEA et le serveur.

**Côté pypilot.**
- Il reçoit les phrases APB d'OpenCPN pour suivre une route. D'après l'auteur, OpenCPN ne produit pas d'APB avec cap magnétique, donc pypilot suit alors la route avec le GPS ; si OpenCPN cesse d'envoyer l'APB, pypilot **garde le dernier cap**.
- L'auteur dit que traiter les points de route et déclencher l'avertisseur dans pypilot serait possible mais n'est pas implémenté, puisqu'OpenCPN sait déjà jouer un son.
- Il accepte des commandes externes par son interface réseau : par exemple `ap.heading_command`, `ap.enabled`, `servo.command` (un projet tiers, `pypilot_ray`, s'en sert avec des boutons GPIO). Savoir si le servo s'arrête de lui-même aux butées n'a pas de réponse claire dans l'extrait lu.

**Côté Fenix.**
- Il reçoit les phrases APB (cible de route), HDG et HDT, MWV et VWR, la vitesse fond, et des trames propriétaires `$PEMC` (dont des commandes de cap et de barre, types 01 et 02). Il émet RSA (angle de barre) et HDG. L'écart latéral (XTE) est lu par l'analyseur.
- Mode de suivi (« Track » ou « Nav ») : suit un waypoint à partir d'un cap externe. Limites notées dans RELEASE.md : le repli sur le relèvement vers le waypoint n'est pas implémenté, et le virement est impossible dans ce mode.
- Le site du projet annonce une intégration avec OpenCPN ; le mode de liaison (USB ou Bluetooth) n'est pas vérifié.
- **Avertisseur** : un composant `DevBuzzer` existe, mais dans la boucle principale (`Fenix.ino`) le commentaire indique que **le signal sonore est encore à faire** (TODO) ; l'état d'erreur n'allume que le rétroéclairage de l'écran, s'il est présent. Des alarmes d'écart de route existent dans `Autopilot.cpp` (`compute_OCA`). À ne pas compter comme acquis.

**Autres systèmes étudiés.** Milo et SimplePilot n'ont aucune entrée NMEA dans le code lu : ils partiraient de zéro. Nautinect annonce du NMEA dans son README, mais pas dans son code source lu.

## 3. Niveaux de réaction (échange du 2026-11-02)

| Niveau | Réaction | Disponible aujourd'hui ? |
|---|---|---|
| 1 | Alarme seule (ordinateur ou tablette) | Oui, avec OpenCPN, ODraw et Watchdog (non testé) ; ou avec les alarmes de zone de Freeboard-SK (non testé) |
| 2 | Alarme au poste de barre (avertisseur, voyant) | À construire ; ni Fenix ni pypilot ne le font pour des zones |
| 3 | Manœuvre automatique limitée | À écrire (logique « gardien ») ; **fonction à prévoir dans la conception** (décision de Mathieu) |

Idée de passage intermédiaire (proposition de Claude) : un **mode fantôme**, où la logique calcule ses décisions, les journalise et déclenche l'alarme, mais n'envoie aucune commande au pilote. Il permettrait de juger le comportement sur l'eau sans lui donner de pouvoir.

## 4. Architecture proposée (hypothèse de travail)

- **Gardien** : programme qui compare la position du bateau aux zones, décide d'une alarme ou d'une demande de changement de cap bornée. Hypothèse : il tourne **hors du pilote** (ordinateur, Raspberry Pi ou tablette), parce qu'un microcontrôleur de petite taille manipule mal des polygones, et pour garder le pilote simple et testable seul. L'autre option, un gardien dans le pilote, est à examiner.
- **Source des zones (point de conception important)** : trois sources sont possibles d'après la recherche du 2026-11-02 : un plugin OpenCPN qui s'appuie sur ODAPI, les régions d'un serveur Signal K, ou un fichier propre. Pour ne pas fermer de porte, le gardien devrait lire les zones à travers un **adaptateur** (une couche qui cache d'où elles viennent), de sorte que la source puisse changer sans réécrire la logique de décision. Proposition, non validée.
- **Pilote** : exécutant sûr. Il suit son cap, accepte des demandes externes **bornées** et les refuse si elles sont hors limites, et revient à un comportement sûr si le gardien se tait.
- **Poste de barre** : joystick ou touches pour la reprise de main immédiate, et une alarme locale.
- **Flux** : position et vitesse (GPS) vers le gardien ; zones vers le gardien ; demandes de cap vers le pilote par une interface NMEA ou propre au pilote ; alarmes vers le poste de barre.
- **Primitive utile (inférence, non testée)** : la fonction ODAPI de croisement de ligne (`OD_FindClosestBoundaryLineCrossing`) répond à la question « si je continue vers ce point, où et à quelle distance croiserai-je une limite ? ». Avec comme point d'arrivée la position projetée le long du cap, c'est le calcul de regard vers l'avant dont un gardien aurait besoin. La distance et sa fiabilité restent à vérifier.

## 5. Dispositions de conception à prévoir

Elles rendent le niveau 3 possible sans l'imposer. Pour chacune, la raison. (Propositions de Claude, non validées ; reprises dans `conception/decisions-et-dispositions-2026-11-02.md (DP-02)`.)

1. **Source de position et de vitesse (GPS)** accessible au gardien. Sans elle, aucune comparaison aux zones.
2. **Interface de commande externe bornée** (angle maximal, durée maximale, validation). Sans bornes, une erreur du gardien devient une erreur de barre.
3. **Priorité absolue de l'action humaine** (joystick, touche, désengagement) sur toute demande automatique. C'est la règle de sécurité centrale.
4. **Port NMEA 0183 réservé** : entrée de route (APB), sorties (barre, cap, alarme). Fenix en a déjà un ; pypilot passe par son réseau et Signal K.
5. **Alarme au poste de barre**, indépendante de l'ordinateur. Mathieu navigue souvent en solitaire, les mains occupées.
6. **État d'évitement** dans la logique des modes, avec conditions d'entrée et de sortie et journal.
7. **Chien de garde** : si le gardien cesse de communiquer ou si le GPS devient invalide, retour à un comportement sûr et alerte. C'est le défaut relevé chez Nautinect (une commande qui reste appliquée sans limite de temps).
8. **Enregistrement** des mesures et des décisions, qui sert aussi à valider la note sur l'anticipation par capteurs.
9. **Adaptateur de source de zones** (OpenCPN, Signal K, fichier) : le gardien ne dépend pas d'une seule source.
10. **Choix gardien dans ou hors du pilote** : à examiner (voir 4).

## 6. Marge de sécurité : raisonnement illustratif

Pour qu'une manœuvre d'évitement soit utile, la distance de déclenchement doit couvrir tout ce qui se passe avant que le bateau ne change réellement de trajectoire. En première approximation :

**marge ≈ vitesse × (délai de détection + délai du vérin + temps de virage) + erreur du GPS + marge de sécurité**

À titre d'ordre de grandeur **non recherché** : à 2 m/s, avec 10 s de délai cumulé (le vérin recommandé par Fenix met environ 10 s à parcourir toute sa course : 300 mm à 30 mm/s), la marge atteint déjà 20 m avant l'erreur du GPS. Sur un petit plan d'eau, cela peut représenter une grande part de la largeur. Le temps de virage peut s'estimer avec un modèle de Nomoto du bateau (Fenix en identifie un en route ; ses valeurs de départ sont calées pour un autre bateau). L'erreur d'un GPS grand public est de quelques mètres (connaissance générale, non vérifiée ici).

## 7. Modes de défaillance et parades à étudier

| Défaillance | Conséquence possible | Parade à étudier |
|---|---|---|
| GPS imprécis ou perdu | Fausse alarme ou absence d'alarme | Contrôle de validité, retour à un comportement sûr, alerte |
| Gardien ou liaison en panne | Commande figée ou plus aucune protection | Chien de garde, délai d'expiration de chaque demande |
| Mauvais sens d'évitement | Aggraver la situation | Règles de choix simples, angle borné, alarme prioritaire sur la manœuvre |
| Zone mal dessinée | Alarme inutile ou danger non signalé | Vérification des zones, mode fantôme avant tout pouvoir |
| Fausses alarmes fréquentes | Perte de confiance de l'utilisateur | Réglage des marges, journal pour analyse |
| Conflit entre action humaine et demande automatique | Résistance du système à la reprise de main | Priorité absolue à l'humain, test dédié |
| Cap magnétique faussé (déviation, gîte) | Virage dans le mauvais sens | Calibration et contrôle de cohérence avec la route GPS |
| Source de zones indisponible (programme d'affichage fermé, serveur arrêté) | Plus aucune zone connue | Copie locale des zones, alerte à la perte de la source |
| Autres bateaux ou obstacles non cartographiés | Non gérés par le système | Veille humaine ; le système ne remplace pas la vigilance |

## 8. Plan de recherche et de codage proposé (non engagé)

1. **Lire** (avancé le 2026-11-02 : voir 2) les points d'accès du serveur REST d'OpenCPN, la liste des messages JSON d'ODraw, l'emplacement de stockage des limites, et les notifications émises par les alarmes de zone de Freeboard-SK.
2. **Lire** le détail des commandes externes de Fenix (`$PEMC`, mode de suivi) et de pypilot (interface réseau, comportement aux butées).
3. **Modéliser** le délai de virage et de réponse du vérin pour fixer la marge, à partir de mesures (enregistreur de données).
4. **Prototyper à terre** : rejouer des positions GPS enregistrées devant le gardien, en mode fantôme, sans pilote.
5. **Simuler** avec les outils disponibles (simulateur de Fenix qui simule cap et barre sans centrale ni vérin ; simulateurs de voilier) avant tout essai réel.
6. **Essayer sur l'eau en mode fantôme** (alarme et journal seulement), puis seulement décider du niveau 2, puis du niveau 3 avec limites strictes.

## 9. Questions ouvertes

- Quels sont les points d'accès du serveur REST d'OpenCPN ? Permet-il de lire les zones ?
- Où ODraw enregistre-t-il les limites (fichier `navobj.xml` ou autre), et à quel rythme ?
- Quelles notifications les alarmes de zone de Freeboard-SK émettent-elles, et comment un programme externe les reçoit-il ?
- Faut-il garder OpenCPN comme outil de dessin et de carte (avec une passerelle en plugin C++), ou dessiner dans Freeboard-SK, plus facile à relier à un programme externe ? Compromis à discuter avec Mathieu, qui souhaite pouvoir utiliser OpenCPN.
- Gardien dans ou hors du pilote ?
- Quelle stratégie de choix du sens d'évitement, et quelles limites de la manœuvre (angle, durée) ?
- Quelle précision de position est réellement atteignable sur ce plan d'eau, avec quel récepteur ?
- Faut-il aussi une alarme sur la profondeur mesurée par un échosondeur (NMEA), en complément des zones dessinées ?
- Un « couloir » le long d'une route avec alarme d'écart latéral (XTE) suffirait-il pour certains usages, comme solution plus simple ?
- Comment prouver, avant l'eau, que la reprise de main humaine l'emporte toujours ?

## 10. Liens et sources

- Décisions : `conception/decisions-et-dispositions-2026-11-02.md (DP-02)` (autorité). Analyse des dépôts : `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`. Anticipation par capteurs : `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`. Essai (reporté) : `essais/zones-opencpn-20261102/README.md`.
- ODraw (pkgsrc) ; en-tête `include/ODAPI.h` et notes de version d'ODraw 1.2 (dépôt `jongough/ocpn_draw_pi`) ; Watchdog (description du paquet) ; page de manuel d'OpenCPN (serveur REST) ; journal d'un utilisateur (chargement de `navobj.xml`) ; Freeboard-SK (README et spécification OpenAPI 2.18) ; forum OpenMarine (alarmes, APB, cap magnétique) ; plugin Autopilot Route (dépôt et analyse de Marco Bergman) ; présentation INTERTANKO à l'OHI ; dépôt Fenix (`Fenix.ino`, `Autopilot.cpp`, `emcNMEA.cpp`, `RELEASE.md`) ; dépôt pypilot et son workbook ; projet tiers `pypilot_ray`.
