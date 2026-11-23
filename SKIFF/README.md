# SKIFF : banc Pi → vérin simulé → simulateur Skiff

Banc logiciel pour rejouer des séquences de barre (virement) sur le Lagoon 450S du
simulateur [Skiff](https://github.com/DeepBlueDynamics/skiff), avec un vérin simulé
entre le Pi et le safran. Stdlib Python seulement.

## Fichiers

| Fichier | Rôle |
|---|---|
| `verin_sequence.py` | Vérin simulé (`step_verin`, retard + vitesse max + butées) et séquences d'étapes |
| `pont_skiff.py` | Pont HTTP vers Skiff : envoie `helm = position du vérin / 35`, journalise en CSV |
| `preparer_essai.py` | Remet le Lagoon dans le même état (reset, vent, voiles, établissement) ; `DetecteurPassageVent` |
| `essai_detecteur.py` | Essai du détecteur : -20° jusqu'au passage du vent, puis 0° |
| `virement_phases.py` | Virement à phases de `essais/CON010-virement-20261123/virement_spec.py` transposé à Skiff, et mesures façon `analyse_spec.py` |
| `essai_virement.py` | Préparation + virement à phases + mesures (CSV, journal, mesures JSON) |
| `essai_temoin.py` | Témoin : le maintien de cap de Skiff reçoit directement Hfinal (sans vérin) |
| `chercher_cap.py` | Trouve le cap d'approche qui donne le vent apparent visé, pour un vent donné |
| `test_*.py` | Tests (faux serveur Skiff) |

## Conventions (une seule source chacune)

- **Signe de barre** : `pont_skiff.SIGNE_VERS_SKIFF = +1`. En signe Skiff, +20° fait venir l'étrave sur bâbord et -20° sur tribord (essai du 2026-11-23).
- **Angle du vent apparent** : toujours `pont_skiff.awa_vient_de(state)`. Le `awa_deg` brut de Skiff est décalé de 180° (« va vers ») : son zéro est le **vent arrière**. Converti : 0° = face au vent, + = tribord, - = bâbord.
- **Angle de virement** : Hfinal = H0 + angle. Il doit viser le près **symétrique** de l'autre amure. Approche à 293° avec un vent du 000° (67° du vent vrai) → environ **134°** (Hfinal ≈ 067°). Avec 80°, Hfinal = 13° est à 13° du vent : non navigable.
- **Vent envoyé à Skiff** : `wind_to_deg` = direction vers laquelle il souffle (vent du 000° → 180°), avec `manual: true`.

## Utilisation

1. Tests : `python -m unittest test_verin_sequence test_pont_skiff test_preparer_essai`
2. Démarrer Skiff (dans son propre dossier) : `cargo run --release --bin skiff`, vérifier `http://localhost:18081/healthz`. **Ne pas ouvrir le cockpit** (il réécrit la barre).
3. Pont seul : `python pont_skiff.py --cible -20 --tenue 4 --duree 12 --csv essai_pont_01.csv`
4. Préparation : `python preparer_essai.py --cap 293.7` (ajouter `--lat/--lon` en eau libre si la carte des terres est chargée)
5. Détecteur : `python essai_detecteur.py --csv essai_detecteur_01.csv`
6. Virement à phases, A/B sur la vitesse du vérin : `python essai_virement.py --angle 134 --vitesse 10 --tag virement_134_v10`, puis `--vitesse 5 --tag virement_134_v5`
7. Témoin : `python essai_temoin.py --angle 134 --tag temoin_134`
8. Autre vent : `python chercher_cap.py --vent 10 --awa 40`, puis `--vent 10 --cap <CAP trouvé> --angle auto` (près symétrique) dans `essai_temoin.py` ou `essai_virement.py`

## Résultats du 2026-11-23 (`resultats-20261123/`)

Exécutés par Claude sur une copie de Skiff compilée dans son espace de travail (sans carte des terres ni bathymétrie : échouage désactivé), pas sur le PC de Mathieu.

- **Pont seul** (`essai_pont_01.csv`) : cadence 50 ms (48 à 52 ms), aucune barre réécrite, rampe du vérin à 8,00 °/s, safran Skiff à 1,4° au plus derrière la position du vérin. Bateau à l'arrêt : il ne tourne pas, ce qui est normal sans vitesse.
- **Préparation** : établi en 38 s, cap 293,0°, vent apparent +41,3°, 3,67 m/s, rotation +0,02 °/s, `cap_final` 13,0°.
- **Détecteur** (`essai_detecteur_01.csv`) : armé, passage du vent détecté à 15,35 s (cap 354,0°), retour de barre commandé sur la même ligne. Rotation d'environ 4 °/s à -20°. Après le retour à 0°, le Lagoon **reste face au vent** : cap 2,4 à 2,5°, 0,4 à 0,8 m/s, vent apparent -6°, `cap_final` 13° non atteint. Résultat reproduit sur deux passes.

Constat, non une conclusion de réglage : ramener la barre à 0° au moment exact du passage du vent ne suffit pas à finir le virement sur ce bateau simulé.

### Virement à phases (spécification de Mathieu, phases de l'essai 4)

Phases : -15° (contre-barre) à 10 °/s · 20° à 10 °/s, 3 s · 25° à 5 °/s, 8 s · 10° à 5 °/s, 2 s · 0° à 5 °/s.
Approche identique pour tous : cap 293,1°, vent apparent +40,6°, 3,85 m/s, établie 10 s. Une exécution par cas.
Reprise après séquence : tenue de cap proportionnelle (loi du maintien de Skiff, 2,1° de barre par degré) **à travers le vérin** (choix de transposition, pypilot n'est pas dans ce banc).

| Fichiers | Réglage | Vent apparent à 0 | Fin de séquence | À la fin de la séquence | Final (≈ 70 s) | Réussi |
|---|---|---|---|---|---|---|
| `virement_A_v10_*` | angle 80°, vérin 10 °/s | 16,3 s | 24,1 s | aligné sur Hfinal 13° (à 13° du vent !) | recule (-0,22 m/s) | non |
| `virement_134_v10_*` | angle 134°, vérin 10 °/s | 16,2 s | 24,0 s | 59 % du virement, 1,08 m/s | cap 25°, 0,18 m/s | non |
| `virement_134_v5_*` | angle 134°, vérin 5 °/s | 20,2 s | 27,1 s (phase 2 NON ATTEINT) | 58 %, 1,23 m/s | cap 26°, 0,20 m/s | non |
| `temoin_134.csv` | maintien de cap Skiff, barre -35° immédiate | 8,0 s | — | — | cap 39°, 0,68 m/s (objectif 067°) | non |

Constats (SIMULÉ, Lagoon 450S de Skiff, vent 7,2 m/s) :

1. La **mécanique** de la séquence fonctionne sur Skiff : phases dans l'ordre, maintien compté à l'arrivée, « NON ATTEINT » quand le vérin est trop lent (5 °/s pour passer de +15° à -20° en 5 s), reprise sur Hfinal.
2. Vérin à 5 °/s : passage du vent 4 s plus tard qu'à 10 °/s ; état final semblable.
3. **Même le témoin ne finit pas le virement** : ce Lagoon simulé perd presque toute sa vitesse en virant et repart très lentement. Comme pour SailSim (constat de `CON010-virement-20261123`), le banc valide la mécanique, pas les valeurs : angles et durées se règlent sur le Capri 22.

### Plus de vent, approche plus arrivée (témoins, angle symétrique)

| Fichier | Vent | Approche | Dérive à l'approche | Vent apparent à 0 | Final (70 s) |
|---|---|---|---|---|---|
| `temoin_v7.2_a40.csv` | 7,2 m/s | 293,1°, +40,6°, 3,85 m/s | -4,3° | 7,9 s | cap 39°, 0,68 m/s (Hfinal 067°) |
| `temoin_v10_a40.csv` | 10 m/s | 308,4°, +41,1°, 1,31 m/s | **-39,0°** | jamais | cap 324°, 0,45 m/s |
| `temoin_v13_a40.csv` | 13 m/s | 308,5°, +41,5°, 1,72 m/s | **-42,2°** | jamais | cap 329°, recule |

Sondes d'écoute à 7,2 m/s (préparation seulement) : 293°/0,76 → 3,85 m/s · 285°/0,68 → 3,82 m/s · 285°/0,60 → 3,22 m/s · 294°/0,60 → 2,41 m/s · 285°/0,76 → 0,73 m/s · 294°/0,90 → 0,51 m/s.

Constats (SIMULÉ) :

4. **Plus de vent ralentit ce Lagoon** : dès 10 m/s, il dérive de 39 à 42° (ses dérives et safrans décrochent vers 16 à 18° dans le modèle), avance en crabe à 1,3–1,7 m/s et ne passe plus le vent.
5. **Une approche plus arrivée ne donne pas plus de vitesse** : le plafond est d'environ 3,8 m/s à 7,2 m/s de vent, et le pic de réglage d'écoute est très étroit.
6. Conclusion : dans Skiff, aucun réglage essayé ne permet au Lagoon de finir un virement, même avec le maintien de cap interne. Le banc Skiff s'arrête à la validation de la **mécanique** (pont, vérin, préparation, détecteur, séquence à phases).
