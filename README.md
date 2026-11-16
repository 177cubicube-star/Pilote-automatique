# Pilote automatique de voilier

Dépôt du projet complet : concevoir et construire un **pilote automatique de
barre franche à vérin linéaire**, pour voiliers jusqu'à 9 m. Le bateau d'essai
est un Catalina Capri 22. Le projet va de la recherche jusqu'au prototype
fonctionnel.

Ce dépôt a vocation à porter **tout** le projet : sources et documentation,
concepts et techniques de conception, schémas électriques, code embarqué,
prototypes et essais. Le **raisonnement et les décisions** vivent dans un vault
Obsidian, qui fait autorité. Ce dépôt en garde des **copies datées** dans
`conception/`.

> 🟡 **Phase actuelle (mise à jour du 2026-11-16) : conception.**
> Le cahier des besoins est établi. Treize décisions sont acceptées (DEC-003 à
> DEC-015) : périmètre fonctionnel, capteurs, vérin, ordre de réalisation,
> précision de cap, et architecture de départ (pypilot sur Raspberry Pi,
> contrôle moteur `motor.ino`, façade ESP32 ; Fenix en repli). Aucun
> matériel n'est acheté, aucun code embarqué n'est écrit.
> Référence : [`conception/cahier-des-besoins-et-decisions-2026-11-16.md`](conception/cahier-des-besoins-et-decisions-2026-11-16.md).

## L'objectif

Un pilote de barre franche à **vérin linéaire seulement** (course d'au moins
300 mm, force d'au moins 100 lbf), avec :
- au socle : cap compas, barre bloquée, follow-up et non-follow-up ; virement et
  empannage par séquences programmables ; homme à la mer ; alarmes ; boutons,
  écran tactile, veille physique et réglage depuis une tablette ;
- en extension : vent apparent et vent réel, suivi de route OpenCPN, anticipation
  de la barre par le vent ;
- capteurs : GPS, IMU ICM-20948, accéléromètre LIS3DH ; liaisons NMEA 2000, et
  NMEA 0183 en entrée et en sortie.

| Rôle | Projet | Pourquoi il est ici |
|---|---|---|
| Base de l'**architecture de départ** (DEC-014) | [pyPilot](https://pypilot.org/doc/) | Architecture hybride retenue : pypilot, façade ESP32 et contrôle moteur séparé |
| Base **DIY** de référence | [Fenix](https://github.com/spascual90/Fenix.git) | Projet Arduino complet à vérin linéaire ; repli et source d'idées (anticipation par le vent) |
| Référence **commerciale** | [Pelagic Autopilot](https://pelagicautopilot.com/) | Produit de comparaison |

## Les volets du projet

| Volet | Contenu | État |
|---|---|---|
| **Sources & documentation** | Registre des sources, notes de collecte, synthèses | 🟢 En cours |
| **Conception** | Cahier des besoins, décisions, concepts, conception V0.3 | 🟢 En cours |
| **Électronique** | Schémas, câblage, liste de composants (BoM) | 🟡 Liste des entrées-sorties faite ; la BoM V0.2 est dépassée |
| **Code** | Firmware embarqué, régulation, interfaces | ⚪ À venir |
| **Prototypes et essais** | Simulation (SailSim, Q0 et Q1), simulateur GPS, futurs bancs | 🟡 En simulation seulement |

## Ce que le dépôt contient aujourd'hui

| Emplacement | Rôle |
|---|---|
| [`sources-techniques.md`](sources-techniques.md) | **Le registre.** Une ligne par source déposée, avec type, lien, date de dépôt et statut. |
| [`sources-brutes/`](sources-brutes/) | Le contenu **détaillé** conservé quand une source apportait plus qu'un lien, et les analyses de dépôts open source. |
| [`conception/`](conception/) | Copies datées des documents de conception. Commencer par `cahier-des-besoins-et-decisions-2026-11-16.md`. Les documents plus anciens portent un encadré quand ils sont dépassés. |
| [`essais/`](essais/) | Qualification SailSim (Q0, Q1) et simulateur GPS pour les zones OpenCPN. |
| [`simulations/`](simulations/) | Simulations comparées Fenix et pypilot. |
| [`diagrammes-pilotes/`](diagrammes-pilotes/) | Diagrammes des six projets de pilotes étudiés. |
| [`sessions/`](sessions/) | Recaps de continuité de session. |

## La méthode de collecte : ratisser large d'abord, trier ensuite

Les sources sont déposées **telles quelles**, sans filtrage ni jugement de
pertinence au moment du dépôt. Le tri et l'extraction se font **au moment de
l'analyse**, pas au moment de la collecte.

Conséquence assumée : le registre contient des sources qui seront écartées.
C'est voulu — écarter une source demande de l'avoir lue, et ce travail n'est
pas encore fait.

Chaque ligne du registre porte un statut :

| Statut | Signification |
|---|---|
| `Enregistrée, non analysée` | Déposée, jamais lue en profondeur. C'est encore le statut de la plupart des sources ; plusieurs sont déjà analysées ou partiellement lues (voir le registre). |
| `Analysée` | Une synthèse existe, ou les éléments retenus sont passés dans le vault Obsidian. |
| `Écartée` | Lue et rejetée — avec la raison en note. |

Les éléments retenus après analyse sont consignés dans un vault Obsidian, qui
sert de source de référence pour le travail de conception.

## Prochaine étape

Voir la section 7 du dernier recap dans `sessions/`. Au 2026-11-16 :
- réconcilier le vérin de référence avec la force minimale ;
- arbitrer le budget du socle ;
- faire une BoM V0.3 ;
- réviser le plan d'exécution en V0-6 (architecture décidée par DEC-014) ;
- décider ensemble la machine hôte et le point d'entrée du NMEA 2000.

## Avertissement

Les contenus de `sources-brutes/` (câblages, valeurs, procédures) sont
recopiés **sans vérification** depuis leurs sources d'origine. Ce sont des
notes de collecte, pas des instructions de montage validées. À revalider
contre la documentation d'origine avant tout usage — un câblage erroné grille
une carte, et un pilote mal réglé lâche la barre en mer.
