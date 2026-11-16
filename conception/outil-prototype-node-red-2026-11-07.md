# Concept : Node-RED comme outil de montage et de prototype

Rédigé le 2026-11-07. **Statut : CONCEPT EXPLORATOIRE — PROPOSITION. Aucune décision de conception n'est validée** ; la décision de Mathieu sur l'outil (DP-04, proposée) est consignée dans `conception/decisions-et-dispositions-2026-11-02.md`, qui fait autorité. Cette note la développe sans la modifier.

**Non exécuté :** Node-RED n'est ni installé ni essayé. Les faits viennent de la documentation officielle et de pages de paquets et de forums, lues le 2026-11-07.

**Rangement :** `conception/`, choix **à confirmer par Mathieu**. Cette note n'a pas été portée dans le vault.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

## 1. Ce que Mathieu a énoncé (2026-11-07)

Node-RED (https://github.com/node-red/node-red) est l'outil que Mathieu utilisera pendant le **montage** et le **prototypage** du pilote. Cet énoncé porte sur l'**outil d'essai** uniquement. Il ne choisit ni la plateforme du pilote final (Arduino, Raspberry Pi ou autre), ni l'architecture, et il ne dit pas si Node-RED restera dans le système une fois le prototype terminé. Statut : **PROPOSÉE** (DP-04), comme les trois décisions précédentes.

## 2. L'idée générale, en langage simple

Node-RED est un outil de programmation « visuelle ». Au lieu d'écrire un long programme ligne par ligne, on dessine dans une page web un **flux** (*flow*) : des boîtes appelées **nœuds** (*nodes*), reliées par des fils. Chaque nœud fait une petite chose : lire un port série, découper une phrase, faire un calcul, afficher un résultat, envoyer une donnée plus loin. Les données voyagent d'un nœud à l'autre dans des **messages**, des petits paquets dont le contenu principal se trouve dans `msg.payload`. Le site officiel le décrit comme de la programmation « low-code » pour des applications pilotées par des événements : rien ne se passe tant qu'un événement (une phrase NMEA qui arrive, un clic, une minuterie) ne déclenche le flux.

Pour un projet de pilote automatique, c'est l'équivalent d'une **table de montage électronique** : on branche des morceaux, on regarde ce qui circule, on débranche et on recommence, sans avoir à compiler un programme à chaque essai. Ce goût du « voir et manipuler » correspond bien à un esprit visuel, issu du design industriel.

Le programme est écrit en JavaScript (Node-RED repose sur Node.js). On n'a pas besoin d'en écrire pour la plupart des flux, mais un nœud « fonction » permet d'y glisser quelques lignes de JavaScript quand un calcul est trop particulier.

Licence : Apache-2.0, avec un copyright de l'OpenJS Foundation et d'autres contributeurs (page GitHub).

## 3. Ce qui est établi (CONFIRMÉ par lecture le 2026-11-07, NON EXÉCUTÉ)

**Installation et exploitation.**
- La page de départ de la documentation propose plusieurs options : sur un ordinateur local, sur Raspberry Pi (script d'installation tout-en-un), dans Docker, ou depuis le code source (git). Elle mentionne aussi BeagleBone, Android (via Termux, expérimental), FlowFuse, AWS et Azure. **Windows n'apparaît pas dans la liste de cette page** : la procédure d'installation locale reste **À VÉRIFIER**.
- Sur Raspberry Pi, un script unique installe Node.js, npm et Node-RED, sur les systèmes Debian (dont Ubuntu). Le même script sert à mettre à jour. Si Node.js est déjà présent, il vérifie qu'il est en version 20 ou plus récente ; sinon il installe la version 22 LTS. À partir de Node.js 24, il n'existe plus de versions 32 bits : les Pi de type armv6 ne seront plus pris en charge. La page ne liste pas de modèles précis.
- Le script installe Node-RED comme **service**. Pour qu'il démarre tout seul à l'allumage : `sudo systemctl enable nodered.service`.
- L'éditeur est accessible dans un navigateur sur le **port 1880** : `http://localhost:1880` sur la machine elle-même, ou `http://<nom-de-la-machine>:1880` depuis un autre appareil (téléphone, ordinateur du bord).

**Sécurité de l'éditeur.**
- Par défaut, **l'éditeur n'est pas protégé** : quiconque atteint l'adresse peut ouvrir l'éditeur et **déployer** des modifications. La documentation précise que c'est acceptable seulement sur un réseau de confiance.
- On protège l'éditeur avec la propriété `adminAuth` du fichier `settings.js` (type `credentials`, mot de passe haché avec bcrypt, permissions `"*"` pour tout faire ou `"read"` pour la lecture seule). La commande `node-red admin hash-pw` (version 1.1.0 ou plus récente) fabrique le mot de passe haché. Les nœuds HTTP se protègent à part avec `httpNodeAuth`.

**Lire et écrire sur un port série (le lien avec le NMEA 0183).**
- Le paquet `node-red-node-serialport` (version 2.0.3 au moment de la lecture, licence Apache-2.0) apporte les nœuds *serial in*, *serial out*, *serial request*, *serial-port* (configuration) et *serial control*. Il s'installe par le menu « Manage palette » de l'éditeur. L'installation peut afficher des messages ressemblant à des échecs de compilation qui sont souvent de simples avertissements.
- *serial in* peut découper le flux reçu à un caractère (par défaut le saut de ligne `\n`), après un délai, ou par taille fixe, et livre le texte en chaîne UTF-8 ou en données binaires. Pour des phrases NMEA 0183, qui se terminent par un retour à la ligne, le découpage par défaut convient sans doute (**INFÉRENCE**).
- Le nœud *serial control* permet de **changer de port à la volée**. Utile parce qu'un adaptateur USB qui se rebranche peut changer de numéro (point relevé dans la description du paquet).
- Sur un système Linux, un adaptateur NMEA vers USB apparaît comme `/dev/ttyUSB0` (numéro variable), et la vitesse standard du NMEA 0183 est de **4800 bauds** ; l'AIS et les multiplexeurs utilisent 38400 bauds (site de Signal K).
- Savoir si ces nœuds sont déjà présents après l'installation du script officiel : **À VÉRIFIER** à la première installation.

**Lien avec Signal K.**
- Le paquet `@signalk/node-red-contrib-signalk` (version 1.2.0 au moment de la lecture) ajoute des nœuds Signal K à Node-RED. Il fonctionne dans deux situations : avec un Node-RED **séparé** du serveur Signal K (on déclare alors un nœud de configuration `signalk-client` avec l'adresse, le port, le chiffrement TLS éventuel et les identifiants), ou avec un Node-RED **intégré** dans le serveur Signal K par le plugin `signalk-node-red`. Il permet de lire le serveur, de publier des mises à jour, de traiter des requêtes PUT et d'envoyer des notifications. Dans le mode séparé, il demande d'ajouter un espace de stockage `skpersist` au fichier `settings.js`.
- Certains nœuds ne fonctionnent que dans le mode intégré : événements de l'application, deltas entrants, interception des entrées, et **sortie NMEA** (envoi de phrases NMEA 0183 ou de messages NMEA 2000).
- Le plugin `signalk-to-nmea0183` convertit des données Signal K en phrases NMEA 0183 et les rend disponibles sur le serveur TCP NMEA 0183 intégré de Signal K, au **port 10110**. OpenCPN peut s'y connecter comme client TCP (page du paquet).
- Un ancien paquet de nœuds intégrés (`@signalk/node-red-embedded`) mentionnait un nœud `signalk-geofence-switch` qui vérifie si le bateau est à l'intérieur d'une zone définie (« geofence »). Cette information vient du journal de modifications d'une version datant de 2020. **À VÉRIFIER :** un nœud équivalent existe-t-il dans le paquet actuel ? À regarder avant de compter dessus.

**Précédents dans les sources du projet et dans la communauté.**
- Dans l'analyse des dépôts (`sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`), un utilisateur de pypilot a dû passer par Node-RED pour convertir l'attitude (qui circule dans Signal K) en phrase propriétaire Furuno, afin de la lire sur un traceur.
- Sur le forum OpenMarine (mars 2024), un utilisateur a converti une phrase de vent **MWV** en **VWR** avec Node-RED, en recalculant le total de contrôle (*checksum*) pour ré-émettre la phrase. Quelqu'un lui répond qu'un plugin Signal K le fait aussi. C'est un exemple concret de ce que Node-RED sait faire entre une girouette et un pilote.
- **HYPOTHÈSE** (connaissance générale, non vérifiée ici) : le total de contrôle d'une phrase NMEA 0183 est le « OU exclusif » (XOR) de tous les caractères situés entre le `$` et le `*`, écrit en deux chiffres hexadécimaux.

## 4. Rôles possibles pendant le prototype (PROPOSÉE par Claude, non validée)

Mathieu n'a pas encore précisé le rôle de Node-RED. Voici cinq rôles qui se rattachent à ce que le dépôt a déjà établi. Ils peuvent se combiner. Le choix, et l'ordre, appartiennent à Mathieu (**À DÉCIDER**).

| Rôle | En une phrase | Lien avec le dépôt |
|---|---|---|
| A. **Banc d'essai** | Fabriquer ou rejouer des données (position GPS, vent, cap) et les envoyer au pilote ou au traceur, sans bateau ni capteur réel. | Essais à terre reportés le 2026-11-02 (DP-02) ; scripts `essais/zones-opencpn-20261102/simulate_gps_rmc.py` et `test_simulate_gps_rmc.py` déjà présents. À décider : Node-RED les complète-t-il, ou les remplace-t-il ? |
| B. **Passerelle / traducteur** | Faire parler entre eux des appareils qui n'ont pas le même « langage » (NMEA 0183, Signal K, trames propriétaires). | Girouette NMEA (DP-03), traceur OpenCPN, trames `$PEMC` de Fenix, DISP-04 et DISP-11. |
| C. **Journal d'essais** | Enregistrer ce qui circule (horodaté) pour comprendre après coup. | DISP-08 (enregistrement des mesures et des décisions). |
| D. **Tableau de bord de mise au point** | Afficher cap, barre, vent, alarmes, et changer des réglages pendant les essais. | Réglages des gains (trames `$PEMC` 05 et 06 de Fenix), validation de l'anticipation (`conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`). La palette de tableau de bord à utiliser reste **À VÉRIFIER**. |
| E. **Prototype du « gardien » en mode fantôme** | Comparer la position du bateau aux zones, journaliser ses décisions et déclencher une alarme, **sans jamais envoyer de commande au pilote**. | `conception/concept-evitement-zones-opencpn-2026-11-02.md`, DISP-01, DISP-06, DISP-07, DISP-09 et DISP-10, et l'hypothèse « gardien hors du pilote ». |

Une raison de s'intéresser à E : l'hypothèse de travail du dépôt est que le gardien tourne **hors du pilote** (ordinateur, Raspberry Pi ou tablette). Node-RED est précisément un programme qui tourne sur ce genre de machine. Il pourrait donc servir de **maquette** du gardien : les idées s'y essayent vite, puis on décide plus tard si la version finale reste dans Node-RED ou est réécrite ailleurs. Ce n'est pas une décision.

## 5. Ce que Node-RED ne doit pas faire (principes de sécurité, PROPOSÉE)

Ces principes prolongent la règle déjà énoncée par Mathieu : la reprise de main humaine l'emporte toujours (DISP-03). Ils prolongent aussi DISP-02 et DISP-07 ; ils ne les remplacent pas.

1. **Node-RED n'est pas dans la boucle de sécurité.** Le pilote reste un « exécutant sûr » qui garde son cap, refuse les demandes hors limites et revient à un comportement sûr si on lui parle plus. La barre ne doit jamais dépendre d'un flux Node-RED qui fonctionne bien.
2. **Pas de commande de barre depuis Node-RED au début.** On commence par observer, journaliser et alerter (niveaux 1 et 2 du concept d'évitement de zones). Toute commande vers le pilote passe par les dispositions déjà proposées : demandes bornées en angle et en durée, expiration, priorité humaine, chien de garde.
3. **Le temps réel n'est pas garanti.** **HYPOTHÈSE** (connaissance générale sur Node.js : un seul fil d'exécution principal, des tâches qui s'enchaînent selon les événements ; non vérifié dans cette session). Une boucle de régulation serrée du vérin n'a donc pas sa place dans Node-RED. Les délais acceptables pour un gardien sont une question à mesurer.
4. **Le bouton « Deploy » modifie le programme en marche.** Un changement de flux pendant que du matériel est branché peut avoir un effet immédiat. Règle proposée : modifier à terre ou en mode fantôme, jamais en direct sur un pilote qui commande la barre.
5. **Protéger l'éditeur** dès qu'il est accessible par Wi-Fi à bord (voir section 3). Ne jamais l'exposer sur Internet sans protection.

## 6. Montage de banc d'essai (PROPOSÉE, à discuter)

```
 Girouette NMEA ─┐
 GPS (NMEA) ─────┼─► Adaptateur USB ─► Machine hôte avec Node-RED ─► OpenCPN (TCP)
 Fenix (série) ──┘                          │    │                    Signal K (option)
                                            │    └─► Journal (fichiers horodatés)
                                            └─► Tableau de bord (navigateur, téléphone)
```

Lecture du schéma : les capteurs et le pilote envoient leurs phrases à l'ordinateur par des adaptateurs USB ; Node-RED les reçoit, les journalise, les affiche et les transmet au traceur. Dans un premier temps, **le sens principal des données est du matériel vers Node-RED**, pas l'inverse (principe 2).

Machine hôte : Mathieu travaille sous Windows. Un Raspberry Pi est une autre option, plus proche de ce qu'il y aurait à bord. Ce choix n'est pas fait (**À DÉCIDER**).

## 7. Plan de prise en main (PROPOSÉE, du plus simple au plus utile)

Chaque étape a un résultat qu'on peut vérifier, pour avancer en comprenant le « pourquoi ».

1. **Installer Node-RED sur la machine d'essai** en suivant la page officielle d'installation correspondante. *Vérification :* l'éditeur s'ouvre à `http://localhost:1880`.
2. **Premier flux sans matériel** : un nœud *inject* (qui envoie un message à la demande) relié à un nœud *debug* (qui affiche le message dans la barre latérale). *Vérification :* un clic sur *inject* fait apparaître le message dans *debug*.
3. **Simuler une phrase NMEA** : un nœud *inject* qui émet une phrase `RMC` ou `MWV` d'exemple, vers *debug*. *Vérification :* la phrase s'affiche telle quelle.
4. **Installer `node-red-node-serialport`** et lire un port série réel (un GPS USB, ou un Arduino qui renvoie du texte) avec *serial in*. *Vérification :* les phrases arrivent une par ligne dans *debug*.
5. **Parser une phrase** avec un nœud *function* (découper à la virgule, convertir) pour en tirer une valeur utile (par exemple l'angle de vent). *Vérification :* la valeur affichée correspond à la phrase brute.
6. **Journaliser** les messages dans un fichier horodaté. *Vérification :* le fichier se remplit et se relit.
7. **Relier à OpenCPN** par TCP (Node-RED serveur ou client) pour vérifier la liaison avec le traceur. *Vérification :* la position simulée bouge dans OpenCPN. C'est le point de contact avec les essais à terre de zones reportés (`essais/zones-opencpn-20261102/README.md`) : il ne se fait qu'à la reprise de ce chantier.
8. **Seulement ensuite**, essayer le rôle E (gardien en mode fantôme).

## 8. Gestion du travail (PROPOSÉE, non validée)

- Les flux de Node-RED sont enregistrés dans le dossier de l'utilisateur de Node-RED (par défaut `~/.node-red`, qui contient aussi `settings.js`). Les exporter régulièrement en fichiers JSON donne un historique et une sauvegarde.
- Le dépôt range déjà ses essais en dossiers datés, chacun avec un `README.md` et ses scripts (`essais/Q1-20261030/`, `essais/zones-opencpn-20261102/`). Les flux exportés pourraient suivre ce rangement (`essais/<nom>-<date>/`). Cette note ne crée aucun dossier ; le rangement est **À DÉCIDER** par Mathieu.
- **HYPOTHÈSE** : Node-RED offre aussi, d'après ma connaissance générale, une fonction « Projects » reliée à Git. Je ne l'ai pas vérifiée : à confirmer avant de l'adopter.
- Les mots de passe et jetons (Signal K, MQTT, etc.) ne doivent pas se retrouver dans les flux exportés vers le dépôt (principe général de prudence, non spécifique à Node-RED).

## 9. Statut des éléments de cette note

| Élément | Statut |
|---|---|
| Node-RED est l'outil du montage et du prototype | **PROPOSÉE** (DP-04, énoncée par Mathieu le 2026-11-07) |
| Description, licence, installation sur Pi, port 1880, sécurité `adminAuth`, nœuds série et Signal K | **CONFIRMÉ** par lecture de la documentation et des pages des paquets ; **NON EXÉCUTÉ** |
| Rôles A à E, principes de sécurité de la section 5, banc d'essai, plan de prise en main, rangement | **PROPOSÉE** par Claude, **À DÉCIDER** par Mathieu |
| Caractère temps réel de Node.js, XOR du total de contrôle, fonction « Projects » | **HYPOTHÈSE** (connaissance générale, non vérifiée dans cette session) |
| Nœud de zone (geofence) dans le paquet Signal K actuel, nœuds série préinstallés ou non, installation sous Windows, palette de tableau de bord | **À VÉRIFIER** |

## 10. Questions ouvertes

- Quel rôle (A à E) Mathieu veut-il donner à Node-RED en premier ?
- Sur quelle machine l'installer pour le banc d'essai (ordinateur Windows, Raspberry Pi) ? Quelle est la procédure d'installation locale sous Windows ?
- Node-RED seul, ou Node-RED avec un serveur Signal K (mode séparé ou intégré) ? Cela dépend du rôle B et de la source de zones choisie.
- Quelle palette de tableau de bord utiliser, et est-elle compatible avec la version de Node-RED installée ?
- Les scripts Python d'essai à terre restent-ils la référence, ou Node-RED prend-il le relais ?
- Un nœud de zone (geofence) existe-t-il dans la version actuelle des nœuds Signal K ? Ferait-il le travail de comparaison aux zones pour le mode fantôme ?
- Quel délai de réaction acceptable pour le gardien, et comment le mesurer avec Node-RED ?
- Node-RED reste-t-il à bord après le prototype (outil d'essai conservé) ou disparaît-il du système final ? Question à trancher plus tard.

## 11. Liens et sources

- Décisions : `conception/decisions-et-dispositions-2026-11-02.md` (DP-04, autorité). Zones : `conception/concept-evitement-zones-opencpn-2026-11-02.md`. Essais à terre (reportés) : `essais/zones-opencpn-20261102/README.md`. Girouette : `sources-brutes/point-clos-nmea-girouette-2026-11-02.md`. Dépôts open source : `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`. Anticipation par capteurs : `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`.
- Dépôt Node-RED : https://github.com/node-red/node-red
- Documentation officielle : « Getting started », « Raspberry Pi » et « Securing Node-RED » (nodered.org).
- Paquet `node-red-node-serialport` (npm et catalogue des flux Node-RED).
- Paquet `@signalk/node-red-contrib-signalk` (catalogue des flux Node-RED) ; ancien paquet `@signalk/node-red-embedded` (journal de modifications) ; plugin `@signalk/signalk-to-nmea0183` (npm) ; page d'installation de Signal K (signalk.org).
- Forum OpenMarine, fil « Using Signal K to modify NMEA data/sentences » (2024-03).
