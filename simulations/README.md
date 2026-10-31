# Simulations de référence — Fenix / pypilot (2026-10-28)

**Statut :** archive de référence (décision L-8 de Mathieu, 2026-10-30). Ces scripts sont la source des preuves `ARCH:S-01` à `ARCH:S-09` du document `conception/architecture-pilote-proposition-2026-10-28.md`. Ils ne remplacent pas SailSim, qui reste le banc principal (Plan V0.5).

**Nature des résultats :** tout ce que ces scripts produisent est **SIMULÉ**. Ils tournent sur un bateau hypothétique de 12 m (Nomoto T = 2,26 s, K = 0,19), pas sur le Catalina Capri 22, et avec un vérin, des bruits et des perturbations supposés. Ils n'exécutent ni le firmware Fenix ni le logiciel pypilot : ce sont des **portages Python** écrits à partir d'une lecture du code (Fenix `b8410e5`, pypilot `fdff88f`). Les limites détaillées sont en tête de chaque script.

## Contenu

| Fichier | Rôle |
|---|---|
| `fenix_pid_sim.py` | Portage de `PID_ext::Compute` de Fenix ; scénarios S0 à S4 |
| `pypilot_sim.py` | Portage du pilote `basic` et de `Servo.do_command` de pypilot ; scénarios S0 à S4 |
| `comparaison_pilotes.py` | Banc commun : mêmes bateau, vérin, limite de barre et perturbations (E0, P1 à P4). **Importe les deux scripts précédents : les trois doivent rester dans ce dossier.** |
| `sortie_*.txt` | Sorties de référence de chaque script (exécution du 2026-10-30) |
| `*.png` | Figures produites par les scripts |

## Exécuter

Python 3 avec `numpy` (et `matplotlib` pour les figures), depuis ce dossier :

```
python -I fenix_pid_sim.py
python -I pypilot_sim.py
python -I comparaison_pilotes.py
```

Durée : quelques secondes pour les deux premiers, environ 15 s pour le banc commun. Chaque script affiche ses tableaux et écrit sa figure PNG à côté de lui.

**Test de non-régression (ARCH:VR-13) :** la sortie console doit être identique au fichier `sortie_*.txt` correspondant, sauf la ligne « Figure : … ». Un écart signifie que le script ou l'environnement a changé.

## Provenance — à lire

Les fichiers d'origine, livrés dans la conversation du 2026-10-28 « Comparaison des dépôts Fenix et pypilot », n'avaient jamais été enregistrés sur disque. Ils ont été **reconstitués le 2026-10-30** à partir du texte exact de cette conversation :

- `fenix_pid_sim.py` : seconde écriture complète, plus les trois modifications appliquées ensuite (bande morte du vérin coupée en S1) ;
- `pypilot_sim.py` : écriture unique, sans modification ultérieure ;
- `comparaison_pilotes.py` : écriture d'origine, plus le correctif appliqué le même jour (seuil d'arrêt 0,3°, variante 0,6°, appel à 100 Hz, P3 avec barre de compensation).

**Validation de la reconstitution (exécutée le 2026-10-30) :**

- `fenix_pid_sim.py` redonne toutes les valeurs de référence du plan de tests §2.1 : S0 0,00 % et ζ ≈ 1,30 ; S1 67,9 / 45,5 / 32,3 % ; S2 Kp effectif 2,45 et limite 17,1° ; S3 1,24° / 1,30° ; S4 +0,50° / +0,00°.
- `pypilot_sim.py` redonne toutes les valeurs du plan de tests §2.2 : S0 ≤ 0,01° ; S1 9,1 / 29,7 % et RMS 0,05 / 0,56° ; S2 22,0 / 29,7 / 54,8 / 73,8 % ; S3 0,27° et 0,07° ; S4 6,3 / 11,4 %.
- `comparaison_pilotes.py` : les **38 lignes de résultats** (V0, E0, P1 à P4) sont identiques, caractère pour caractère, à l'annexe 10.9 du plan de tests.

Environnement de validation : Python 3.13.18, numpy 2.5.4, matplotlib 3.11.2.

Empreintes SHA-256 :

```
35f96836835a6ea5a301226fc0a8fcbab5946655d14e79a894352958a6b11fa8  fenix_pid_sim.py
562d013c720acd039fe9e34d533db33501d4ea12472ed80e69ef9faa4197afe9  pypilot_sim.py
bed9145ffb9b13d931e61943d95816c6bdd1b6bb8f1dccefb43721daf5abdc4e  comparaison_pilotes.py
```
