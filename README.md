# Pilote automatique de voilier

Dépôt du projet complet : concevoir et construire un **pilote automatique de
barre pour voilier** — de la recherche jusqu'au prototype fonctionnel.

Ce dépôt a vocation à porter **tout** le projet : sources et documentation,
concepts et techniques de conception, schémas électriques, code embarqué,
prototypes et essais.

> 🟡 **Phase actuelle : collecte de sources.**
> Le dépôt ne contient encore ni code, ni schéma, ni décision technique
> arrêtée. Ce qui suit décrit une trajectoire, pas un état.

## L'objectif

Bâtir un pilote de barre du type Fenix — **Arduino Mega + vérin linéaire +
IMU** — en visant une conception comparable à un produit commercial existant.

| Rôle | Projet | Pourquoi il est ici |
|---|---|---|
| Référence **commerciale** | [Pelagic Autopilot](https://pelagicautopilot.com/) | Le produit qui se vend, et que le projet cherche à égaler en conception |
| Référence **open-source** | [pyPilot](https://pypilot.org/doc/) | Architecture jugée la plus proche de celle de Pelagic |
| Base de départ **DIY** | [Fenix](https://github.com/spascual90/Fenix.git) | Projet Arduino complet et documenté (Mega + vérin + IMU) |

## Les volets du projet

| Volet | Contenu | État |
|---|---|---|
| **Sources & documentation** | Registre des sources, notes de collecte, synthèses | 🟢 En cours |
| **Conception** | Concepts, techniques de conception, choix d'architecture et leurs raisons | ⚪ À venir |
| **Électronique** | Schémas, diagrammes de câblage, liste de composants (BoM) | ⚪ À venir |
| **Code** | Firmware embarqué, régulation, interfaces | ⚪ À venir |
| **Prototypes** | Montages d'essai, mesures, résultats de tests | ⚪ À venir |

L'organisation en dossiers se fixera **quand le contenu arrivera**, pas avant :
inventer une arborescence pour des dossiers vides ne rend service à personne.

## Ce que le dépôt contient aujourd'hui

| Fichier | Rôle |
|---|---|
| [`sources-techniques.md`](sources-techniques.md) | **Le registre.** Une ligne par source déposée, avec type, lien, date de dépôt et statut. |
| [`sources-brutes/`](sources-brutes/) | Le contenu **détaillé** conservé intégralement quand un dépôt apportait plus qu'un simple lien : composants, câblage, formules, procédures de calibration. |

Les compilations brutes déposées à ce jour :

- [`fenix-liens-et-notes-2026-09-08.md`](sources-brutes/fenix-liens-et-notes-2026-09-08.md)
  — BoM Fenix, firmwares, câblage BTS7960, calibration IMU et vérin, modes de
  navigation, interface série.
- [`pelagic-pypilot-notes-2026-09-08.md`](sources-brutes/pelagic-pypilot-notes-2026-09-08.md)
  — specs Pelagic, architecture pyPilot/TinyPilot, variante ESP32, vitesses de
  vérin, alimentation.

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
| `Enregistrée, non analysée` | Déposée, jamais lue en profondeur. **C'est le statut de toutes les sources à ce jour.** |
| `Analysée` | Une synthèse existe, ou les éléments retenus sont passés dans le vault Obsidian. |
| `Écartée` | Lue et rejetée — avec la raison en note. |

Les éléments retenus après analyse sont consignés dans un vault Obsidian, qui
sert de source de référence pour le travail de conception.

## Prochaine étape

Amorcer le tri : faire passer les sources de `Enregistrée, non analysée` à
`Analysée` ou `Écartée`. Les volets Conception, Électronique, Code et
Prototypes s'ouvrent à partir de ce tri.

## Avertissement

Les contenus de `sources-brutes/` (câblages, valeurs, procédures) sont
recopiés **sans vérification** depuis leurs sources d'origine. Ce sont des
notes de collecte, pas des instructions de montage validées. À revalider
contre la documentation d'origine avant tout usage — un câblage erroné grille
une carte, et un pilote mal réglé lâche la barre en mer.
