# Concept : Anticiper la correction de barre grâce aux capteurs inertiels

Rédigé le 2026-11-02. **Statut : CONCEPT EXPLORATOIRE — PROPOSITION. Aucune décision de conception n'est validée.** Idée de Mathieu : ajouter un capteur d'accélération et de direction qui suit le mouvement du nez du bateau pour que la barre agisse **en prévention**. Ses chiffres sont très approximatifs et n'ont pas été recherchés.

**Non exécuté :** rien n'a été mesuré ni simulé ; les constats viennent de la lecture du code (voir `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`, sections 3.1, 3.2.3, 3.7, 4).

**Rangement :** dans `conception/`, comme la proposition d'architecture du 2026-10-28 qu'il complète sans la modifier ; choix de rangement **à confirmer par Mathieu**. Version du vault : `05 - Concepts/CON-006 - Anticipation de la barre par capteurs inertiels.md`.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

## 1. L'idée (formulée par Mathieu)

Ajouter au pilote un capteur d'accélération et de direction (par exemple un trois axes) qui suit les mouvements du nez du bateau dans l'espace, afin que le mouvement de la barre agisse **en prévention** plutôt qu'en réaction à une erreur de cap déjà installée. Mathieu précise que les chiffres évoqués sont très approximatifs et n'ont pas été recherchés.

## 2. Ce qui est établi (lu dans le code ou la documentation)

Le détail et les sources sont dans `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md` (sections 3.1, 3.2.3 et 3.7).

- Les pilotes étudiés utilisent déjà une centrale inertielle (IMU) à trois types de capteurs : accéléromètre, gyroscope, magnétomètre. L'idée ne consiste donc pas à introduire un nouveau type de mesure, mais éventuellement un second point de mesure ou une meilleure exploitation des mesures existantes.
- **La gîte n'agit sur la commande ni dans pypilot ni dans Fenix, dans les fichiers lus.** pypilot la calcule (filtrée) et l'exporte vers Signal K ; aucun de ses trois pilotes lus (`basic`, `simple`, `learning`) ne l'utilise, mais le fichier de configuration du pilote expérimental `learning` n'a pas été lu. Fenix calcule roulis et tangage uniquement pour projeter la vitesse de rotation sur la verticale et ne les expose pas : `DevICM20948` ne transmet que cap, vitesse de lacet et un indicateur du magnétomètre.
- **pypilot** : la vitesse de lacet (terme D) est le moteur principal de la correction ; une dérivée seconde (DD) « améliore le temps de réaction » d'après son manuel. Le calcul final additionne simplement les contributions de chaque gain (`Compute`). Selon un message du forum, l'accélération résiduelle (sans la gravité) existe dans l'IMU mais n'est pas exploitée comme pilonnement, avance ou dérive.
- **pypilot a un précédent de contrôle anticipatif** : le pilote `learning` (expérimental, désactivé, code incomplet) utilise un modèle appris pour prédire l'effet de séquences de commandes de barre sur environ 0,4 s et retient la meilleure ; sans modèle, il retombe sur le pilote de base.
- **Fenix** : le cap utilisé pour la régulation est filtré des effets de vagues par un observateur (`WavePassiveObserver`) dont les entrées sont le cap, la position de barre et la vitesse de lacet : ni roulis ni accélérations. Depuis la version 4.1, une **prédiction de l'écart de lacet** à partir de l'IMU est calculée « pour information seulement », sans modifier la logique du PID (RELEASE.md). La sortie du PID est la somme P + I + D + FF + windFF : un terme de plus pourrait s'y ajouter (hypothèse de conception, non testée).
- **Précédent commercial** : le guide de réglage du pilote B&G H5000 décrit une « compensation de gîte » qui applique une correction de barre avant que les rafales ou la mer ne provoquent un événement dangereux, désactivée par défaut. L'idée de la piste B n'est donc pas nouvelle ; elle n'est simplement pas présente dans les deux pilotes ouverts lus. Deux brevets anciens vont dans le même sens (statut juridique non vérifié).
- Le vérin recommandé par Fenix (300 mm de course, 30 mm/s) met environ 10 s à parcourir toute sa course (calcul à partir de ces deux valeurs). Le vérin de Mathieu n'est pas encore choisi.
- Côté NMEA, ni Fenix (dans ce qui a été lu) ni pypilot n'échangent le roulis ou la gîte en NMEA 0183 ; pypilot l'exporte via Signal K. Si la gîte est mesurée par l'IMU du pilote lui-même, le NMEA n'intervient pas.

## 3. Trois sens possibles de « prévenir »

| Piste | Ce qu'on capte | Idée | Statut |
|---|---|---|---|
| A. Lacet | Vitesse et accélération de lacet | Le bateau commence à tourner avant que l'erreur de cap soit grande | Déjà exploitée (pypilot D et DD, Fenix : modèle de référence et feedforward) |
| B. Gîte | Inclinaison du bateau lors d'une rafale | En voile, la gîte accroît la tendance à remonter au vent : la barre pourrait compenser avant le changement de cap | **Hypothèse à tester** ; absente des deux pilotes ouverts lus, présente dans un pilote commercial (H5000) |
| C. Nez dans les vagues | Mouvements du nez (tangage, accélérations) | La vague touche le nez avant l'arrière | Utilisée surtout pour filtrer (observateur de vagues de Fenix), pas pour anticiper ; gain incertain sur un lac |

## 4. Un deuxième capteur au nez : ce que le raisonnement suggère

- Un gyroscope mesure la même vitesse de rotation à n'importe quel endroit d'une coque rigide : pour la rotation, un second capteur apporte très peu.
- Ce qu'il ajouterait surtout est une **avance** : le nez voit la vague avant l'arrière. Ordre de grandeur **non recherché** : pour un bateau de 6 à 7 m à 1,5 ou 2 m/s, environ 3 à 4 s entre le nez et le safran. À mesurer.
- Cette avance n'a de valeur que si le système corrige plus vite qu'elle. Le délai du vérin et l'inertie du bateau sont les freins probables.
- Un accéléromètre au nez mélange gravité, pilonnement, tangage, roulis et vibrations ; en extraire le « mouvement du nez » demande une fusion de capteurs, que l'IMU existant fait déjà pour son propre point.
- Plus d'entrées dans la régulation, ce sont plus de façons de se tromper (oscillations si la correction anticipée est mal réglée, panne ou valeur aberrante d'un capteur). Il faudrait des contrôles de plausibilité, comme ceux de pypilot (réinitialisation si les valeurs sortent de plages vraisemblables).

## 5. Plan d'essai proposé (non engagé)

1. **Enregistrer sans piloter** : IMU et enregistreur de données à bord, en barrant à la main, à la prochaine saison (le bateau est sorti de l'eau pour l'hiver).
2. **Analyser l'avance** : pour chaque signal candidat (lacet, gîte, mouvement du nez), vérifier s'il précède le changement de cap et de combien de secondes.
3. **Ne retenir que les signaux dont l'avance dépasse le délai du vérin**, puis les ajouter comme petite correction anticipée à faible gain (le guide H5000 recommande d'attendre environ une minute après l'engagement du pilote avant de régler le gain de gîte, le temps que la tendance à remonter au vent se stabilise).
4. **Tester d'abord sur simulateur** (Fenix en propose un ; je ne sais pas s'il modélise les rafales).

## 6. Questions ouvertes

- Un terme de gîte s'ajouterait-il le mieux à la sortie du PID de Fenix (comme le feedforward du vent), comme entrée de l'observateur, ou ailleurs ? Les remarques de 3.2.3 et 3.7 de l'analyse donnent les points d'accroche lus ; la fin d'`Autopilot.cpp` et la classe d'identification de Nomoto restent à lire.
- Que contient le fichier de configuration du pilote `learning` de pypilot (capteurs d'entrée) ? Y figure-t-il le roulis ou des accélérations ?
- Quelle avance réelle sur le bateau de Mathieu, sur son plan d'eau ?
- Quel délai de réponse aura le vérin retenu ?
- Un deuxième capteur apporte-t-il quelque chose que l'IMU principal ne donne pas déjà ?
- Faut-il, dans le cas de la piste B, que la gîte soit mesurée par l'IMU du pilote ou importée d'un autre instrument (alors seulement le NMEA ou Signal K interviendraient) ?

## 7. Liens

- `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md` (sections 3.1, 3.2.3, 3.7 et 4).
- `sources-brutes/point-clos-nmea-girouette-2026-11-02.md` (correction de gîte du vent apparent).

## Sources

- Manuel pypilot (gains D et DD) ; `boatimu.py` (gîte filtrée) ; `autopilot.py` et `pilots/*.py` (aucune gîte dans la commande) ; forum OpenMarine (`navigation.attitude`, `imu.accel_residuals`).
- Fenix : `RELEASE.md` (prédiction du lacet, v4.1), `WavePassiveObserver.cpp`, `PID_v1_ext.cpp`, `ICM20948AHRS.cpp`, `DevICM20948.cpp`, `IF_NMEA.cpp`, `emcNMEA.cpp`, recommandation de vérin (300 mm, 30 mm/s).
- Guide de réglage B&G H5000 (copie sur vs.j109.org) ; brevets US5152239 et US5179905.
