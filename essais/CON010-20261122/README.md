# Essais SailSim du 2026-11-22 — pilote `absolute`, `servo.speed.min` et séquences de manœuvre (SIMULÉ)

Deux séries faites sur le **banc Q1 v5 sous Docker** (voir `../Q1-20261030/bout-en-bout-docker/README.md`) :
image `sailsim-pypilot:test`, pypilot `fdff88f`, conteneur `pp`, configuration d'autopilote `pypilot_servo` (couche servo), bateau SailSim `default` (**pas le Capri 22**). Une seule exécution par cas.

Note du vault liée : `05 - Concepts/CON-010 - Séquences de manœuvre programmables (virement et empannage).md` (analyse complète).

## 1. `absolute-speedmin/` — pilote `basic` ou `absolute` × `servo.speed.min` 100 % ou 30 %

Scénario `pypilot_heading_hold`. Script : `essai.py` (4 cas, conteneur redémarré entre chaque). Mesures après 15 s :

| Cas | Erreur de cap moyenne | max | Barre (min…max) | Course totale de barre |
|---|---|---|---|---|
| basic, min 100 % (défaut) | 1,73° | 3,50° | −1,5…3,0° | 26° |
| **basic, min 30 %** | **0,71°** | 2,07° | 0…3,7° | 31° |
| absolute, min 100 % | 3,43° | 8,65° | −10,5…18,5° | 268° |
| absolute, min 30 % | 2,86° | 6,49° | −8,4…12,5° | 231° |

- Baisser `servo.speed.min` supprime le cycle limite ±3° observé en Q1 (le défaut 100/100 % fait un mouvement tout-ou-rien).
- `absolute` oscille avec ses gains par défaut (`servo.position.p/i/d` = 0,1 / 0 / 0,01) : réglage à faire avant de l'utiliser.
- Au démarrage, `absolute` retombe sur `basic` tant que l'angle de barre n'est pas valide ; le script réimpose `ap.pilot=absolute` dès qu'il l'est (vers 8 s).

## 2. `sequences/` — preuve de concept CON-010

Lecteur de séquences = client JSON-TCP de pypilot (`banc.py` + `sequences.py`) : pilote en veille, chaque étape règle `servo.speed.max` puis `servo.position_command`, fin d'étape sur durée, passage du vent ou cap tourné ; ensuite retour au pilote `basic`. Réglage commun `servo.speed.min` = 30.

**Calibration** (`calib.py`, `calib2.py`, scénario `pypilot_heading_hold`) :
- `servo.speed.max` se modifie par le réseau (valeur relue).
- `calib` : en veille, `servo.position_command` **ne bouge pas** la barre. Cause lue dans `servo.py` : en veille, `do_command` remet le « windup » à zéro alors que `command.use_period` reste vrai (posé par `command.command(0)`), donc vitesse 0.
- `calib2` : contournement `servo.command=0` (envoyé par le réseau) juste avant `position_command` → barre à 9,2° pour 10° demandés. Angle pypilot **positif = virage à bâbord**.

**Série 1** (`sequences.py`, voiles fixes à 0,5) :

| Cas | Entrée ±5° du nouveau cap | Stable ±5° | Course de barre |
|---|---|---|---|
| Empannage natif (saut de consigne) | 33 s | 38 s | 118° |
| **Empannage en séquence** | **14 s** | **21 s** | **89°** |
| Virement natif | jamais (arrêt bout au vent) | — | — |
| Virement en séquence | jamais (cap +15° puis arrêt) | — | — |

**Série 2** (`sequences2.py`, voiles réglées par `auto_sail_trim`, config `pypilot_servo_voiles.toml`) :

| Cas | Cap atteint (cible +50°) |
|---|---|
| Virement natif | +1° |
| Séquence, lancement 15° | +14° |
| Séquence, lancement 25° | +13° (barre réellement atteinte : 19°, vérin trop lent pour 4 s) |
| Témoin : pilote Nomoto interne de SailSim, barre 30° (`temoin_nomoto_virement.csv`) | +23°, puis arrêt |

**Lecture** : l'empannage en séquence fonctionne. Le virement **ne peut pas être jugé sur ce banc** : même le pilote interne de SailSim ne termine pas ce virement avec le bateau `default`.

> **Correction du 2026-11-23 (relecture de `temoin_nomoto_virement.csv`) : la lecture ci-dessus est fausse pour le témoin.** « +23° » est le cap à 60 s. Le témoin **réussit** : vent apparent passé sur l'autre bord, entrée à ±5° du nouveau cap à 75,25 s (45 s après la commande), `u` remontée à 5,4 m/s. Il garde la barre à 29,8° jusqu'à un vent apparent d'environ −26° ; les séquences ramenaient la barre au centre bout au vent. Suite : `../CON010-virement-20261123/`. Les portes de qualité de SailSim échouent pour tous les cas, natifs compris ; elles ne servent pas à juger ici.

## `sailsim-auto-sail-trim.patch`

Modification du clone local `sailsim-test` pour la série 2 : option `auto_sail_trim` (désactivée par défaut) dans l'adaptateur pypilot, même calcul que le pilote Nomoto interne. S'applique **par-dessus** `../Q1-20261030/q1-adaptateur-pypilot-v5.patch`. Vérifié : `git apply --check -R` passe sur le clone. Non vérifié : tests unitaires et `ruff` de SailSim (absents du `.venv`).

## Rejouer

Prérequis : conteneur `pp` construit (voir Q1), clone `C:\Users\mat_g\Documents\sailsim-test` avec v5 (+ ce correctif pour la série 2), `pypilot_servo_voiles.toml` à côté des scripts.

```powershell
python absolute-speedmin\essai.py
python sequences\calib2.py
python sequences\sequences.py
python sequences\sequences2.py
```

Lancer avec `python` (pas `python -I`) : les scripts importent `banc.py` depuis leur dossier. Ils écrivent leurs résultats à côté d'eux.

## Limites

Simulation seulement ; un passage par cas ; bateau générique ; valeurs de séquence d'exemple ; vérin simulé à 10 °/s au maximum. Les fichiers `*_console.txt` contiennent des accents mal encodés (sortie console Windows), sans effet sur les données.
