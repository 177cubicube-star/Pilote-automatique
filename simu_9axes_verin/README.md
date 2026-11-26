# Banc simulé : centrale 9 axes, lecture Python, vérin et réglages de barre

**Statut : SIMULÉ.** Rien ici n'a touché de matériel. Bateau, vérin, bruits et
vagues sont des hypothèses ; les chiffres servent à **comparer des réglages
entre eux** et à trouver les pièges, pas à prédire le comportement du Capri 22.

## Ce que ce dossier permet

1. **Écrire dès maintenant le code qui lit l'ICM-20948**, et le tester sans la
   carte. Le lecteur (`icm20948_lecteur.py`) parle à un faux bus I2C qui imite
   `smbus2` octet pour octet. Sur le Raspberry Pi, on remplacera une seule
   ligne : `FauxBusI2C(puce)` → `smbus2.SMBus(1)`.
2. **Faire tourner la boucle complète** — vagues → bateau → centrale simulée →
   octets I2C → lecteur → fusion du cap → régulateur → vérin → barre → bateau.
3. **Comparer plusieurs réglages de barre** (PID en cascade et portage du
   pilote `basic` de pypilot) sur les mêmes scénarios, avec les mêmes tirages.

Place dans l'architecture DEC-014 : pypilot lit sa centrale lui-même. Ce banc
ne décide pas de remplacer cette lecture ; il prépare la chaîne de mesure, sert
d'outil de diagnostic au banc B1a, et donne un terrain pour régler avant la mer.
Il complète la ligne « Boucle fermée » du tableau 7 de CON-011, sans la
remplacer : là-bas, c'est le vrai pypilot et le vrai `motor.ino` qui tournent.

## La chaîne simulée

```
 bateau_sim ──force, rotations, champ──> icm20948_sim (puce + registres)
     ^                                        │  faux bus I2C (octets)
     │                                        v
     │                               icm20948_lecteur  ← le code qui ira sur le Pi
     │                                        │  m/s², °/s, µT (repère du bateau)
     │                                        v
     │                                   fusion_cap  (cap, lacet, gîte)
     │                                        │  20 fois par seconde
     │                                        v
  angle réel <── verin_moteur_sim <── u ── regulateurs (PID ou pypilot)
                       └── potentiomètre ──> angle mesuré, rendu au régulateur
```

| Fichier | Rôle |
|---|---|
| `icm20948_sim.py` | La puce : registres (banques 0 et 2), magnétomètre AK09916 en « bypass », sommeil, réinitialisation, bruit, biais, dérive, quantification, saturation, erreurs de bus |
| `icm20948_lecteur.py` | **Le code réel** : démarrage, vérification `WHO_AM_I`, lecture en bloc, conversion d'unités, changement de repère, calibration du magnétomètre, réessai sur erreur de bus |
| `fusion_cap.py` | Deux filtres au choix : **complémentaire** (simple) et **Mahony** (quaternion, biais du gyroscope sur trois axes, pondération de l'accéléromètre, compensation centripète). **Pas la fusion de pypilot** |
| `capteur_gite_sim.py` | Sources de gîte externes : inclinomètre du commerce, ou gîte « parfaite » (borne haute) |
| `bateau_sim.py` | Lacet de Nomoto, gîte et tangage, vagues (pilonnement, embardée), rafales, barre ardente, effet de la gîte sur le cap, bras de levier de la centrale |
| `verin_moteur_sim.py` | Vérin commandé en **vitesse** comme par `motor.ino` : rampe 0,2 s, butées, effort du safran, courant et coupure, jeu, potentiomètre 10 bits, vérin détaché |
| `regulateurs.py` | `pid_position` (cascade cap → angle → vitesse, bande morte, anti-emballement) et `pypilot_basic` (portage, repris de `simulations/pypilot_sim.py`) |
| `banc.py` | La boucle, les scénarios, les indicateurs, le journal CSV |
| `essais_pid.py` | Ligne de commande : réglages × scénarios × graines → tableau + CSV |
| `signalk_emetteur.py` | Transforme l'état du banc en messages Signal K (unités SI) et les envoie par UDP |
| `banc_signalk.py` | Fait tourner le banc **en temps réel** et le publie dans Signal K (lecture seule) |
| `nodered/alarme_ecart_cap.js` | **Logique de l'alarme d'écart de cap** (source unique), testée par `nodered/test_alarme_ecart_cap.js` |
| `nodered/flux_alarme_ecart_cap.json` | Flux Node-RED à importer, **généré** par `nodered/generer_flux_nodered.py` |
| `gains_pid.json` | **Les réglages à comparer — à modifier librement** |
| `test_simu_9axes.py` | 61 tests (octets, briques, filtres, boucle complète, cohérence du banc, Signal K, flux Node-RED) |

Bibliothèque standard de Python seulement : rien à installer.

## Lancer

Depuis ce dossier, dans un terminal (PowerShell ou celui de VS Code) :

```
python -m unittest -v test_simu_9axes      # les 61 tests, quelques secondes
python essais_pid.py --liste               # les scénarios
python essais_pid.py                       # tous les réglages, scénarios par défaut
python essais_pid.py --reglages pid_moyen,pypilot_defaut --scenarios vagues,rafales --graines 1,2,3 --journal
```

Ce qu'on doit voir : les tests finissent par `OK` ; `essais_pid.py` affiche un
tableau par scénario, classé du meilleur au moins bon, puis le chemin du CSV
écrit dans `resultats/`. Avec `--journal`, un CSV par passage (cap, barre,
vérin, 20 lignes par seconde) à ouvrir dans un tableur ou Node-RED.

## Choisir le filtre et la source de gîte

Pourquoi : l'erreur de **gîte** est la première cause d'erreur de **cap**. Le
champ magnétique plonge d'environ 69° ici ; si le filtre croit le bateau penché
alors qu'il ne l'est pas, il « voit » une partie de ce champ vertical comme
horizontale, et le nord calculé se décale (environ 2,5 fois l'erreur de gîte).

```
python essais_pid.py --reglages pid_moyen --scenarios vagues,rafales --graines 1,2,3,4,5 ^
                     --fusions complementaire,mahony --sources-gite imu,inclinometre,parfaite
python essais_pid.py --fusions mahony --accel-calibre --params-fusion "{\"kp_acc\": 0.1}"
```

| Option | Valeurs | Sens |
|---|---|---|
| `--fusions` | `complementaire`, `mahony` | Le filtre qui calcule gîte, tangage et cap |
| `--sources-gite` | `imu` | Verticale donnée par l'accéléromètre de l'ICM-20948 (aujourd'hui) |
| | `inclinometre` | Un inclinomètre du commerce, au même endroit. Il mesure lui aussi la force spécifique (gravité + accélérations) ; simulé sans biais |
| | `parfaite` | La gîte vraie du bateau simulé. **N'existe pas** : c'est la borne haute du gain possible |
| `--accel-calibre` | — | Biais de l'accéléromètre de 2 mg au lieu de 10 mg (hypothèses : calibré sur six faces avant montage, ou non) |
| `--params-fusion` | JSON | Gains du filtre, ex. `{"kp_acc": 0.25, "vitesse_ms": null}` |
| `--rodage-s` | secondes | Temps au quai avant chaque passage (défaut 60 s) |

Gains du filtre de Mahony : `kp_acc` (confiance dans l'accéléromètre : petit =
on croit davantage le gyroscope), `ki_acc` et `ki_mag` (vitesse d'apprentissage
des biais du gyroscope), `kp_mag` (confiance dans le magnétomètre pour le cap),
`seuil_ponderation_g` (au-delà de cet écart à 1 g, l'accéléromètre compte de
moins en moins), `vitesse_ms` (vitesse du bateau pour retirer l'accélération de
virage ; par défaut celle du bateau simulé, comme si le GPS la donnait).

### Ce que montre l'essai du 2026-11-26 (SIMULÉ, 5 graines, `pid_moyen`, scénario `vagues`)

Fichier complet : `resultats/sortie_gite_et_fusion_2026-11-26.txt`.

| Filtre | Source de gîte | Accéléro non calibré : p95 / cap estimé / gîte | Accéléro calibré : p95 / cap estimé / gîte | Vérin (calibré) |
|---|---|---|---|---|
| complémentaire | IMU | 2,55° / 1,78° / 0,91° | 1,66° / 1,00° / 0,68° | 107 mm/min |
| complémentaire | inclinomètre | 1,55° / 0,83° / 0,65° | idem | 105 mm/min |
| Mahony | IMU | 2,08° / 1,27° / 0,51° | **1,26° / 0,54° / 0,25°** | **59 mm/min** |
| Mahony | inclinomètre | 1,23° / 0,44° / 0,23° | idem | 58 mm/min |
| l'un ou l'autre | parfaite | 0,62 à 0,73° / 0,10 à 0,15° / 0 | idem | 55 à 58 mm/min |

Lecture, dans ce modèle :
- **Calibrer l'accéléromètre** est le gain le plus simple : un biais de 10 mg
  penche la verticale d'environ 0,6°, donc le cap d'environ 1,5°.
- **Mahony fait mieux que le filtre simple** partout, et le vérin travaille
  environ 45 % de moins (un cap estimé plus calme commande moins de barre inutile).
- **Un inclinomètre n'apporte presque rien** une fois l'accéléromètre de la
  centrale calibré (1,23° contre 1,26°) : il ne sait pas mieux qu'elle séparer
  la gravité des accélérations.
- Il reste un écart avec la gîte parfaite (1,26° contre 0,62°) : ce sont
  l'embardée et le bras de levier (hypothèses) qui trompent la verticale.
- `kp_acc` : meilleur entre 0,1 et 0,25 ici ; trop haut, les vagues passent ;
  trop bas, la dérive du gyroscope l'emporte.

## Corrections du banc (version 2, 2026-11-26)

Les résultats de la version 1 (`resultats/sortie_reference_2026-11-26.txt` et
`resultats/essais_pid_20261126-144833.csv`, s'ils sont encore là) sont
**périmés** : ils profitaient d'une compensation due au hasard. Référence
actuelle : `resultats/sortie_reference_2026-11-26_v2.txt`.

| Défaut trouvé | Effet | Correction |
|---|---|---|
| Biais de la centrale fixes, identiques pour toutes les graines | Le biais du gyroscope en roulis et celui de l'accéléromètre se compensaient par hasard dans le filtre simple | Biais tirés au hasard par graine (chaque graine = une autre carte) |
| Pilonnement appliqué sur l'axe vertical du **bateau** | Quand le bateau gîte, fausse inclinaison de la gravité | Pilonnement sur la verticale **terrestre** |
| Centrale supposée au centre de rotation, sans embardée | Verticale trop facile à trouver | Bras de levier (0,3 m au-dessus) et embardée de 0,5 m/s² (hypothèses) |
| Chaque passage commençait sans connaître les biais | On mesurait surtout le démarrage du filtre | Rodage de 60 s au quai avant chaque passage |
| Compensation centripète de Mahony avec la rotation du corps | Le tangage s'y mélangeait | Vitesse de variation du cap |

## Voir le banc dans Signal K

**Lecture seule.** Le banc publie ce que le pilote mesure et décide, pour
l'afficher dans Signal K et Node-RED. Rien ne revient de Signal K vers la barre :
dans l'architecture DEC-014, les ordres de barre vont directement au serveur de
pypilot (port 23322).

### 1. Le serveur Signal K

Sous Windows, la documentation officielle renvoie à l'installateur dédié :
[SignalK/signalk-server-windows](https://github.com/SignalK/signalk-server-windows)
(choisir un dossier comme `C:\signalk` plutôt que `Program Files`, comme il le
conseille). L'interface s'ouvre ensuite dans le navigateur, à l'adresse
`http://localhost:3000`.

### 2. Une connexion de données pour le banc

Dans l'interface d'administration, menu des connexions de données (*Data
Connections*), en ajouter une :

| Champ | Valeur |
|---|---|
| Type de données (*Data Type*) | `Signal K` |
| Source Signal K | `UDP` |
| Port | `55561` |
| Identifiant | `banc-simu` (au choix) |

Redémarrer le serveur si l'interface le demande. *Noms des menus à confirmer à
l'écran : je n'ai pas vu l'interface d'administration (voir « Vérifié »
ci-dessous).* La même connexion, écrite directement dans `settings.json` :

```json
{ "id": "banc-simu", "enabled": true,
  "pipeElements": [{ "type": "providers/simple",
    "options": { "logging": false, "type": "SignalK",
                 "subOptions": { "type": "udp", "port": "55561" } } }] }
```

### 3. Lancer le banc

```
python banc_signalk.py --scenario vagues --reglage pid_moyen --fusion mahony
python banc_signalk.py --scenario rafales --duree 600 --vitesse 2 --boucle
python banc_signalk.py --imprimer --duree 5 --vitesse 0        # sans serveur : affiche les messages
```

Options : `--vitesse` (1 = temps réel, 0 = au plus vite), `--frequence` (messages
par seconde, 5 par défaut, comme l'état envoyé à la façade dans CON-011),
`--hote` (le serveur est sur un autre ordinateur, par exemple le Pi),
`--source-gite`, `--accel-calibre`, `--duree`, `--boucle`.

Ce qu'on doit voir : dans le navigateur de données de Signal K (*Data Browser*),
les chemins ci-dessous, avec la source `banc-simu`, qui changent cinq fois par seconde.

### 4. Les chemins publiés

| Chemin Signal K | Contenu | Standard ? |
|---|---|---|
| `navigation.headingMagnetic` | Cap **estimé** par la fusion | oui |
| `navigation.rateOfTurn` | Lacet estimé (positif vers tribord) | oui |
| `navigation.attitude` | Gîte (`roll`), tangage (`pitch`), cap (`yaw`) estimés | oui |
| `steering.rudderAngle` | Angle de barre **mesuré** (potentiomètre) | oui |
| `steering.autopilot.target.headingMagnetic` | Consigne de cap | oui |
| `simulation.truth.*` | Cap, gîte et angle de barre **vrais** du bateau simulé | non (propre au banc) |
| `simulation.headingError` | Consigne − cap vrai | non |
| `simulation.actuator.*` | Commande `u`, courant (A), position de la tige (m) | non |

Unités SI de Signal K : radians, rad/s, ampères, mètres. Les chemins standard
sont ceux qu'un pilote réel publierait : un écran ou un flux Node-RED préparé
ici devrait servir tel quel avec pypilot, **à vérifier** sur les chemins que
pypilot publie vraiment. Le signe de `steering.rudderAngle` (positif = virer sur
tribord) est une hypothèse : la spécification lue ne le précise pas.

### Vérifié le 2026-11-26 (environnement de Claude, signalk-server 2.37.0)

- Le serveur reçoit les messages par la connexion UDP, les range sous le bateau
  courant (`self`) avec la source `banc-simu`, et les rend par son interface
  REST. Ses descriptions confirment les signes : gîte positive = penché sur
  tribord, tangage positif = nez qui monte.
- Le temps réel tient : 6 s simulées durent 6,07 s, rodage compris.
- Serveur absent ou éteint : le banc continue, sans erreur.
- **Pas vérifié** : l'interface d'administration et les écrans (l'installation
  de test ne les servait pas), Node-RED, Windows.

## Alarme d'écart de cap dans Node-RED (prototype du socle)

Le flux lit dans Signal K le cap (`navigation.headingMagnetic`), la consigne
(`steering.autopilot.target.headingMagnetic`) et, si un pilote le publie,
`steering.autopilot.engaged`. Il publie des **notifications** Signal K : il ne
commande rien.

### Comportement (PROPOSITION, à valider)

La grille des capacités demande « seuil et temporisation réglables ; tenir compte
d'une manœuvre volontaire ». DEC-017 ne couvre que les décrochages : cette alarme,
pilote toujours engagé, n'y entre pas. D'où cette proposition :

| Règle | Valeur par défaut | Réglage |
|---|---|---|
| Déclenche si l'écart dépasse le seuil pendant la temporisation | 20° pendant 20 s (temporisation de la référence ST4000+ ; seuil : hypothèse) | `SEUIL_DEG`, `TEMPORISATION_S` |
| S'éteint seule quand l'écart repasse sous seuil − hystérésis pendant le délai de retour (pas d'acquittement) | sous 15° pendant 5 s | `HYSTERESIS_DEG`, `RETOUR_S` |
| Manœuvre volontaire : après un changement de consigne d'au moins 5°, aucune nouvelle alarme tant que l'écart n'est pas revenu sous le seuil, au plus 120 s. Une alarme déjà active continue | 5°, 120 s | `MANOEUVRE_DEG`, `MANOEUVRE_MAX_S` |
| Cap absent : la consigne arrive encore, plus le cap | 3 s | `DONNEES_MAX_S` |
| Pilote non actif (plus de consigne depuis 5 s, ou `engaged` faux) : rien ne sonne, les alarmes se lèvent | 5 s | `CONSIGNE_MAX_S` |

Chemins des notifications : `notifications.steering.autopilot.heading` (écart :
nom normalisé de l'API pilote de Signal K) et
`notifications.navigation.headingMagnetic` (cap absent). État `alarm` avec son et
affichage, puis `normal`.

### Installer et importer

1. Dans Signal K, magasin d'applications (*Appstore*) : installer
   **signalk-node-red** (paquet `@signalk/signalk-node-red`), redémarrer le serveur.
2. Ouvrir Node-RED depuis Signal K (adresse `…/plugins/signalk-node-red/redAdmin`),
   menu ☰ → *Import* → choisir `nodered/flux_alarme_ecart_cap.json` → *Deploy*.
3. Lancer le banc : `python banc_signalk.py --scenario verin_detache`.
4. Ce qu'on doit voir : sous le bloc « Alarme écart de cap », un statut vert
   « veille », puis jaune « au-delà du seuil », puis rouge « ALARME écart de cap » ;
   dans la barre de débogage, le message de l'alarme ; dans Signal K, la
   notification sous `notifications.steering.autopilot.heading`.

Changer un réglage : double-clic sur le bloc « Alarme écart de cap », onglet
*Setup*, puis *Deploy*. Changer la logique : modifier `nodered/alarme_ecart_cap.js`,
lancer `node --test test_alarme_ecart_cap.js` (dans `nodered/`), puis
`python generer_flux_nodered.py`, et réimporter le flux.

Essai de « cap absent » : `python banc_signalk.py --scenario vagues --couper-cap-a 20`.

### Vérifié le 2026-11-26 (environnement de Claude : signalk-server 2.37.0, signalk-node-red 4.4.0, Node-RED 4.1.18)

- 14 tests de la logique (`node --test`) et 2 tests Python (flux à jour avec le code, fils valides).
- Flux déployé dans le vrai Node-RED de Signal K, banc en temps réel :
  - **vérin détaché à 60 s** : l'écart passe 20° vers 115 s, l'alarme apparaît
    entre 130 et 140 s, avec la source `alarme-ecart-cap` ; à l'arrêt du banc,
    elle se lève (« Pilote non actif ») ;
  - **cap coupé à 20 s** : alarme « cap absent » vers 23 s, l'alarme d'écart reste muette.
- Défaut trouvé et corrigé par cet essai : quand tout se tait en même temps, une
  fausse alarme « cap absent » durait environ 2 s.
- **Pas vérifié** : l'éditeur Node-RED à l'écran (déploiement fait par son
  interface de programmation), le son, Windows.

**À retenir :** dans ce scénario, l'alarme d'écart sonne **plus d'une minute**
après que la barre s'est détachée. Elle ne remplace pas le capteur ILS « vérin
détaché » de CON-011 : elle en est le filet.

## Tester un nouveau réglage

Ajouter une entrée dans `gains_pid.json` (ou dans une copie, avec `--gains`) :

```json
"mon_essai": {
  "_note": "kd plus fort pour amortir les vagues",
  "type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 3.0, "zone_integrale_deg": 5.0
}
```

puis `python essais_pid.py --reglages pid_moyen,mon_essai --graines 1,2,3`.
Une clé mal orthographiée arrête l'essai avec un message : une faute de frappe
ne passe jamais en silence.

### Ce que veulent dire les gains du `pid_position`

| Gain | Rôle, en clair | Unité |
|---|---|---|
| `kp` | Combien de barre pour chaque degré d'écart de cap | ° de barre / ° |
| `ki` | Corrige l'écart qui **reste** (barre ardente, gîte), lentement | ° de barre / (°·s) |
| `kd` | Freine la rotation du bateau, d'après le **gyroscope** (amortit) | ° de barre / (°/s) |
| `zone_integrale_deg` | L'intégrale ne se charge pas pendant un grand changement de cap (évite le dépassement) | ° |
| `bande_morte_deg` | Écart de barre toléré avant de bouger le vérin (évite qu'il « chasse ») | ° |
| `kp_position` | Vitesse du vérin selon l'écart de barre | 1 / ° |
| `angle_max_deg` | Barre maximale demandée | ° |

## Les indicateurs

| Colonne | Sens | Bon signe |
|---|---|---|
| `p95°` | 95 % du temps en route, l'écart de cap est sous cette valeur | ≤ 4° (cible du projet ±2 à 4°, ±5° dégradé) |
| `rms°`, `max°` | Écart moyen quadratique, écart maximal en route | petit |
| `dép.°`, `rép.s` | Dépassement et temps pour tenir ±2° après un changement de cap | petit |
| `est.°` | Erreur du cap **estimé** par la fusion : qualité de la chaîne de mesure | ≤ 1° |
| `mm/min`, `inv/min` | Course parcourue et changements de sens du vérin : **usure** | petit |
| `Wh/h` | Énergie du moteur seul (pas l'électronique) : pour Q-006 | petit |
| `sat%` | Temps passé commande à fond | petit |

Lire le p95 comme « la précision » du pilote est une **hypothèse de lecture**,
pas une règle décidée.

## Scénarios

| Nom | Ce qu'il éprouve | Par défaut |
|---|---|---|
| `calme_pas20` | Changements de cap de 20° en eau plate, barre ardente de 2° | oui |
| `vagues` | Clapot : lacet, roulis, tangage, pilonnement | oui |
| `rafales` | Rafales qui font gîter de 15°, la gîte fait remonter au vent | oui |
| `i2c_perturbe` | 5 % des transactions I2C en erreur | oui |
| `verin_lent` | Vérin deux fois plus lent (15 mm/s) | oui |
| `aimant_non_calibre` | 2,5 µT de « fer dur » non compensé, caps 0/90/180 : la **chaîne de mesure**, pas le réglage | non |
| `verin_detache` | La barre se détache à 60 s : le potentiomètre ne voit rien | non |

## Hypothèses à remplacer par du réel

| Hypothèse | Valeur | Remplacer par |
|---|---|---|
| Bateau (Nomoto) | T = 2,26 s, K = 0,19 /s (bateau de 12 m des simulations du 2026-10-28) | Virage à barre fixe sur le Capri 22 |
| Vitesse du vérin | 30 mm/s | Fiche du vérin choisi |
| Effort de calage, courants | 1500 N ; 0,8 A à vide, 8 A calé | Fiche du vérin |
| Effort du safran | 10 N par degré de barre | Mesure à la barre (EXP-003 ou en mer) |
| Bras de barre | 300 mm (→ ±30° pour 300 mm de course) | Calcul M1 et relevé EXP-003 |
| Jeu de l'attache | 1 mm | Montage réel |
| Bruits et biais de l'ICM-20948 | gyro : bruit 0,1 °/s, biais tirés (écart type 0,3 °/s), dérive 0,002 °/s/√s ; accéléro : bruit 2 mg, biais tirés (10 mg, 2 mg si calibré) ; magnéto 0,6 µT | Enregistrement de la vraie carte immobile |
| Accélérations qui trompent la verticale | embardée 0,5 m/s² ; centrale 0,3 m au-dessus du centre de rotation ; pilonnement 1 m/s² | **Hypothèse la plus influente sur la précision du cap** : enregistrer la centrale à bord (saison prochaine) |
| Champ magnétique | 53 µT, inclinaison 69° | Modèle WMM pour Sherbrooke et le plan d'eau |
| Registres de l'ICM-20948 et de l'AK09916 | écrits de mémoire de la fiche technique | **Relecture de la fiche DS-000189 et de celle de l'AK09916** |
| Axes du magnétomètre par rapport à l'accéléromètre | y et z inversés | Essai à la main sur la vraie carte |
| Adresse I2C de la carte Adafruit 4554 | 0x69 | Fiche Adafruit ou `i2cdetect -y 1` sur le Pi |

## Ce que ce banc n'est pas

- Ce n'est **pas pypilot** : ni sa fusion, ni son pilote réel (le terme I du
  pilote `basic` n'est pas porté), ni son étalonnage du servo.
- Pas de FIFO, de DMP, de filtres internes ni de maître I2C interne dans la puce simulée.
- Pas de LIS3DH, pas de girouette, pas de GPS : à ajouter le jour où ils servent.
- Le centre de rotation est fixe, et le bras de levier est le même pour le roulis et le tangage.

## Résultats de référence

`resultats/sortie_reference_2026-11-26_v2.txt` (réglages × scénarios par défaut,
trois graines) et `resultats/sortie_gite_et_fusion_2026-11-26.txt` (filtres ×
sources de gîte). Tous SIMULÉS.
