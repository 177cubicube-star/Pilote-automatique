# Q1 — Adaptateur pypilot de SailSim : modèle de vérin et coupure sûre (2026-10-30)

**Statut :** correctif **exécuté en tests unitaires** (interfaces simulées), **pas encore exécuté avec le vrai pypilot** (conteneur Docker). Lot Q1 de `Plan_execution_pilote_Capri22_V0-5` (vault).

**Base :** `herostrat/sailsim`, commit `ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0`. Correctif : `q1-adaptateur-pypilot.patch` (4 fichiers, +117 / −41 lignes). Rien n'a été proposé au dépôt d'origine.

## Ce que le correctif change

| Défaut (EXP-002, qualification V0.2) | Correction |
|---|---|
| QX-1 / Q1-A : `servo.command` était converti directement en angle de safran (`-cmd × rudder_max`) | `servo.command` est traité comme une **demande de vitesse** du vérin, comme dans pypilot (`servo.py` : `do_command(speed)`). La barre avance à `-cmd × rudder_rate_max`, intégrée sur le pas de temps, et s'arrête en butée à `rudder_max` |
| Q1-B : une commande constante imposait un angle constant | Une commande nulle maintient la barre où elle est ; une commande constante la fait avancer progressivement |
| QX-4 / Q1-E : en cas de perte de communication, la dernière commande était gardée sans limite | Après `comm_timeout` secondes de temps simulé sans pypilot, le vérin est arrêté et un **défaut verrouillé** (`fault`) est levé. Il ne se lève qu'avec `reset_fault()` (réarmement explicite) |
| `rudder_rate_max` accepté mais jamais utilisé | Utilisé comme vitesse du vérin ; exposé dans la configuration (`pypilot_rudder_rate_max_deg_s`, défaut 10 °/s) avec `pypilot_comm_timeout_s` (défaut 1 s) |

Les trois tests unitaires qui validaient l'ancien comportement sont remplacés par cinq tests (avance progressive, maintien à commande nulle, butée, coupure au-delà du délai, défaut verrouillé après reconnexion).

## Validation exécutée (2026-10-30)

- `pytest tests/unit tests/integration tests/scenarios` : **312 réussis, 0 échec**.
- Contrôles du CI du dépôt : `ruff check` réussi, `ruff format --check` réussi, `mypy` sans erreur.
- Environnement : Python 3.13.18, conteneur Linux de la session Claude.

## Ce qui reste à faire dans Q1

- **Q1-C / Q1-D, cap IMU** : le conteneur pypilot utilise toujours la route GPS (COG) à la place du cap IMU (`docker/pypilot/apply_patch.py`). Non corrigé ici.
- **Q1-F, horloge** : la synchronisation entre le temps simulé et le temps réel de pypilot n'est pas mesurée.
- **Q1-H, couche servo de pypilot** : impulsions « période / windup » et étalonnage non reproduits. C'est un banc **au niveau contrôleur**, avec un vérin idéal en vitesse.
- **Version de pypilot** : le Dockerfile clone toujours la tête de branche, sans commit figé (QX-5).
- **Essai de bout en bout** : construire l'image Docker et rejouer `pypilot_heading_hold` avec le profil `default`. Docker est disponible dans l'environnement de la session ; l'image n'a pas encore été construite.

## Appliquer le correctif

Dans un clone de `herostrat/sailsim` au commit ci-dessus : `git apply q1-adaptateur-pypilot.patch`.

## Tentative d'essai de bout en bout (2026-10-31) — interrompue

- **Docker** : le démon démarre dans l'environnement de la session, mais Docker Hub y est refusé par la liste de sites autorisés. L'image de base `python:3.11-slim` ne se télécharge pas.
- **Installation sans Docker** : pypilot `fdff88f` installé dans un environnement Python 3.11 isolé (dépendances PyPI, RTIMULib2 de `RTIMULib/RTIMULib2` comme dans le Dockerfile), correctif de simulation `apply_patch.py` et `pypilot_sim.conf` appliqués. pypilot démarre puis s'arrête : son processus IMU plante (`AttributeError: 'RTIMU.Settings' object has no attribute 'MPU925xAccelFsr'`, `boatimu.py:70`).
- **Nouveau constat (QX-6)** : pypilot exige le fork `seandepagnier/RTIMULib2` (`pyproject.toml:33`, `scripts/install_rtimulib.sh`). Le Dockerfile de SailSim installe `RTIMULib/RTIMULib2`. **Inférence** : avec pypilot `fdff88f`, le conteneur de SailSim plante de la même façon. Non vérifié dans Docker ; non testé avec des versions plus anciennes de pypilot.
- **Blocage** : l'installation du fork a été refusée deux fois par le contrôle de sécurité de l'environnement de la session (code externe), malgré l'accord de Mathieu. L'essai de bout en bout reste à faire, sur une autre machine.

## Q1-C/D et premier essai de bout en bout (2026-10-31)

La section précédente reste vraie pour ce qu'elle décrit ; le blocage est **contourné légitimement** par l'IMU virtuelle ci-dessous, qui ne demande plus le fork RTIMULib (le processus IMU matériel n'est plus lancé).

**Correctif complet :** `q1-adaptateur-pypilot-v2.patch` (7 fichiers, +331 / −43 lignes ; inclut et remplace `q1-adaptateur-pypilot.patch`, conservé pour l'historique). Vérifié applicable sur un clone propre de `ef1e293`.

### Ce que v2 ajoute à v1

- **Constat préalable (lecture du code pypilot `fdff88f`)** : sans IMU, pypilot met ses valeurs IMU à `False` (`boatimu.py:478`) ; le pilote `basic` lit `headingrate_lowpass` et `headingraterate_lowpass` pour ses termes D et DD (`pilots/basic.py:31-37`). Dans l'intégration d'origine de SailSim, **ces deux termes valaient donc zéro**.
- **IMU virtuelle** (`docker/pypilot/sim_imu_patch.py`, nouveau) : remplace le processus IMU matériel de pypilot par une IMU alimentée en UDP (port 20230) par l'adaptateur. pypilot recalcule lui-même cap, vitesse de lacet et leurs filtres, comme avec une vraie puce. Sans message pendant 1 s, l'IMU se déclare en panne.
- **Adaptateur** : envoie à chaque pas cap, vitesse de lacet et roulis ; règle `imu.heading_offset=0` à la connexion (une ligne dans `pypilot.conf` ne suffit pas : vérifié, la valeur restait à 90°). Activé par la configuration SailSim (`pypilot_imu_port`, défaut 20230) ; désactivé par défaut dans la classe.
- **Dockerfile** : fork `seandepagnier/RTIMULib2` (QX-6) et IMU virtuelle. **Non vérifié** : Docker Hub reste inaccessible depuis l'environnement de la session.

### Validation exécutée

- Tests : `pytest tests/unit tests/integration tests/scenarios` **315 réussis** ; `ruff check`, `ruff format --check`, `mypy` réussis.
- **Sonde IMU** (`bout-en-bout/sonde_imu.py`, vrai pypilot) : cap envoyé 117,9° → `imu.heading` 117,8° ; lacet 3,0 °/s → `imu.headingrate_lowpass` 3,0000 ; roulis 5° → 5,0° ; fréquence 19,8 Hz ; après arrêt de l'envoi, valeurs invalidées (`false`).
- **Environnement** : pypilot `fdff88f` installé sans Docker (Python 3.11, environnement isolé), correctif de simulation `apply_patch.py` d'origine + `sim_imu_patch.py`.

### Essai de bout en bout (**SIMULÉ**, vrai pypilot, profil `default`, scénario `pypilot_heading_hold`, 60 s, une exécution chacun)

| | Adaptateur d'origine | Adaptateur corrigé (v2) |
|---|---|---|
| Portes du scénario | PASS | PASS |
| Erreur de cap moyenne (porte) | 10,00° | 4,09° |
| Écart maximal | 13,75° | 16,13° |
| Vitesse de barre maximale | 17,42 °/s | 10,00 °/s (limite du vérin modélisé) |
| Cap moyen sur t > 30 s | −9,41° | +1,58° |
| Cap à t = 60 s | −8,81° | +0,25° |

**Lecture prudente :**
1. **Origine : erreur permanente d'environ −9°.** La route fond (cap + dérive ≈ −11,6°) n'est pas non plus à zéro : l'hypothèse « pypilot tient la route fond » est **réfutée**. **INFÉRENCE** : la commande de vitesse de pypilot, prise pour une position, perd son effet intégrateur ; avec 9,4° d'erreur, P et PR de `basic` donnent ≈ 1,3° de barre, du même ordre que les 1,5° observés. C'est la conséquence chiffrée de QX-1.
2. **Corrigé : le cap converge** vers la consigne (0,25° à 60 s), mais **part d'abord du mauvais côté** (+16° vers 10 s, barre jusqu'à +10,8°). **HYPOTHÈSE non vérifiée** : terme d'anticipation FF de pypilot déclenché par le saut de consigne à l'activation. À investiguer.
   *Note du 2026-10-31 (Q1-F) : cause trouvée et corrigée, voir la section Q1-F. Cette colonne « corrigé (v2) » provient d'une exécution touchée par le défaut de consigne décrit plus bas ; elle n'est plus représentative.*
3. **Une seule exécution par cas**, en temps réel : la gigue d'horloge (Q1-F) n'est pas mesurée, la répétabilité non plus. Les portes de ce scénario sont larges (15° d'erreur moyenne) et ne disent pas qu'un pilote est bon.

## Q1-F — répétabilité, horloge et départ du mauvais côté (2026-10-31)

**Correctif complet :** `q1-adaptateur-pypilot-v3.patch` (7 fichiers, +444 / −47 lignes ; inclut et remplace v2, conservé pour l'historique). Vérifié applicable sur un clone propre de `ef1e293`. SHA-256 : `bfd15493da34a46f791044ded4f1e82409b777ada3f3952dcc587daceb191b54`.

### Défaut découvert par la répétition

En rejouant l'adaptateur v2 cinq fois, les cinq exécutions ont divergé de la même façon (cap −69,7° à 60 s). Le journal pypilot montre `ap.heading_command = 270` alors que SailSim demande 0°.

- **Cause (lecture du code pypilot `fdff88f`, `autopilot.py` l. 274-304, `fix_compass_calibration_change`)** : quand `imu.heading_offset` change pendant que le pilote est engagé en mode compas, pypilot décale la consigne du même angle « pour garder la même route ». Notre réglage 90° → 0° à la connexion transformait donc 0° en 270°. Selon l'ordre dans lequel pypilot traitait les messages (décalage avant ou après `ap.enabled=true`), le défaut apparaissait ou non : c'est pourquoi une exécution isolée pouvait être bonne.
- **Départ du mauvais côté (`autopilot.py` l. 449-462)** : quand la consigne revient de 270° à 0°, pypilot voit un saut de +90° et son terme d'anticipation FF (signe inversé en mode compas, filtre à 10 % par itération) produit une impulsion : `servo.command` ≈ −4,8 puis décroissance sur ≈ 1,5 s, donc barre à tribord et cap qui monte de 5,7° à 17°. L'hypothèse « FF » de la section précédente était donc juste sur le mécanisme, mais le saut ne venait pas de l'activation : il venait de la compensation du décalage.

### Correctif v3 (adaptateur)

1. `imu.heading_offset=0` est envoyé **avant** `ap.enabled=true`, suivi d'une attente de 0,5 s (horloge murale, une seule fois par connexion ; paramètre `offset_settle_s`). Pilote encore désengagé, pypilot absorbe le changement sans toucher la consigne.
2. **Filet de sécurité** : l'adaptateur surveille aussi `ap.heading_command` et réaffirme la consigne de SailSim si pypilot en tient une autre (avertissement dans le journal). Seul, ce filet ne suffit pas : il recrée le saut vu par le FF (série « réaffirmation seule » ci-dessous).
3. Tests : 3 nouveaux (`TestHeadingCommandReassert` ×2, `TestOffsetBeforeEngage`), test du message `watch` mis à jour. `pytest tests/unit tests/integration tests/scenarios` **318 réussis** ; `ruff check` et `mypy` réussis. `ruff format --check` signale 2 fichiers, les mêmes sur le clone d'origine propre (préexistant, dont `apply_patch.py` laissé intact volontairement).

### Mesures (**SIMULÉ**, vrai pypilot, profil `default`, 60 s, 5 exécutions par série, métriques calculées par `q1f/q1f_run.py` sur le cap simulé)

| Série | Erreur moyenne \|cap\| | Écart max | Cap à 60 s | Barre max |
|---|---|---|---|---|
| Origine (`ef1e293`) | 8,92° (5/5) | 13,75–13,76° | −8,82 à −8,80° | 2,04° |
| v2 (décalage dans la rafale de connexion) | 33,81–33,98° | 69,66–69,81° | −69,81 à −69,66° | 1,55–1,56° |
| Réaffirmation seule | 5,20–5,36° | 16,67–17,09° | +0,21 à +0,23° | 9,99–10,37° |
| **v3 (décalage avant engagement)** | **0,77–0,78°** | **5,81°** | **−0,02°** | **2,93–2,94°** |

- **Répétabilité** : à l'intérieur de chaque série, dispersion ≤ 0,17° sur l'erreur moyenne. La seule exception connue est l'exécution isolée v2 faite avant la série (0,78°), qui n'avait pas subi le décalage : c'était la course entre messages, pas le hasard du simulateur.
- **v3** : la consigne tenue par pypilot reste 0,0000 du début à la fin (5/5), aucune réaffirmation déclenchée ; l'écart max 5,81° est l'écart initial (cap de départ 5,73°), sans dépassement du mauvais côté.
- **Horloge** (pas simulé 50 ms) : pas mural moyen 51,4–51,7 ms sur les 20 exécutions (≈ 3 % de lenteur, 60 s simulées en 61,7–62,5 s), écart type 0,4–2,8 ms, pire pas 56–144 ms. Aucune corrélation visible avec les résultats, puisque les séries restent répétables à 0,17° près malgré ces pointes. **INFÉRENCE** : la gigue n'est pas un facteur limitant à ce niveau, mais le banc n'est pas synchronisé (pypilot tourne sur sa propre horloge) ; un pire pas de 144 ms reste à surveiller pour des scénarios plus vifs.
- **Essai officiel rejoué avec v3** (`bout-en-bout/essai_bout_en_bout_final.sh`, sortie `final_corrige.*`) : portes PASS ; métrique de l'évaluateur SailSim `mean_heading_error_deg` 0,24° (v2 : 4,09°), `max_heading_deviation_deg` 1,18° (v2 : 16,13°), `max_rudder_rate_deg_per_s` 0,73 (v2 : 10,00). Attention : l'évaluateur et `q1f_run.py` ne calculent pas la même chose (sur le même fichier d'origine : 10,00° contre 8,92°) ; ne comparer que des chiffres de même source.

**Lecture prudente :** ces chiffres valent pour un seul scénario calme, le profil `default` (Q0 : GO conditionnel, pas le Capri 22) et un vérin idéal en vitesse. Ils montrent que la chaîne SailSim ↔ pypilot est maintenant cohérente et répétable ; ils ne qualifient pas un pilote pour le Capri 22.

Fichiers : `q1f/` (scripts `q1f_run.py`, `q1f_serie.sh`, bilans JSON des 20 exécutions, trajectoires et journaux pypilot représentatifs). Préfixes : `sans_reassert_` = v2, `reassert_seul_` = réaffirmation seule, sans préfixe = v3.

## Q1-G et Q1-H — passage par le nord et couche servo de pypilot (2026-10-31)

**Correctif complet :** `q1-adaptateur-pypilot-v4.patch` (8 fichiers, +728 / −48 lignes ; inclut et remplace v3, conservé). Vérifié applicable sur un clone propre de `ef1e293`. SHA-256 : `82b7759d6a02b61cf7c70a0f0e3297bcb667642a2e5691eab2885398c4dc38f8`.

### Constat de lecture (pypilot `fdff88f`, `servo.py`)

Sans contrôleur moteur sur un port série, `Servo.poll()` s'arrête tout de suite (`if not self.driver: return`) : `send_command()` et `do_command()` ne tournent **jamais**. Jusqu'à v3, le banc lisait donc `servo.command`, la sortie brute du pilote (une somme de gains **non bornée** : −4,8 et −5,6 observés), que l'adaptateur rognait à ±1. Toute la couche servo de pypilot était court-circuitée : gain et inversion (`servo.gain`), intégration « windup », période minimale entre inversions (`servo.period`, 0,4 s), vitesses min et max (`servo.speed.min/max`, 100 % par défaut), calibrage bâbord/tribord (`raw = cal[0] + |vitesse|·cal[1]`), drapeau SATURATED, blocage en butée.

### Ce que v4 ajoute

- **Contrôleur moteur simulé** (`docker/pypilot/sim_servo_patch.py`, nouveau) : remplace la carte Arduino, si bien que la couche servo de pypilot tourne **sans modification**. Il reproduit ce que rapporte le micrologiciel moteur (`arduino/motor/motor.ino`) : ENGAGED à la réception d'une commande, MIN/MAX_RUDDER_FAULT quand l'angle brut sort des bornes envoyées par pypilot (l. 1369-1386). L'angle de barre arrive de SailSim en UDP (port 20231), converti en lecture brute `angle / 100` pour que le calibrage d'angle de pypilot s'applique.
- **Adaptateur, mode `servo_layer`** (désactivé par défaut ; `pypilot_servo_layer` dans la configuration) : envoie l'angle de barre (positif = bâbord, convention pypilot), lit `servo.raw_command` (la commande réellement envoyée au moteur) et ne l'applique que si `servo.engaged` est vrai ; règle `rudder.range` sur la butée simulée.
- Dockerfile et docker-compose : patch et port 20231/udp ajoutés. **Non vérifié** (Docker Hub inaccessible).
- Tests : 4 nouveaux (`TestServoLayer`). `pytest tests/unit tests/integration tests/scenarios` **322 réussis** ; `ruff check`, `mypy` réussis.
- **Non reproduit** (limites) : rampes du micrologiciel (`max_slew_speed/slow`), courant, tension, température, surintensité, embrayage. Sans courant mesuré, pypilot lève son drapeau DRIVER_TIMEOUT pendant les mouvements (sans effet sur la commande).

### Essais (**SIMULÉ**, vrai pypilot, profil `default`, `q1gh/`)

| Essai | Réglage | Résultat observé |
|---|---|---|
| Q1-G, 359° → 1° (`g1_ideal`, `g1_servo`) | vérin idéal / couche servo | cap final 0,99° / −0,69°, plage −2,5…+1,0° / −4,3…+3,3° : chemin court, pas de grand tour |
| Q1-G, 1° → 359° (`g2_ideal`) | vérin idéal | cap final −1,05°, plage −2,7…+1,1° |
| H1, tenue de cap ×5 (`h1s_1…5`) | couche servo, défauts pypilot | erreur moyenne 1,67–1,80° (vérin idéal : 0,77°) ; cycle limite ±2,4–3,5° après 30 s ; commandes moteur seulement −1, 0, +1 ; 10–11 inversions, intervalle min 2,7–3,4 s |
| H2, saturation (`h2_sature`) | consigne 0° → 90° à 5 s | SATURATED à 5,33 s ; barre jusqu'à la butée simulée 30° ; **aucun drapeau de butée** (voir lecture 2) |
| H3, inversion (`h3_inverse`) | `servo.gain = −1` | commande inversée, cap −108° en 40 s : le gain servo agit sur toute la chaîne |
| H4, calibrage par défaut (`h4_calib`) | `servo.speed.min = 30` | 141/141 commandes conformes à `0,2 + 0,8·|vitesse|` (écart ≤ 0,0001) ; |vitesse| min 0,30 |
| H4b, calibrage personnalisé (`h4b_calib_fichier`) | fichier `servocalibration` bâbord [0,1 ; 0,9], tribord [0,3 ; 0,7] | 150/150 conformes (écart ≤ 0,0001) |
| H5, butée (`h5b_butee_inverse`) | gain −1, `rudder.range = 20` à 2 s | MAX_RUDDER_FAULT à 12,7 s ; barre arrêtée à 20,5° ; ensuite 0 commande moteur non nulle sur 369, alors que le pilote demande encore d'aller plus loin |

Contrôle de non-régression : mode vérin idéal rejoué deux fois avec le patch installé, 0,77° / cap −0,02° à 60 s, identique à Q1-F.

**Lecture prudente :**
1. **La couche servo change le comportement.** Avec les réglages par défaut de pypilot (vitesse min = max = 100 %), le vérin avance par impulsions à pleine vitesse et la tenue de cap devient un cycle limite d'environ ±3°. Le chiffre de 0,77° (vérin idéal) ne représente donc pas ce que ferait pypilot avec ses réglages par défaut. **HYPOTHÈSE à vérifier** : un `speed.min` plus bas réduirait ce cycle ; ce réglage dépendra du vérin réel (Q3).
2. **Butée = `range` exactement : pypilot pousse dans la butée.** pypilot ne lève le défaut que si l'angle **dépasse** `range` (30° > 30° est faux). Si la butée physique tombe pile sur `range`, le moteur continue d'être commandé contre elle ; sur le bateau, ce serait un pic de courant. **INFÉRENCE** : régler `range` un peu en deçà de la butée mécanique. À trancher au calibrage réel.
3. **Calibrage : `servo.calibration` n'est pas modifiable par JSON-TCP** (refus observé : la valeur reste à `false`, puis pypilot applique son défaut [0,2 ; 0,8]). Le chemin réel est le fichier `~/.pypilot/servocalibration`, vérifié en H4b.
4. **Répétabilité** : avec la couche servo, l'intégration windup dépend du temps mur de pypilot ; les 5 exécutions H1 ne sont plus identiques (erreur moyenne 1,67–1,80°, cap final −3,5…+2,1°), mais restent proches.
5. **Lecture de code non observée** : `Servo.poll()` ignore une lecture d'angle brut exactement nulle (`if self.driver.rudder:`) ; sans effet visible ici.

Type de banc (note de portée du plan) : **SIL contrôleur + couche servo pypilot**, sans micrologiciel moteur ni modèle électrique. Ce n'est pas encore un SIL système complet.

Fichiers : `q1gh/` (scripts `q1h_run.py`, `q1h_un.sh`, `verif_calib.py` ; trajectoires, journaux pypilot et bilans JSON).

## Image Docker construite et correctif v5 (2026-10-31)

**Constat de Mathieu (sur son poste, Docker Desktop)** : l'image `sailsim-pypilot:test` se construit au complet avec le Dockerfile v4 (16 étapes, dont le fork `seandepagnier/RTIMULib2` et les trois patchs). Version de pypilot clonée dans l'image : `fdff88ffe59c9014cead2a70451d0beca97dbeb1`, la même que celle des essais Q1. **Pas encore exécuté** : conteneur démarré et essai de bout en bout sous Docker.

**Défaut trouvé à la relecture et corrigé en v5** : les deux patchs écoutaient en UDP sur `127.0.0.1`. Docker relaie les ports publiés vers l'adresse réseau du conteneur, pas vers sa boucle locale : l'IMU virtuelle et l'angle de barre n'auraient jamais été reçus. Vérifié par analogie sans Docker (`q1gh/sonde_bind.py`) : avec une écoute `127.0.0.1`, un paquet envoyé à l'adresse réseau de la machine n'est pas reçu (`imu.heading = false`) ; avec `0.0.0.0`, il l'est (123,4° envoyés, 123,4° lus).

**Correctif v5** : `q1-adaptateur-pypilot-v5.patch` (8 fichiers, +743 / −50 lignes ; inclut et remplace v4, conservé). Vérifié applicable sur un clone propre de `ef1e293`. SHA-256 : `26f9f54366a5ccf76fb1f1bd4f57c0389df24fefa98e908fc9e77db5057b2ff2`.

- Adresse d'écoute UDP des deux patchs : variable d'environnement `SIM_UDP_BIND`, défaut `127.0.0.1` (installation locale) ; le Dockerfile la règle à `0.0.0.0`. Le journal de pypilot affiche maintenant l'adresse réelle (`sim imu: listening on udp ('0.0.0.0', 20230)`).
- Dockerfile : pypilot **fixé** sur `fdff88f` (`ARG PYPILOT_COMMIT`), au lieu de la dernière version. Le fork RTIMULib2 n'est pas fixé (commit non connu).
- Validation : 322 tests réussis, `ruff check` réussi ; non-régression sans Docker, défaut `127.0.0.1` : vérin idéal 0,78° (Q1-F : 0,77–0,78°), couche servo cap final +2,3°, 11 inversions, commandes −1 / 0 / +1.
- **Non vérifié** : la reconstruction de l'image avec v5 et l'essai de bout en bout sous Docker (à faire sur le poste de Mathieu).

### Reste à faire dans Q1 (au 2026-10-31)

- ~~Q1-F~~ et ~~transitoire de départ~~ : faits le 2026-10-31 (section Q1-F).
- ~~Q1-G~~ et ~~Q1-H~~ : faits le 2026-10-31 (section Q1-G et Q1-H). Restent hors banc : micrologiciel moteur (rampes), modèle électrique et surintensité.
- **Docker** : construire l'image avec le Dockerfile corrigé, sur une machine qui accède à Docker Hub.

