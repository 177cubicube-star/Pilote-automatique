
# CON-009 — Script d'anticipation de la barre par le vent (spécification)

> **Copie datée du 2026-11-16 — le vault fait autorité.** Source : vault, `05 - Concepts/CON-009 - Script d'anticipation de la barre par le vent (spécification).md` (type `concept`, statut `exploratoire`). Le principe (option C) est accepté (DEC-005, DEC-007) ; les valeurs chiffrées sont des valeurs de départ. Les noms entre « » désignent des notes du vault.

Spécification d'un script à écrire avec Claude Code dans le dépôt du projet. Rien n'est codé ni testé. Cette note décrit **quoi** construire ; le **comment** (structure du code, emplacement dans le dépôt) suit les conventions du dépôt (`CLAUDE.md`).

## Provenance et relations

- Décision d'origine : « DEC-005 - Prévoir un mode vent et une girouette-anémomètre NMEA » — le vent est une donnée de plus pour la gestion du gouvernail. Le 2026-11-16, Mathieu a retenu l'**option C** (mode fantôme, puis activation explicite, mode compas compris) et a décidé de créer ce script.
- Étape : **extension**, avec le mode vent apparent (« grille-capacites-pilote »).
- Architecture candidate : « CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé ». Aucune anticipation par le vent n'a été trouvée dans la documentation de pypilot.
- Référence de calcul : « Fenix - anticipation du vent (wind feedforward) » (lecture du code de Fenix, commit `b8410e5`, non exécuté).
- Idée voisine : « CON-006 - Anticipation de la barre par capteurs inertiels ».

## Problème

Un régulateur de cap corrige **après** que le bateau a dévié. Une rafale ou un changement d'angle du vent fait lofer ou abattre le bateau avant que l'erreur de cap n'apparaisse. L'anticipation (*feedforward*) calcule à l'avance le coup de barre qui compense l'effet du vent.

## Solution candidate

Un script Python, exécuté sur le calculateur qui héberge pypilot et Signal K, construit en **deux versions**.

### Version 1 — Mode fantôme (seule version à construire maintenant)

Le script **calcule et journalise**. Il **n'envoie aucune commande** à pypilot ni au moteur.

**Entrées**

| Donnée | Source proposée | Remarque |
|---|---|---|
| Angle du vent apparent | Signal K, `environment.wind.angleApparent` (radians) | Avec son horodatage, pour en calculer l'âge |
| Vitesse du vent apparent | Signal K, `environment.wind.speedApparent` (m/s) | Idem |
| Cap | pypilot (cap de l'IMU) | Pour l'analyse du journal |
| Mode et état du pilote | pypilot (engagé ou en veille, mode actif) | Le calcul continue en veille, mais l'état est journalisé |
| Angle de barre mesuré | pypilot, si le retour de position est disponible | Indispensable pour identifier les coefficients |

*À vérifier par Claude Code :* les noms exacts des valeurs pypilot et la méthode de lecture (bibliothèque cliente de pypilot ou interface réseau).

**Calcul (point de départ : la formule de Fenix)**

1. Filtrer l'angle et la vitesse du vent sur environ 1 s.
2. Moment de lacet estimé : `moment = k_air × vitesse² × Cn(angle)`, où `Cn` est un coefficient qui dépend de l'angle du vent (table par tranches d'angle).
3. Correction de barre : `correction = −moment × gain`, **bornée** (Fenix : ±10°).
4. Seuil d'activation sur la vitesse du vent, avec hystérésis (Fenix : active au-dessus de 0,6 m/s, arrêtée sous 0,4 m/s).

La table `Cn` de Fenix est **un exemple, pas des valeurs pour le Capri 22**. Les coefficients de départ seront à zéro ou prudents, puis identifiés à partir du journal. Toutes les constantes (`k_air`, gain, borne, seuils, durée de filtrage, âge maximal du vent) sont dans un **fichier de configuration**, pas dans le code.

**Garde-fous (déjà actifs en mode fantôme, pour être testés)**

- Vent trop vieux (âge supérieur à une limite configurable) → correction calculée à 0, motif journalisé.
- Valeurs hors plage plausibles ou saut brutal → correction à 0, motif journalisé.
- Correction toujours bornée.
- En veille : calcul journalisé, marqué « veille ».

**Sortie : un journal**

Un fichier CSV horodaté, une ligne par cycle : temps ; âge, angle et vitesse du vent (bruts et filtrés) ; cap ; mode et état du pilote ; angle de barre mesuré ; moment estimé ; correction calculée ; état de l'anticipation (calculée, coupée) et motif de coupure.

### Version 2 — Activation (plus tard, hors de cette spécification)

La correction serait réellement appliquée, mode compas compris, après identification des coefficients et **sur décision explicite de Mathieu**. Un point reste ouvert : **pypilot ne prévoit pas d'entrée pour une correction de barre**. Agir sur la consigne de cap n'est pas équivalent ; une modification de pypilot sera probablement nécessaire. La version 2 commence par trancher ce point.

## Identification des coefficients (proposition)

Avec le journal de navigations réelles en mode compas, comparer, par tranche d'angle de vent, l'angle de barre que le pilote a effectivement tenu en régime établi avec le moment estimé. En déduire `Cn` par régression simple. À préciser quand des journaux existeront. Fenix ajuste en plus le poids de l'anticipation automatiquement (cible de 80 %, avec le défaut de l'issue #13) : **non repris en version 1**.

## Alternatives

- **Porter le code de Fenix** tel quel : il est en C++ pour Arduino et lié à son régulateur ; mieux vaut reprendre la formule et la réécrire.
- **Pas d'anticipation, mode vent seulement** (option A de DEC-005) : écartée par Mathieu.

## Critères d'acceptation de la version 1

1. **Aucune commande n'est jamais envoyée** à pypilot ni au moteur, quel que soit l'état. Vérifié par un test.
2. Le journal est produit et lisible, avec toutes les colonnes.
3. Les coupures (vent trop vieux, hors plage, saut brutal, veille) se déclenchent dans les tests, avec le bon motif.
4. La correction ne dépasse jamais la borne configurée.
5. Les tests du dépôt passent ; les résultats réels sont rapportés.

## Inconnues

- Fréquence de calcul utile (celle des données de vent, ou un rythme fixe).
- Noms et méthode de lecture des valeurs de pypilot.
- Valeurs de départ de `k_air`, du gain et de la table `Cn` pour un petit voilier.
- Correction de la gîte et du mouvement du mât sur le vent apparent (disposition 14 de DEC-005) : prévue plus tard, pas en version 1.
- Point d'injection dans pypilot pour la version 2.

## Essais nécessaires

1. **Tests unitaires** avec des données de vent simulées : seuils, filtrage, bornes, coupures.
2. **Rejeu** d'un journal ou de données de vent enregistrées.
3. **Banc** : avec le pypilot du banc SailSim, si ce banc fournit des données de vent (à vérifier), sinon avec des valeurs injectées par Node-RED dans Signal K.
4. **Sur l'eau, en mode fantôme** : collecte de journaux en mode compas, pour identifier les coefficients.

## Issue

Non tranchée. Le passage à la version 2 exigera une décision explicite de Mathieu.
