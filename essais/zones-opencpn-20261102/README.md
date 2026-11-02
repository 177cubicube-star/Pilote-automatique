# Essai : Essais à terre sur les zones (OpenCPN, Signal K) et lectures locales

Rédigé le 2026-11-02. **Statut : GUIDE À PRÉPARER — CHANTIER REPORTÉ** (décision de Mathieu, 2026-11-02 : « on met le test de côté, chantier à faire plus tard »). Ni lancé ni abandonné ; rien n'est à faire maintenant.

**Non exécuté sur le matériel de Mathieu :** les deux scripts du dossier ont été exécutés le 2026-11-02 dans l'environnement de Claude (`python3 test_simulate_gps_rmc.py` : 18 réussis, 0 en échec, y compris depuis un autre dossier) ; **jamais avec OpenCPN ni sur le poste de Mathieu**.

**Rangement :** dossier daté, comme `essais/Q0-20261030-run001/` et `essais/Q1-20261030/` : ce `README.md` et les scripts `simulate_gps_rmc.py`, `test_simulate_gps_rmc.py`. Il accompagne `conception/concept-evitement-zones-opencpn-2026-11-02.md`. Version du vault : `07 - Essais/EXP-004 - Essais à terre zones OpenCPN et Signal K.md`.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

## Fichiers conservés avec ce guide

| Fichier (dans le dossier `07 - Essais`) | Rôle |
|---|---|
| `simulate_gps_rmc.py` | Simulateur de GPS qui envoie des phrases NMEA RMC à OpenCPN |
| `test_simulate_gps_rmc.py` | Contrôle automatique du simulateur (18 vérifications, sans OpenCPN) |

Pour reprendre : garder les deux fichiers dans un même dossier, puis lancer `python test_simulate_gps_rmc.py`. Le résultat attendu est « 18 reussis, 0 en echec ». Le test a été exécuté le 2026-11-02 dans l'environnement de Claude, y compris depuis un autre dossier que celui des fichiers ; **il n'a pas été exécuté sur l'ordinateur de Mathieu**.

## But

Savoir, par l'essai, comment les zones dessinées sortent d'OpenCPN ou de Signal K, avant de choisir une architecture. Le résultat est une série d'observations à rapporter dans la conversation, pas du code.

## Outil : `simulate_gps_rmc.py`

Script Python (bibliothèque standard seulement) qui simule un GPS avançant en ligne droite et envoie des phrases NMEA 0183 `RMC` (position, vitesse, cap) à OpenCPN. Il a été testé contre des récepteurs TCP et UDP simulés en local (somme de contrôle vérifiée sur un exemple publié, aller-retour des positions, avance de 1 852 m en 1 h à 1 nœud, message d'erreur clair sans serveur). **Il n'a pas été testé avec OpenCPN lui-même.**

- Voir les phrases sans rien envoyer : `python simulate_gps_rmc.py --print-only --duration 5`
- Envoyer à OpenCPN : `python simulate_gps_rmc.py --lat <latitude> --lon <longitude> --heading 90 --speed 4`
- Options : `--protocol tcp|udp` (tcp par défaut), `--host`, `--port` (10110 par défaut), `--duration` (120 s par défaut, 0 = jusqu'à Ctrl+C), `--rate`, `--quiet`.
- Dans OpenCPN, créer une connexion réseau TCP avec l'adresse `0.0.0.0` et le port `10110` : OpenCPN joue alors le rôle de serveur et accepte la connexion du script (comportement décrit dans le manuel d'OpenCPN).
- Le cap envoyé est un cap sur le fond (course), pas un capteur de cap.

## A. OpenCPN : dessiner une zone et déclencher une alarme

1. Installer OpenCPN si ce n'est pas fait. Dans `Options` puis `Plugins`, utiliser `Update Plugin Catalog: Master`, puis installer et activer **ODraw** et **Watchdog** (ODraw figure au catalogue ; Watchdog : à vérifier).
2. Avec ODraw, dessiner une **limite** (type **exclusion** pour un haut-fond ; type **inclusion** pour le contour du lac) **devant** la trajectoire du script. L'interface exacte dépend de la version : suis le manuel d'ODraw et **prends des captures d'écran** de ce que tu vois.
3. Dans Watchdog, chercher le réglage lié aux limites ou aux zones, et noter ce qu'il propose (alarme à l'entrée ? à la sortie ? distance ou temps avant la limite ?). À vérifier.
4. Lancer `simulate_gps_rmc.py` avec un point de départ proche de ta zone (par exemple 100 m avant la limite : à 4 nœuds le bateau simulé avance d'environ 2 m/s, soit environ 50 s avant d'y arriver). Vérifier que l'icône du bateau apparaît et avance dans OpenCPN.
5. Noter : l'alarme se déclenche-t-elle ? avec quel son ou quel message ? à quelle distance de la limite ?
6. Avec OpenCPN en marche, tester la commande `opencpn --remote --get_rest_endpoint` : elle doit afficher l'adresse du serveur REST. **Note l'adresse, puis ouvre-la dans un navigateur** et rapporte ce qui s'affiche.
7. Chercher le fichier **`navobj.xml`** sur l'ordinateur (emplacement à vérifier). Rapporte son chemin, sa date de dernière modification, et si le nom de ta limite y apparaît (ouvrir avec un éditeur de texte, **sans l'enregistrer**).

## B. Signal K et Freeboard-SK : une autre voie pour les zones

1. Installer le serveur Signal K (il demande Node.js). Par défaut il répond sur le port 3000 (à vérifier pour ta version).
2. Dans l'interface d'administration, installer **Freeboard-SK** depuis l'Appstore (à vérifier). Il peut demander un composant pour stocker les ressources (routes, régions, notes) : note ce que l'interface réclame.
3. Dessiner une **région** dans Freeboard-SK et noter où elle est enregistrée.
4. Ouvrir dans un navigateur l'adresse de la liste des régions du serveur (chemin `resources/regions`, à vérifier pour ta version). Rapporte ce qui s'affiche : c'est la preuve qu'un programme externe peut lire tes zones.
5. Si tu es à l'aise : tester l'alarme de zone (`POST /signalk/v2/api/alarms/area` avec un déclencheur `entry`). Cela demande une authentification (jeton ou cookie) ; **sinon, saute cette étape**, ce n'est pas urgent.

## C. Lectures à faire dans ton dépôt local de Fenix (pour finir les points restés illisibles)

Ouvre le dossier du dépôt dans VS Code et utilise `Ctrl+Shift+F` (recherche dans tous les fichiers). Copie les résultats dans la conversation.

- `nomotoId` : où la classe d'identification de Nomoto est-elle définie ?
- `class WindFeedforward` puis le fichier `WindFeedforward.cpp` : copier la table des coefficients de moment de vent (`Cn`).
- `Autopilot.cpp` : ouvrir autour des lignes 1740 à 1780 si ce n'est pas déjà fait (utile pour l'issue #13 ; la ligne 1775 a depuis été relue, voir la note du vault « Fenix - anticipation du vent (wind feedforward) »).
- `getWindFFratio`, `setWindFFratio` : où sont-ils appelés ?

## D. Ce que tu rapportes dans la conversation

- Les captures d'écran ou les textes des étapes A et B.
- Les chemins et les adresses relevés (fichier `navobj.xml`, adresse du serveur REST, adresse des régions).
- Les résultats de recherche de la partie C.
- Tout ce qui t'a surpris ou bloqué : c'est souvent là qu'on apprend le plus.

## E. Limites et prudence

- Ces essais servent à **comprendre**, pas à valider une fonction de sécurité. Un résultat positif à terre ne prouve pas un comportement fiable sur l'eau.
- Ne branche aucun actionneur à un programme qui reçoit des zones tant que le mode « fantôme » (alarme et journal seulement) n'a pas été essayé.
- Si une étape ne marche pas comme décrit, ne force pas : note l'écart et rapporte-le.
