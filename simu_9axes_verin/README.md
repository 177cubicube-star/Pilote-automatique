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
| `vent_sim.py` | Vent réel (oscillation, bascules, rafales) et vent apparent au pont et en tête de mât (gîte, roulis) |
| `girouette_sim.py` | Girouette-anémomètre simulée qui émet de **vraies phrases NMEA 0183 `$WIMWV`** |
| `nmea_mwv.py` | **Le code réel** qui lit les phrases MWV et dit si le vent est encore frais |
| `mode_vent.py` | Mode vent apparent : consigne de cap tirée de l'angle de vent, corrections, secours compas |
| `essais_vent.py` | Ligne de commande : variantes du mode vent × scénarios de vent → tableau + CSV |
| `anticipation_vent.py` | **Anticipation de la barre par le vent (CON-009)**, apprise sur les 10 dernières minutes ; mode fantôme |
| `anticipation_vent.json` | Toutes ses constantes (CON-009 : dans un fichier, pas dans le code) |
| `essais_anticipation.py` | Ligne de commande : le vent forcit et tourne, avec ou sans anticipation → tableau + CSV |
| `voilure_sim.py` | **Banc honnête** : 7 profils de voiliers plausibles dont la physique diffère des hypothèses des algorithmes |
| `essais_robustesse.py` | Matrice de robustesse : profils × réglages × variantes, avec le pire cas |
| `signalk_emetteur.py` | Transforme l'état du banc en messages Signal K (unités SI) et les envoie par UDP |
| `banc_signalk.py` | Fait tourner le banc **en temps réel** et le publie dans Signal K (lecture seule) |
| `nodered/alarme_ecart_cap.js` | **Logique de l'alarme d'écart de cap** (source unique), testée par `nodered/test_alarme_ecart_cap.js` |
| `nodered/flux_alarme_ecart_cap.json` | Flux Node-RED à importer, **généré** par `nodered/generer_flux_nodered.py` |
| `gains_pid.json` | **Les réglages à comparer — à modifier librement** |
| `test_simu_9axes.py` | 95 tests (octets, briques, filtres, boucle complète, cohérence du banc, Signal K, flux Node-RED, vent, anticipation, banc honnête) |

Bibliothèque standard de Python seulement : rien à installer.

## Lancer

Depuis ce dossier, dans un terminal (PowerShell ou celui de VS Code) :

```
python -m unittest -v test_simu_9axes      # les 95 tests, une demi-minute
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
| complémentaire | IMU | 2,37° / 1,77° / 0,86° | 1,44° / 0,97° / 0,62° | 94 mm/min |
| complémentaire | inclinomètre | 1,32° / 0,80° / 0,59° | idem | 92 mm/min |
| Mahony | IMU | 1,99° / 1,26° / 0,50° | **0,99° / 0,45° / 0,21°** | **52 mm/min** |
| Mahony | inclinomètre | 0,90° / 0,34° / 0,19° | idem | 51 mm/min |
| l'un ou l'autre | parfaite | 0,58 à 0,69° / 0,09 à 0,12° / 0 | idem | 45 à 46 mm/min |

*Banc v4 (roulis réaliste). Avec le roulis exagéré des versions précédentes, les
écarts étaient plus grands (Mahony calibré : 1,26° au lieu de 0,99°) ; les
conclusions ci-dessous sont les mêmes.*

Lecture, dans ce modèle :
- **Calibrer l'accéléromètre** est le gain le plus simple : un biais de 10 mg
  penche la verticale d'environ 0,6°, donc le cap d'environ 1,5°.
- **Mahony fait mieux que le filtre simple** partout, et le vérin travaille
  environ 45 % de moins (un cap estimé plus calme commande moins de barre inutile).
- **Un inclinomètre n'apporte presque rien** une fois l'accéléromètre de la
  centrale calibré (0,90° contre 0,99°) : il ne sait pas mieux qu'elle séparer
  la gravité des accélérations.
- Il reste un écart avec la gîte parfaite (0,99° contre 0,58°) : ce sont
  l'embardée et le bras de levier (hypothèses) qui trompent la verticale.
- `kp_acc` : meilleur entre 0,1 et 0,25 (balayage fait sur le banc v3, **pas
  refait** en v4) ; trop haut, les vagues passent ; trop bas, la dérive du
  gyroscope l'emporte.

## Corrections du banc (versions 2 à 4, 2026-11-26)

Référence actuelle : `resultats/sortie_reference_2026-11-26_v4.txt`. Les fichiers
plus anciens, s'ils sont encore là, sont **périmés** : v1
(`sortie_reference_2026-11-26.txt`, `essais_pid_20261126-144833.csv`) profitait
d'une compensation due au hasard ; v2 avait le signe de l'ardeur faux ; v3 avait
un roulis en résonance.

| Défaut trouvé | Effet | Correction |
|---|---|---|
| Biais de la centrale fixes, identiques pour toutes les graines | Le biais du gyroscope en roulis et celui de l'accéléromètre se compensaient par hasard dans le filtre simple | Biais tirés au hasard par graine (chaque graine = une autre carte) |
| Pilonnement appliqué sur l'axe vertical du **bateau** | Quand le bateau gîte, fausse inclinaison de la gravité | Pilonnement sur la verticale **terrestre** |
| Centrale supposée au centre de rotation, sans embardée | Verticale trop facile à trouver | Bras de levier (0,3 m au-dessus) et embardée de 0,5 m/s² (hypothèses) |
| Chaque passage commençait sans connaître les biais | On mesurait surtout le démarrage du filtre | Rodage de 60 s au quai avant chaque passage |
| Compensation centripète de Mahony avec la rotation du corps | Le tangage s'y mélangeait | Vitesse de variation du cap |
| **(v3)** Signe de l'effet de la gîte sur le cap inversé : le bateau gîté **abattait** au lieu de remonter au vent | Le scénario `rafales` était incohérent ; la conclusion « sans intégrale, hors cible » en dépendait | Signe corrigé, et barre ardente de `rafales` du même côté que la gîte. La conclusion tient de nouveau (p95 de 4,5°, « dégradé ») |
| **(v4)** Roulis en **résonance** : vagues autour de 3 s, période propre de 3 s, amortissement 0,15 | Roulis d'écart type 11° et pointes à ±29° dans `vagues` (±50° au grand largue). Il exagérait les erreurs de gîte et surtout le balancement de la tête de mât | Amortissement 0,5 (hypothèse : voiles et quille amortissent) : écart type 4°, pointes à ±11°. **Conclusions changées** : mode vent et anticipation (sections ci-dessous) ; réglages PID et gîte : mêmes conclusions |

## Mode vent apparent (windvane électronique)

Cadre : DEC-005 (acceptée) — mode vent, girouette-anémomètre **électronique** en
NMEA 0183, validité du vent avec retour au compas et alerte, correction de la gîte
et du mouvement, jamais de virement ni d'empannage déclenché par le pilote.

### La chaîne simulée

```
vent réel ──> vent apparent en tête de mât (gîte, roulis × 8,5 m) ──> girouette simulée
                                                                          │ phrases $WIMWV (4 Hz)
                                                                          v
                         consigne de cap <── mode_vent <── nmea_mwv (le code réel)
                               │
                               v
                  régulateur de cap habituel (PID ou pypilot) ──> vérin ──> bateau
```

Le mode tient un **angle de vent apparent** (positif tribord, négatif bâbord,
comme Signal K). Il ne commande pas la barre directement : il transforme l'angle
en **consigne de cap**, que suit le régulateur de cap. Le cap et le gyroscope
gardent ainsi leur rôle d'amortissement.

- **Direction du vent** : `cap + angle`, calme même quand le bateau lacet, puis
  filtrée (`tau_s`, 3 s par défaut).
- **Consigne de cap** : `direction filtrée − angle voulu`.
- **Correction de la gîte et du mouvement du mât** (disposition 14), activée par
  défaut. La vitesse de la tête de mât est calculée depuis le gyroscope ; elle est
  **amortie comme la girouette amortit sa mesure** (`amortissement_capteur_s`).
- **Vent perdu** (disposition 12) : plus de phrase valide depuis `age_max_s`
  (2 s), alors retour au compas sur la dernière consigne de cap et alarme. Il n'y a
  **pas de retour automatique** au mode vent : il faut le redemander. *Proposition,
  à valider.*
- **Jamais de changement de bord** (disposition 15) : passer d'un angle tribord à
  un angle bâbord est refusé. Si le vent tourne, le bateau tourne avec lui du même
  bord.

Ce n'est **pas** le mode vent de pypilot, qui a ses modes *Wind* et *True Wind*,
non portés ici.

### Lancer

```
python essais_vent.py                                    # 5 variantes × 5 scénarios, 3 graines
python essais_vent.py --scenarios vent_arriere --params-mode-vent "{\"tau_s\": 6}"
python banc_signalk.py --scenario vent_pres              # en direct dans Signal K
```

### Ce que montre l'essai du 2026-11-26 (SIMULÉ, 3 graines)

Fichier complet : `resultats/sortie_mode_vent_2026-11-26.txt`. Écart entre l'angle
de vent apparent vrai et l'angle voulu (moyenne quadratique) et course du vérin :

| Variante | Près 40° | Travers 90° | Grand largue 150° |
|---|---|---|---|
| Sans correction | 2,7° · 537 mm/min | 4,2° · 582 mm/min | 5,4° · 1092 mm/min |
| Correction, sans amortissement assorti | 2,4° · 357 mm/min | 4,1° · 415 mm/min | 3,5° · 698 mm/min |
| **Correction, amortissement assorti (défaut)** | **2,5° · 124 mm/min** | **4,0° · 185 mm/min** | **3,2° · 167 mm/min** |
| Défaut, filtre de 10 s | 3,0° · 81 mm/min | 4,3° · 100 mm/min | 4,1° · 112 mm/min |

Pour comparer, en mode compas dans les mêmes vagues, le vérin parcourt environ
96 mm/min. *Banc v4. Avec le roulis exagéré du banc v3, l'erreur sans correction
paraissait bien pire (22,3° au grand largue).*

Lecture, dans ce modèle :
- **La correction de la tête de mât sert surtout le vérin.** Avec un roulis
  réaliste, l'angle sans correction reste correct au près et au travers (2,7° et
  4,2°) et se dégrade au grand largue (5,4°) ; mais le vérin court 4 à 6 fois plus,
  parce que chaque coup de roulis balance la tête de mât (8,5 m de haut) et fait
  osciller la consigne.
- **Il faut corriger au même rythme que le capteur.** La girouette amortit sa
  mesure ; retirer le mouvement du mât *de l'instant présent* garde l'angle à peu
  près juste mais laisse le vérin courir 2 à 4 fois plus. D'où le paramètre
  `amortissement_capteur_s`, à relever sur la fiche du capteur choisi ou à mesurer.
- **Le filtre règle le compromis** entre la précision de l'angle et le travail du
  vérin : de 3 s à 10 s, on perd 0,3 à 0,9° et on divise la course du vérin par 1,5 à 1,9.
- **Bascule de 20°** : le bateau suit en une vingtaine de secondes, sans jamais
  changer de bord (0 passage). **Girouette muette** : alarme à 62 s (coupure à 60 s
  plus 2 s), puis cap tenu au compas.

### Hypothèses propres au vent

| Hypothèse | Valeur | Remplacer par |
|---|---|---|
| Hauteur de la tête de mât au-dessus du centre de rotation | 8,5 m | Mesure sur le Capri 22 |
| Girouette | 4 phrases/s, amortissement 0,3 s, bruit 1° et 0,1 m/s | Fiche du capteur choisi |
| Vitesse du bateau | constante, 2,5 m/s, quelle que soit l'allure | Polaire ou loch |
| Gîte due au vent | 18° de travers pour 7 m/s apparents, en carré de la vitesse | Journal à bord |
| Vent | 6 m/s (7 au grand largue), oscillation ±5° sur 90 s, rafales ±15 % | — |

## Anticipation de la barre par le vent (CON-009), apprise sur 10 minutes

### Ce qu'on teste

Quand le vent forcit, le bateau gîte et cherche à remonter au vent. Le régulateur
ne corrige qu'après l'écart. L'anticipation **prépare l'angle de barre** dès que
le vent change, d'après ce qu'elle a appris dans les **10 dernières minutes** :

1. une fois par seconde, en **régime établi** (lacet, écart de cap et variation du
   vent faibles), elle note l'angle de barre tenu et le vent (vitesse²) ;
2. elle en tire la « barre habituelle » pour chaque vent, par moindres carrés,
   dans la tranche d'angle du **vent de base** (comme la table `Cn` de Fenix) ;
3. dès que le vent s'écarte de sa moyenne lente (60 s), elle calcule l'écart de
   barre à préparer, **borné à ±10°**.

Conforme à CON-009 : vent filtré sur 1 s, seuils 0,6/0,4 m/s, constantes dans
`anticipation_vent.json`, garde-fous avec motif (vent absent, trop vieux, hors
plage, saut brutal, vent faible, modèle insuffisant, veille), journal d'une ligne
par cycle, et **mode fantôme qui n'agit jamais** (vérifié par un test : mêmes
chiffres qu'« aucune »).

**Écart à CON-009, signalé :** l'anticipation reçoit le vent **corrigé de la gîte
et du mouvement du mât** (même correcteur que le mode vent). CON-009 prévoyait
cette correction « plus tard ». Au banc, sans elle, la vitesse du vent saute à
chaque coup de roulis : 1195 « sauts brutaux » en 15 minutes, et le modèle n'est
jamais prêt.

**Au banc seulement :** la variante `active` ajoute la correction à l'angle de
barre voulu du PID, pour mesurer le gain possible. Ce n'est **pas** la version 2
de CON-009, qui demande ta décision explicite et bute sur un point ouvert : pypilot
n'a pas d'entrée pour une correction de barre. Avec `pypilot_basic`, la variante
active est refusée.

### Lancer

```
python essais_anticipation.py
python essais_anticipation.py --scenarios renfort_compas --journal      # journal CON-009 (fantôme)
```

### Ce que montre l'essai du 2026-11-26 (SIMULÉ, 3 graines)

Fichier complet : `resultats/sortie_anticipation_2026-11-26.txt`. Écart maximal
pendant les séquences (cap en mode compas, angle de vent en mode vent) et course
du vérin :

| Scénario | Aucune (= fantôme) | Active | Active + angle |
|---|---|---|---|
| Mode compas, bateau peu ardent (0,15), bascules | 2,11° · 65 mm/min | 2,01° · 67 | 1,97° · 67 |
| Mode compas, **bateau ardent** (0,40), bascules | 3,41° · 90 | **2,73° · 96** | 2,52° · 93 |
| Mode compas, bateau ardent, **sans bascule** | 3,27° · 89 | **2,05° · 94** | 2,01° · 91 |
| Mode vent à 40°, bascules | 11,6° · 133 | 11,9° · 173 | 9,7° · **328** |

Le modèle est prêt vers 165 s (moyenne des graines), bien avant la première
séquence (620 s). *Banc v4 (roulis réaliste).*

Lecture, dans ce modèle :
- **L'anticipation ne sert que si le coup de vent pèse vraiment sur la barre.** Sur
  un bateau peu ardent, la barre ne bouge que d'environ 1° : le PID s'en charge
  seul. Sur un bateau ardent, l'écart maximal baisse de 37 % sans bascule et de
  20 % avec, pour 6 % de course de vérin en plus.
- **L'option `modele_angle` gagne ici, mais n'est pas robuste.** Sur ce banc, dont
  la physique a la forme du modèle, elle prévoit bien la bascule (0,46° d'erreur
  au lieu de 2,1°) et l'écart baisse de 26 %. Sur les bateaux du banc honnête,
  elle perd au pire cas (section suivante). Elle reste désactivée. *Sur le banc v3,
  au roulis exagéré, elle ne gagnait même pas ici : le bruit noyait l'effet de l'angle.*
- **En mode vent, elle n'aide pas.** L'écart vient surtout de la direction du vent,
  que le bateau doit suivre. Avec l'angle, elle devient une seconde boucle de vent
  nerveuse : prévision fausse de 9,8°, vérin 2,5 fois plus sollicité.
- **Meilleur cas.** Ce tableau utilise un modèle de la même forme que la physique
  du simulateur. La section suivante, le banc honnête, est le vrai test.
- **L'ardeur du Capri 22 est inconnue.** Le mode fantôme en mer (CON-009,
  essai 4) dira si l'on est plus près du cas « peu ardent » ou du cas « ardent ».

## Banc honnête (étape 1 du travail en profondeur)

### Pourquoi

Un algorithme qui apprend la même loi que celle du simulateur paraît toujours bon.
Pour comparer des algorithmes, la physique doit **différer** de leurs hypothèses,
et un bon algorithme doit tenir sur **plusieurs** bateaux plausibles. On juge sur
le **pire cas**, pas sur la moyenne.

### Les profils (`voilure_sim.PROFILS`, hypothèses plausibles, aucune mesurée)

| Profil | Ce qui change par rapport à l'hypothèse des algorithmes |
|---|---|
| `reference` | Rien : physique du banc v3. **Contrôle** : redonne les mêmes chiffres au milliardième (test) |
| `ardent` | Ardeur 0,40 (au lieu de 0,15) |
| `ardeur_progressive` | L'ardeur grandit avec la gîte : 0,20 à plat, 0,60 à 20° |
| `gite_lente` | Ardent ; la force dans les voiles s'établit en 3 s |
| `voiles_irregulieres` | Gîte selon une table irrégulière (pas \|sin\|) et couple direct des voiles selon l'angle |
| `polaire` | La vitesse suit le vent et l'allure ; le safran pousse en vitesse² |
| `tout` | Tout à la fois : environ 9° de barre ardente en permanence |

Lancer : `python essais_robustesse.py` (une dizaine de minutes ; options
`--profils`, `--reglages`, `--variantes`, `--graines`).

### Ce que montre la matrice du 2026-11-26 (SIMULÉ, banc v4, 3 graines, `renfort_compas`)

Fichier complet : `resultats/sortie_robustesse_2026-11-26.txt`. Écart maximal
pendant les renforcements :

| Profil | `pid_moyen` sans anticipation | `pid_moyen` + anticipation | Sans zone d'intégrale, sans | Sans zone + anticipation | Sans zone + anticipation avec angle |
|---|---|---|---|---|---|
| reference | 2,11° | 2,01° | 2,11° | 2,01° | 1,97° |
| ardent | 3,41° | 2,73° | 3,41° | 2,73° | 2,52° |
| ardeur_progressive | 5,60° | 4,35° | 5,55° | 4,34° | 3,65° |
| gite_lente | 3,18° | 2,80° | 3,18° | 2,80° | 2,76° |
| voiles_irregulieres | 3,23° | 2,58° | 3,23° | 2,58° | 2,60° |
| polaire | 2,51° | 2,23° | 2,51° | 2,23° | 2,23° |
| **tout** | **12,47°** | **12,47°** | 5,35° | 4,52° | 4,75° |
| **Pire cas** | **12,47°** | **12,47°** | 5,55° | **4,52°** | 4,75° |

Lecture, dans ce modèle :
- **Le banc honnête a trouvé un piège dans le PID.** La zone d'intégrale de 5° (qui
  évite le dépassement lors d'un changement de cap) **gèle l'intégrale pour
  toujours** dès que la barre ardente demande plus de `kp × zone` = 6° de barre :
  le proportionnel seul laisse alors plus de 5° d'écart. Sur `tout`, cela donne un
  écart permanent d'environ 10° (p95 11,8°). Sans zone, le même bateau est tenu
  (p95 4,5°). Le plafond de l'intégrale (`i_max_deg`) n'y est pour rien (essayé à
  15° : même résultat). **À corriger en premier à l'étape 2.**
- **L'anticipation par la vitesse du vent tient sur tous les bateaux** : 11 à 22 %
  d'écart maximal en moins sur les profils qui en ont besoin, presque rien sur la
  référence, jamais pire. Coût : 3 à 16 % de course de vérin en plus.
- **Elle ne peut pas apprendre si le pilote ne tient pas le cap** : sur `tout` avec
  la zone d'intégrale, aucun point n'est en régime établi (écart de plus de 4°) et
  le modèle n'est jamais prêt.
- **L'option `modele_angle` n'est pas robuste** : meilleure sur les bateaux dont la
  physique ressemble à son hypothèse, moins bonne sur `tout` (4,75° contre 4,52°).
- **La prévision reste médiocre** : souvent du même ordre que le changement de
  barre réel (par exemple 2,5° prévus de travers pour 3,2° tenus sur `gite_lente`).
  L'anticipation aide par sa direction et son instant, pas par sa justesse. C'est
  la piste de l'étape 2 (autres algorithmes : moindres carrés récursifs,
  observateur de perturbation).

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
| `environment.wind.angleApparent`, `…speedApparent` | Vent apparent **mesuré** par la girouette (scénarios de vent) | oui |
| `steering.autopilot.target.windAngleApparent` | Angle de vent voulu (mode vent) | oui |
| `simulation.truth.wind*`, `simulation.autopilot.mode` | Vent vrai ; mode `vent` ou `compas_secours` | non |

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
| `vent_pres`, `vent_travers`, `vent_arriere` | **Mode vent** à 40°, 90° et 150° tribord | non (`essais_vent.py`) |
| `vent_bascule` | Mode vent ; le vent tourne de 20° à 60 s : le bateau doit suivre | non (`essais_vent.py`) |
| `vent_perdu` | Mode vent ; la girouette se tait à 60 s : secours compas attendu | non (`essais_vent.py`) |
| `renfort_compas`, `renfort_compas_ardent`, `renfort_compas_ardent_sans_bascule`, `renfort_vent` | 10 min d'apprentissage, puis 4 séquences où le vent forcit de 35 % en tournant | non (`essais_anticipation.py`) |

## Hypothèses à remplacer par du réel

| Hypothèse | Valeur | Remplacer par |
|---|---|---|
| Bateau (Nomoto) | T = 2,26 s, K = 0,19 /s (bateau de 12 m des simulations du 2026-10-28) | Virage à barre fixe sur le Capri 22 |
| Amortissement du roulis | 0,5 (0,15 jusqu'à la v3 : résonance) | Enregistrement du roulis à bord |
| Effet du vent sur le bateau | 7 profils plausibles (`voilure_sim.py`) | Mode fantôme en mer : ardeur, retard, polaire |
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

Banc v4 : `resultats/sortie_reference_2026-11-26_v4.txt` (réglages × scénarios
par défaut, trois graines), `sortie_gite_et_fusion_2026-11-26.txt` (filtres ×
sources de gîte), `sortie_mode_vent_2026-11-26.txt` (mode vent),
`sortie_anticipation_2026-11-26.txt` (anticipation) et
`sortie_robustesse_2026-11-26.txt` (banc honnête). Tous SIMULÉS.
