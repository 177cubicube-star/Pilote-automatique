# Cahier des besoins et décisions acceptées — session du 2026-11-16

Rédigé le 2026-11-16 à partir du vault Obsidian. **Copie datée pour le dépôt : le vault fait autorité.** En cas d'écart, les notes du vault prévalent : `00 - Projet/Cahier des besoins du pilote.md` et `06 - Décisions/DEC-003` à `DEC-013`.

**Statut.** Contrairement au document `decisions-et-dispositions-2026-11-02.md`, ces décisions sont **ACCEPTÉES par Mathieu** le 2026-11-16. Les DEC-003 à DEC-005 reprennent DP-01 à DP-03 de ce document. Les dispositions DISP-01 à DISP-16 ont été acceptées avec DEC-004 et DEC-005, et la condition et la lecture du 2026-11-16 s'y appliquent. La provenance de chaque choix (citation de Mathieu, revue du 2026-11-16) est dans le vault, `00 - Projet/Registre d'approbation - session du 2026-11-16.md`.

**Non exécuté :** aucune de ces décisions n'a été testée. Ce sont des exigences, pas des fonctions existantes.

Les noms entre « » désignent des notes du vault.

## A. Registre des décisions acceptées

| ID | Décision | Date de la note | Statut |
|---|---|---|---|
| DEC-003 | Vérin linéaire seulement. Acceptation partielle : la ligne « Milo devient un projet distinct » n'est pas reprise | 2026-11-01 | ACCEPTÉE (2026-11-16) |
| DEC-004 | Prévoir dès la conception l'évitement de zones et l'interface avec un traceur (OpenCPN) | 2026-11-02 | ACCEPTÉE (2026-11-16) |
| DEC-005 | Prévoir un mode vent et la réception d'une girouette-anémomètre électronique (NMEA) | 2026-11-02 | ACCEPTÉE (2026-11-16) |
| DEC-006 | Démarche de réalisation, ordre du projet et outil de prototype | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-007 | Périmètre fonctionnel du pilote et étapes de réalisation | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-008 | Capteurs embarqués et connectivité du socle | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-009 | Gabarit de bateau et exigences minimales du vérin | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-010 | Ordre de réalisation du socle : panneau local et arrêt matériel d'abord | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-011 | IMU 9 axes : ICM-20948 | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-012 | Accéléromètre séparé : LIS3DH | 2026-11-16 | ACCEPTÉE (2026-11-16) |
| DEC-013 | Précision de cap visée : ±2 à 4°, jusqu'à ±5° en conditions dégradées | 2026-11-16 | ACCEPTÉE (2026-11-16) |

DEC-001 et DEC-002 (organisation du vault) ne portent sur aucun choix technique.

## B. Cahier des besoins du pilote (copie)

**Ce que Mathieu veut de son pilote automatique, en une page.** Pour un voilier à barre franche jusqu'à 9 m ; bateau d'essai : Catalina Capri 22. Document maître du projet, établi à partir de la session du 2026-11-16.

### Comment lire ce document

- **Il résume, il ne décide pas.** Ce qui fait foi, ce sont les décisions DEC citées. Pour changer un besoin, on modifie ou on remplace la DEC, puis on met ce cahier à jour.
- **Une décision « proposée » n'est pas encore acceptée.** L'état de chaque DEC est indiqué entre parenthèses.
- La provenance de chaque choix (citation de Mathieu, revue du 2026-11-16) est dans « Registre d'approbation - session du 2026-11-16 ».
- Le détail technique reste dans les notes de travail : « grille-capacites-pilote » (section 16) et « Entrées-sorties du socle ».

### B.1 Démarche — « DEC-006 - Démarche de réalisation, ordre du projet et outil de prototype » *(acceptée le 2026-11-16)*

- Tout prévoir dans la conception, ajouter les éléments au fur et à mesure.
- Le pilote est d'abord construit avec le **vérin linéaire**. L'adaptation au ST1000+/ST2000+ vient ensuite, dans un projet séparé.
- Prototype et essais : **Node-RED intégré à Signal K** (sa place dans le système final n'est pas décidée).
- Actionneur : **vérin linéaire seulement** (« DEC-003 - Vérin linéaire commun, Milo en projet distinct »). Minimums : **course de 300 mm (330 idéal), force de 100 lbf**, davantage acceptable (« DEC-009 - Gabarit de bateau et exigences minimales du vérin »). Ces deux décisions sont acceptées depuis le 2026-11-16.
- Ordre dans le socle : **panneau local et arrêt matériel d'abord**, liaisons et tablette ensuite (« DEC-010 - Ordre de réalisation du socle - panneau local et arrêt matériel d'abord », acceptée le 2026-11-16).

### B.2 Ce que fait le pilote, par étape — « DEC-007 - Périmètre fonctionnel du pilote et étapes de réalisation » *(acceptée le 2026-11-16)*

| Famille | Socle (première version) | Extension (prévue, ajoutée ensuite) | Selon usage | Ultérieur |
|---|---|---|---|---|
| **Modes** | Cap compas · barre bloquée à un angle · non-follow-up · follow-up | Vent apparent · vent réel · suivi de route OpenCPN · anticipation par le vent (option C) | | |
| **Manœuvres** | Virement et empannage automatiques sur commande · séquences programmables (3 préréglages) · homme à la mer · retour au cap précédent | Esquive | | |
| **Alarmes** | Écart de cap · zone · haut-fond cartographique · sortie d'alarme au poste de barre | Vent · arrivée au waypoint | Haut-fond par sondeur | Évitement automatique |
| **Protections** | Table des défauts comme point de départ (réactions à fixer au chantier Sécurité) | | | |
| **Interface** | Boutons · écran tactile et affichage simple · veille physique · mobile, tablette ou PC (réglages, séquences, cartographie, route **et commande directe**) | Télécommande | | Commande vocale |
| **Données** | Angle de barre · courant et tension · journal · températures du moteur et du contrôleur | | | |

**Quatre règles transversales :**
1. La **veille physique** reprend toujours la main, sans écran ni liaison sans fil.
2. Une manœuvre ne part **jamais d'elle-même** : virement et empannage exigent une commande explicite et s'annulent par la veille.
3. Les **séquences** restent réglables et utilisables sans les capteurs supplémentaires (bôme, cellule de charge) : ceux-ci améliorent, ils ne sont jamais requis.
4. **Zones, OpenCPN et évitement sont des options** : disponibles seulement si le matériel nécessaire est présent et installé ; le pilote fonctionne sans elles (« DEC-004 - Prévoir l'évitement de zones et l'interface OpenCPN », acceptée le 2026-11-16).

### B.3 Capteurs et liaisons — « DEC-008 - Capteurs embarqués et connectivité du socle » *(acceptée le 2026-11-16)*

| Socle | Extension |
|---|---|
| GPS · IMU 9 axes **ICM-20948** (« DEC-011 - IMU 9 axes - ICM-20948 ») · accéléromètre séparé **LIS3DH** (« DEC-012 - Accéléromètre séparé - LIS3DH ») (seconde source) · capteur de bôme · cellule de charge sur l'écoute | Girouette-anémomètre électronique |
| NMEA 2000 · entrée et sortie NMEA 0183 · capteurs éloignés en nœuds NMEA 2000 | |

**Précision de cap visée :** ±2 à 4° en conditions normales, jusqu'à ±5° en conditions dégradées. Ce sont des cibles de départ, à confirmer par les essais. Les seuils de gîte et d'état de la mer qui définissent « dégradé » sont des paramètres réglables depuis l'interface (« DEC-013 - Précision de cap visée »).

### B.4 Ce qui n'est pas encore décidé

| Sujet | État | Où |
|---|---|---|
| Architecture du calculateur | Orientation vers l'hybride pypilot + façade ESP32 + `motor.ino` ; comparaison avec CON-002 à faire | « CON-008 - Architecture hybride pypilot, façade ESP32 et contrôle moteur séparé », « Q-008 - Calculateur et architecture de commande » |
| Modèle du vérin et effort à la barre | Vérin linéaire, au moins 300 mm et 100 lbf (décidé). Le modèle n'est pas choisi. Le vérin Fenix (300 N, environ 67 lbf annoncés) reste à réconcilier avec le minimum de force | « Q-002 - Effort réel à la barre », « DEC-003 - Vérin linéaire commun, Milo en projet distinct » *(acceptée le 2026-11-16)* |
| Budget | Socle chiffré à environ 1 715 $ CA, environ 715 $ au-dessus de l'enveloppe d'environ 1 000 $ | « Q-007 - Usage prioritaire, budget et moyens » |
| Sécurité et conduite en navigation | Chantier non ouvert ; réactions aux défauts à fixer | « Projet et périmètre » |
| Capteurs éloignés | Type du capteur de bôme, amplificateur de la cellule, format des messages NMEA 2000, usage de l'accéléromètre séparé | « Entrées-sorties du socle », section 9 |
| Séquences en angle mesuré | Proposition à évaluer | « grille-capacites-pilote », section 16 |
| Liaison façade ↔ pypilot, machine hôte, injection de l'anticipation | Inconnues | CON-008, « CON-009 - Script d'anticipation de la barre par le vent (spécification) » |
| Capteur de vent | Modèle non choisi (mode vent accepté, « DEC-005 - Prévoir un mode vent et une girouette-anémomètre NMEA ») | DEC-005 |
| Évitement automatique | Niveaux, limites de la manœuvre et source des zones à définir | DEC-004, « CON-007 - Évitement de zones avec un traceur type OpenCPN » |
| Finalité du pilote principal | L'Accueil parle d'aller « jusqu'au produit » ; le passage en projet personnel visait la conversion des ST | À confirmer |

### B.5 Rapport avec les documents existants

#### Cahier de conception V0.3 — rapprochement du 2026-11-16

« Conception_Pilote_Automatique_V0-3 » reste le document de **conception technique**. Il traite de la régulation, de l'actionnement, du simulateur et des portes de décision G0 à G5. Ce cahier-ci dit **ce que le pilote doit faire**. Les deux se complètent. Le tableau ci-dessous montre l'effet des DEC acceptées sur le registre D-01 à D-11. **Aucune décision D-xx n'est tranchée par ce rapprochement.**

| ID V0.3 | Sujet | Effet des DEC du 2026-11-16 | État |
|---|---|---|---|
| D-01 | Base de code embarquée | Le cahier V0.3 voyait Fenix comme candidat initial. CON-008 oriente maintenant vers pypilot (orientation seulement). | Ouvert |
| D-02 | Contrat contrôleur → moteur | Aucun | Ouvert |
| D-03 | Loi de cap | DEC-005 et DEC-007 ajoutent l'anticipation par le vent (option C), qui s'ajoutera à la loi de cap retenue | Ouvert |
| D-04 | Acquisition IMU | DEC-008 fixe une **IMU 9 axes** plus un accéléromètre séparé. Trois centrales industrielles (SBG, Xsens, VectorNav), proposées puis **écartées** par Mathieu le 2026-11-16 pour leur coût. **ICM-20948 (carte Adafruit 4554) retenue** par « DEC-011 - IMU 9 axes - ICM-20948 », le 2026-11-16; accéléromètre séparé LIS3DH retenu par « DEC-012 - Accéléromètre séparé - LIS3DH » | **Répondu** |
| D-05 | Vérin | DEC-003 : vérin linéaire seulement. DEC-009 : au moins 300 mm (330 idéal) et au moins 100 lbf. Le modèle sera choisi d'après le pourcentage d'utilisation en charge (M2) | Exigences fixées, modèle ouvert |
| D-06 | Driver moteur | DEC-007 exige la mesure du courant, de la tension et de la **température du contrôleur** : le driver retenu devra le permettre | Ouvert, contraint |
| D-07, D-08 | Gains selon la vitesse, filtrage de la houle | Aucun | Ouverts |
| D-09 | Simulateur principal | Aucun. Node-RED (DEC-006) sert aux essais de prototype ; il ne remplace pas le simulateur | Ouvert |
| D-10 | Communication et interface | **En grande partie répondu.** DEC-007 et DEC-008 fixent l'interface (boutons, écran, veille physique, tablette) et les liaisons (NMEA 2000, NMEA 0183) du socle. Reste l'**ordre de réalisation** à l'intérieur du socle : la recommandation de V0.3 (panneau local et arrêt matériel d'abord) est compatible, mais **non confirmée** | **Répondu par « DEC-010 - Ordre de réalisation du socle - panneau local et arrêt matériel d'abord »** |
| D-11 | Traitement de l'intégrale | Aucun | Ouvert |

**Deux écarts, où les DEC font foi :**
- **Hors périmètre de V0.3 (§2).** V0.3 excluait le « mode vent opérationnel » et le « suivi de waypoints en mer ». DEC-005 et DEC-007 les intègrent maintenant en **extension**. L'exclusion de V0.3 ne vaut donc plus que pour la première version, celle qui ferme la boucle de cap.
- **Bateau.** Réglé le 2026-11-16 par DEC-009 : voiliers à barre franche jusqu'à 9 m, avec le Capri 22 comme bateau d'essai. L'Accueil et « Projet et périmètre » sont harmonisés.

**Ce qui reste valable tel quel dans V0.3 :**
- les principes de sûreté de la §3.2 (déconnexion mécanique rapide, arrêt matériel indépendant du logiciel, superviseur indépendant). Ce sont des propositions qui alimenteront le chantier Sécurité ;
- les portes G0 à G5 ;
- la règle de ne rien acheter de définitif avant G1 et G4.
- Les sections 1 à 15 de « grille-capacites-pilote » datent du 2026-11-06. En cas d'écart, la section 16 et DEC-007 font foi.

### Liens
« Projet et périmètre » · « Registre d'approbation - session du 2026-11-16 » · « Questions ouvertes »
