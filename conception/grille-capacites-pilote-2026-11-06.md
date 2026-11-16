---
type: analyse
statut: en-cours
verification: a-verifier
date: 2026-11-06
aliases: [grille des capacités, capacités du pilote, étendue des fonctions du pilote, exigences du pilote]
---

# Grille des capacités du pilote — effet sur le vérin, le calculateur et l'interface

> **⚠️ Document dépassé — mise à jour du 2026-11-16.** Cette version du 6 novembre ne contient ni les choix de capacités ni les étapes (socle, extension, selon usage, ultérieur) fixés par Mathieu le 2026-11-16. La version à jour est dans le vault, `03 - Analyses/grille-capacites-pilote.md`, section 16. Les choix acceptés sont résumés dans `conception/cahier-des-besoins-et-decisions-2026-11-16.md` (DEC-007). Le contenu ci-dessous est conservé tel quel.

## 1. Objet et conclusion

Cette grille définit les capacités envisagées pour un pilote de barre franche sur le Capri 22. Elle sert à préparer le choix du vérin, du contrôleur moteur, du calculateur et de l'interface.

**Choisir les fonctions ne suffit pas à dimensionner le contrôleur moteur.** Les fonctions permettent de définir des **scénarios de travail**. Il faut ensuite les traduire en force, course, vitesse sous charge, fréquence d'utilisation et limites thermiques, puis lire les caractéristiques électriques du vérin retenu.

La démarche proposée : **usages → scénarios → exigences mécaniques → choix du vérin → exigences électriques → choix du contrôleur → essais**. Des retours en arrière seront nécessaires si un composant ne satisfait pas les exigences.

Cette grille accompagne la fiche [six-projets-pilotes-barre-detail-2026-11-06.md](../sources-brutes/six-projets-pilotes-barre-detail-2026-11-06.md) (notamment sa section 7.5 sur le dimensionnement du vérin).

## 2. Périmètre, état des décisions et niveau de confiance

**État des décisions au 6 novembre 2026.**
- Vérin linéaire : pièce commune retenue.
- Plateforme : ouverte (Fenix n'est plus le choix arrêté).
- Décisions d'intention : mode vent par girouette-anémomètre **électronique** NMEA ; interfaçage traceur (OpenCPN) via NMEA fortement souhaité ; évitement automatique de zones prévu dès la conception, implanté dans un chantier ultérieur.
- Interface : un mobile ou une tablette **dédiés** sont désormais possibles.
- Le chantier « sécurité et conduite en navigation » n'est **pas encore ouvert** : les réactions aux défauts proposées en section 9 sont des pistes, pas des exigences arrêtées.

Les priorités proposées ici (section 13) ne sont **pas** de nouvelles décisions.

**Niveau de confiance.** Cette version fusionne la grille initiale et une révision commentée fournie par Mathieu, dont les sources ont été revérifiées le 6 novembre 2026 (voir « Historique de révision »). Aucun relevé sur le bateau, aucun calcul complet de montage, aucune compilation ni aucun essai matériel n'a été réalisé. Les caractéristiques du vérin et les seuils d'acceptation restent à déterminer.

**Conventions.**
- **Documenté** : appuyé par une source citée.
- **Analyse** : conséquence technique tirée pour ce projet.
- **Proposition** : choix de conception ou d'organisation à évaluer.
- **À mesurer** : information nécessaire avant validation matérielle.

## 3. Corrections apportées au raisonnement initial

| Point initial | Correction | Conséquence pour le projet |
|---|---|---|
| Plus rapide, plus fréquent ou plus de débattement signifie plus de courant | Distinguer courant instantané, énergie consommée et échauffement | Évaluer séparément les contraintes électriques et thermiques |
| Un niveau faible/moyen/fort par mode suffit | La sollicitation dépend aussi du réglage, de la charge et de l'environnement | Définir des scénarios mesurables (section 14) |
| Follow-up : « arrêt au relâchement » | **Erreur de ma part.** En follow-up, on choisit un angle et la barre s'y rend puis s'arrête ; c'est en non-follow-up que la barre bouge tant qu'on appuie (vérifié dans plusieurs manuels Simrad et Furuno) | Corriger l'interface et les critères d'essai |
| Loch ou GPS équivalents pour le vent réel | Le référentiel (eau ou fond) doit être explicite | Documenter les données et le calcul retenus |
| Une zone dessinée devient une alarme | Les frontières et alarmes demandent une configuration précise | Vérifier la chaîne OpenCPN Draw + Watchdog sur la plateforme retenue |
| Évitement = changement immédiat de cap | Il faut une trajectoire praticable et une marge de manœuvre | Séparer alarme, proposition de trajectoire et commande automatique |
| Non-follow-up classé « faible » pour le vérin | Il peut demander la pleine puissance et atteindre une butée | Ne pas le classer faible par défaut |
| Alarmes techniques traitables plus tard | Certaines protections déterminent dès maintenant le matériel et le câblage | Définir les défauts et réactions dès le socle initial (proposition) |

## 4. Grandeurs à ne pas confondre

| Grandeur | Signification | Ce qu'elle permet de choisir |
|---|---|---|
| Force du vérin | Effort axial nécessaire selon la barre et la géométrie | Capacité mécanique, transmission |
| Course | Déplacement utile de la tige entre les positions extrêmes | Longueur et montage du vérin |
| Vitesse sous charge | Vitesse réelle lorsque le vérin fournit l'effort demandé | Rapidité de réponse |
| Courant en charge | Courant pendant un fonctionnement défini | Contrôleur, câblage, alimentation |
| Courants transitoires | Pointes au démarrage, lors d'inversions ou d'un blocage | Limitation, protections, tenue des composants |
| Énergie | Consommation cumulée dans le temps | Autonomie de la batterie |
| Activité thermique | Durée et intensité du travail, repos, température | Service admissible du vérin et du contrôleur |

**Puissance mécanique.** `P = F × v` (F en newtons, v en mètres par seconde). Par exemple, 300 N à 0,045 m/s donnent environ 13,5 W de puissance utile *(calcul)*. Cette relation ne donne pas directement le courant : la tension, les rendements de la vis et du moteur, et les caractéristiques du moteur interviennent aussi.

**Courants transitoires (documenté, Pololu).** Le courant de blocage (moteur alimenté mais immobile) peut atteindre une dizaine de fois le courant à vide. Un démarrage à pleine puissance absorbe brièvement ce courant de blocage, et une inversion brusque d'une pleine vitesse à l'autre en absorbe presque le double. Les moteurs à balais ne sont généralement pas faits pour rester bloqués longtemps. Idéalement, le contrôleur et l'alimentation supportent le courant de blocage ; sinon, il faut au minimum dépasser le courant à vide et utiliser la limitation d'accélération et de courant.

**Énergie et échauffement.** Bouger plus longtemps augmente généralement l'énergie consommée, sans augmenter forcément le courant instantané.

**Facteur de service.** C'est la part du temps pendant laquelle le vérin peut travailler. Il se lit avec ses conditions (charge, température, durée du cycle) : une valeur de 25 % n'autorise pas à fonctionner pendant n'importe quel quart d'une période. Il ne faut pas le confondre avec le **rapport cyclique PWM**, qui sert à commander la vitesse du moteur. Un moteur alimenté et bloqué chauffe sans bouger. *(Source Thomson citée par la révision, non relue.)*

## 5. Socle commun aux fonctions de pilotage

Les capteurs indiqués plus loin sont des dépendances supplémentaires ou particulières. Ils ne remplacent pas le socle nécessaire à la boucle de pilotage.

**Proposition de socle :**
- mesure de cap exploitable et datée pour les modes automatiques (une IMU 9 axes est une solution possible, pas une exigence universelle) ;
- contrôleur moteur adapté, avec limites de fonctionnement et gestion des commandes périmées ;
- commande de veille accessible et moyen de reprise manuelle ;
- surveillance de l'alimentation et des défauts pertinents ;
- identification claire de l'interface qui détient l'autorité de commande ;
- démarrage et redémarrage en veille ;
- journal permettant de comprendre une anomalie.

**Retour de position.** Il est requis pour le follow-up envisagé, et utile aux limites de position, à condition de détecter ses défauts. Un potentiomètre intégré au vérin mesure la position de la **tige** : obtenir l'angle de barre demande une calibration de la géométrie et suppose que la liaison mécanique est intacte.

## 6. Modes de pilotage

| Capacité | Fonction et dépendances | Effort, vitesse et activité du vérin | Interface et validation |
|---|---|---|---|
| **Cap compas** | Maintien d'un cap ; mesure de cap et dynamique adaptées | Scénario de référence ; effort et activité dépendent du bateau, de la mer et du réglage | Auto, veille, ±1° / ±10°. Vérifier stabilité, dépassement et réaction à la perte du cap |
| **Vent apparent** *(intention)* | Maintien d'un angle de vent apparent ; données de vent valides et datées, plus le socle | Activité potentiellement accrue, mais pas systématiquement forte ; filtrage et équilibre sous voiles déterminants | Angle demandé et mesuré, source et état. Tester variations de vent, données figées, perte de source |
| **Vent réel** | Maintien d'un angle calculé ; vent apparent + vitesse dans un référentiel défini | Aucune réduction de sollicitation garantie avant essai | Afficher le référentiel et la validité. Vérifier les calculs et les changements de source |
| **Suivi de route** *(souhaité)* | Correction de l'écart à une route ; position, données de navigation et socle | Modéré en régime établi, mais soutenu lors d'une reprise de route ou d'un changement de branche | Route active, écart, prochaine action. Tester perte de données et transition de waypoint |
| **Follow-up (FU)** | On choisit un angle de barre ; la barre le rejoint puis le conserve. Retour de position requis | Effort lié à la charge ; vitesse et amplitude à limiter | Afficher angle demandé et mesuré. Vérifier que le changement de mode ne provoque aucun mouvement inattendu |
| **Non-follow-up (NFU)** | Le vérin bouge tant qu'on appuie | Peut demander la pleine puissance et atteindre une butée | Boutons bâbord / tribord ; arrêt au relâchement, et expiration de la commande si la liaison est perdue |

**Follow-up et non-follow-up (documenté).** Dans les manuels Simrad consultés, en FU la barre se rend à l'angle commandé puis s'arrête ; en NFU elle bouge tant que le bouton ou le levier est actionné. Les manuels précisent aussi qu'en FU on ne peut pas reprendre la barre à la main. Si une autorisation maintenue (par exemple « bouton à garder enfoncé ») est souhaitée en FU, elle doit être ajoutée explicitement à la conception.

**Vent réel (documenté, Raymarine).** L'angle et la vitesse du vent réel (TWA, TWS) se calculent à partir du vent apparent et de la **vitesse sur l'eau** (loch) ; le **cap** sert en plus à obtenir la direction du vent par rapport au nord (TWD). La vitesse sur le fond (GPS) sert au « vent sol », qui est une autre grandeur. En présence de courant, les deux calculs diffèrent. Sur un lac, le courant est généralement faible, mais la grille doit décrire le calcul effectivement choisi, pas seulement l'étiquette « vent réel ».

## 7. Manœuvres

| Capacité | Exigence proposée | Effet sur le vérin | Point à valider |
|---|---|---|---|
| **Virement automatique** | Changement d'amure avec angle ou trajectoire réglables et possibilité d'annuler | Vitesse sous charge et durée de travail importantes ; angle maximal maîtrisé | Rotation suffisante sans saturation prolongée ; comportement si le bateau perd de la vitesse |
| **Empannage automatique** | Fonction distincte du virement, avec conditions d'autorisation et confirmation explicites | Manœuvre sous charge variable ; priorité à la maîtrise de la rotation | Coordination avec la conduite du bateau et des voiles ; sa validation ne découle pas de celle du virement |
| **Esquive** | Changement temporaire de consigne, ou commande manuelle, clairement identifié | Dépend de l'écart demandé, de la vitesse du bateau et des limites réglées | Accès immédiat, annulation, limites, mode conservé après la manœuvre |
| **Retour au cap précédent** | Restauration volontaire d'une consigne mémorisée | Peut demander une manœuvre importante | Afficher la consigne restaurée et vérifier que le retour reste approprié |

**Commentaire.** Un changement de cap important ne justifie pas automatiquement le débattement maximal : la trajectoire et la vitesse de rotation se règlent. Retrouver le cap précédent ne veut pas dire retrouver la route précédente, et peut ramener vers la zone qui avait motivé l'esquive.

## 8. Navigation, zones et alarmes

| Fonction | Données nécessaires | Exigence et limite |
|---|---|---|
| Alarme d'écart de cap | Cap, consigne, mode, durée de dépassement | Seuil et temporisation réglables ; tenir compte d'une manœuvre volontaire |
| Alarme de vent | Angle et vitesse de vent valides | Préciser la variation surveillée, le filtrage et la durée ; distinguer vent fort et capteur défaillant |
| Arrivée au waypoint | Position et route active | Distinguer l'avertissement d'arrivée de l'autorisation de changer de branche |
| Alarme de zone | Position, frontière configurée, et éventuellement route et vitesse sur le fond | Tester la proximité, le franchissement prévu et la perte de position |
| Alarme de haut-fond | Cartographie ou zone définie ; éventuellement sondeur | Une alarme cartographique dépend des données et du niveau d'eau ; un sondeur mesure sous le bateau, sans garantir une anticipation suffisante |
| Évitement automatique *(intention, chantier ultérieur)* | Position, géométrie des zones, mouvement du bateau, contraintes de navigation | Demande une trajectoire admissible, des marges, et un comportement prévu quand l'évitement est impossible |

**OpenCPN Watchdog (documenté).** Le greffon Watchdog propose quatre alarmes de frontière : franchissement prévu (la route et la vitesse actuelles amènent à une frontière en moins de N minutes), proximité (position à moins de N milles d'une frontière), inclusion (sortie d'une zone) et zone de garde AIS. Les frontières doivent être dessinées avec **OCPN Draw**. Watchdog **alerte** (son, fenêtre, commande système, courriel) mais ne commande pas le pilote ; il peut par ailleurs surveiller pypilot. Ces fonctions ne constituent donc pas un évitement automatique ; leur disponibilité est à vérifier sur la plateforme retenue, notamment si la tablette devient le traceur principal.

**Proposition pour l'évitement ultérieur.** Prévoir dès maintenant une interface de demande de trajectoire, mais conserver une **autorité unique** qui arbitre les commandes. Développer successivement l'alarme, l'affichage d'une trajectoire proposée, puis seulement la commande automatique, après validation.

La marge d'anticipation devra couvrir l'âge des données, le délai de traitement, la réponse du bateau, l'incertitude de position et la marge cartographique. Le délai de réaction ne se choisit pas uniquement d'après la vitesse du vérin.

## 9. Protections et réactions aux défauts *(propositions, chantier sécurité non ouvert)*

Une **alarme** informe le barreur. Une **protection** modifie ou interrompt le fonctionnement. Les deux se spécifient séparément.

| Événement | Réaction proposée ou décision à documenter | Essai nécessaire |
|---|---|---|
| Mise sous tension ou redémarrage | Veille ; aucune reprise automatique de mouvement | Coupures et redémarrages dans différents états |
| Commande NFU périmée | Arrêt du mouvement après un délai défini | Perte du message de relâchement, rupture radio |
| Cap invalide ou figé | Ne plus utiliser cette donnée ; réaction du moteur et alarme à définir | Déconnexion, valeur figée, valeur incohérente |
| Perte du vent ou des données de route | Transition définie : veille, ou repli explicitement validé, avec signalement | Perte de source dans chaque mode |
| Perte de la tablette | Réaction selon son rôle : affichage seul, commande ou calculateur | Couper chaque liaison séparément |
| Surintensité ou blocage | Limitation ou coupure, avec seuil et délai adaptés ; éviter les répétitions destructrices | Essai contrôlé dans les limites du matériel |
| Retour de position invalide | Interdire les fonctions qui en dépendent ; signaler le défaut | Débranchement, valeurs hors plage |
| Sous-tension ou surchauffe | Réaction définie avant un comportement électronique imprévisible | Essai d'alimentation, observation thermique |
| Commandes simultanées | Priorité explicite ; veille prioritaire ; commandes anciennes invalidées | Tablette, boutons et télécommande en concurrence |

**Commentaire.** La veille électrique ne garantit pas que la barre soit libre. Le dégagement mécanique du vérin se vérifie séparément, y compris sous charge. Limites de position, fins de course et protections électriques sont complémentaires.

## 10. Interface

| Option | Intérêt | Vérification avant adoption |
|---|---|---|
| Mobile ou tablette dédiés | Affichage riche, réglages, journal, éventuellement cartographie (OpenCPN sur Android) | Lisibilité en plein soleil, alimentation, fixation, pluie, compatibilité des fonctions, rôle exact en cas de déconnexion |
| Boutons physiques | Commande au toucher, rapide, sans regarder | Ergonomie, étanchéité, rebonds, comportement d'un bouton bloqué |
| Télécommande | Commande depuis l'avant du bateau | Portée, piles, expiration des commandes, aucun mouvement après reconnexion |
| Commande vocale hors ligne | Mains libres | Taux de fausses commandes dans le vent ; validation distincte avant toute autorité de mouvement |
| Combinaison | Sépare l'affichage détaillé des commandes essentielles | Une autorité cohérente, état visible, veille accessible indépendamment de l'écran |

**Proposition.** Privilégier une combinaison écran + commandes physiques essentielles. La voix reste une option expérimentale et ne remplace pas la veille physique.

## 11. Calculateur et communications

La complexité d'une fonction ne se traduit pas directement en besoin de processeur puissant. Surveiller une frontière simple peut être léger en calcul et pourtant difficile à valider ; à l'inverse, cartographie et reconnaissance vocale demandent davantage de mémoire et de ressources.

Il faut distinguer :
- la boucle de commande, dont les délais doivent rester maîtrisés ;
- la réception et la validation des données ;
- l'affichage et la journalisation ;
- la planification de route ou d'évitement.

Le choix NMEA doit préciser la version, le transport, l'interface électrique, les messages acceptés, les unités, le référentiel du cap, l'âge maximal des données et la priorité des sources. Recevoir une trame ne valide pas le comportement du pilote.

## 12. Affichage et journal

| Information | Utilité | Précaution |
|---|---|---|
| Mode, état et interface active | Comprendre qui commande | Distinguer mode demandé et mode réellement actif |
| Cap et consigne | Évaluer la tenue de cap | Référentiel magnétique ou vrai explicite |
| Angle demandé et position mesurée | Comprendre la réponse du vérin | Signaler estimation, calibration ou mesure invalide |
| Vent, vitesse, écart de route | Comprendre les modes spécialisés | Afficher source et validité |
| Courant, tension, énergie | Surveiller l'effort et l'autonomie | Documenter le point de mesure ; le courant du moteur ne représente pas toute la consommation de la batterie |
| Défauts et transitions | Expliquer les arrêts et changements de mode | Horodatage cohérent, événements conservés |

Le journal devrait contenir au minimum : temps, mode, consigne, cap, commande moteur, position si disponible, courant, tension, défauts et âge des données utiles. Sa fréquence et son stockage se définissent sans bloquer la boucle de commande.

## 13. Proposition de priorités

| Étape | Fonctions proposées | Condition pour poursuivre |
|---|---|---|
| **Socle initial** | Cap compas, veille physique, non-follow-up, protections, courant et tension, journal | Fonctionnement reproductible au banc, puis en navigation calme |
| **Extension fonctionnelle** | Vent apparent, route OpenCPN, alarmes de zones, virement réglable | Validation de chaque mode, des pertes de source et des transitions |
| **Extensions selon usage** | Vent réel, follow-up, affichages supplémentaires | Besoin démontré et capteurs adaptés |
| **Chantier ultérieur** | Évitement automatique | Alarmes et trajectoires proposées validées avant toute autorité automatique |
| **Options à justifier** | Empannage automatique, commande vocale | Bénéfice d'usage suffisant et validation spécifique |

Ce phasage est une proposition. Le mode vent apparent (décision d'intention) pourrait entrer dans la première version si c'est ta priorité d'usage, tout en restant testé après le socle compas et les protections.

## 14. Scénarios d'essai à préparer

| Scénario | Mesures à relever | Critère d'acceptation à fixer avant l'essai |
|---|---|---|
| Maintien de cap | Erreur, activité du vérin, courant, énergie | Erreur admissible, pas d'oscillation durable |
| Petit changement de consigne | Temps de réponse, dépassement | Réponse maîtrisée sans inversions excessives |
| Manœuvre importante | Rotation, position, courant, saturation | Trajectoire acceptable, limites respectées |
| Fonctionnement prolongé | Température, énergie, repos | Respect des conditions thermiques des composants |
| Perte d'une source | Délais, mode, commande moteur | Réaction conforme à la table des défauts |
| Changement d'interface | Commandes reçues, autorité active | Aucun mouvement venant d'une commande ancienne |
| Approche simulée d'une zone | Position, délais, distance d'alarme | Avertissement suffisamment anticipé dans le scénario retenu |

**Scénarios probablement dimensionnants pour le contrôleur** *(analyse, à confirmer par la mesure)* : virement sous charge, rafales en mode vent, blocage en butée ou grippage, inversions rapides de sens. Ce sont eux qui fixent le courant de pointe et l'échauffement ; ils méritent d'être mesurés en premier dès qu'un vérin est disponible.

Les premiers essais de logique de zone et de données invalides peuvent se faire par simulation ou rejeu de données (le simulateur NMEA déjà présent dans le projet en est un point de départ possible). Les essais en navigation viennent ensuite, dans un espace adapté : il n'est pas nécessaire d'approcher un vrai haut-fond pour tester une alarme.

## 15. Informations nécessaires au choix du matériel

1. Relever les positions des deux articulations du vérin, la course possible et les angles de barre utiles (les cotes de montage de la ST1000+ restent une référence géométrique).
2. Mesurer les efforts dans des situations représentatives, pas seulement par temps calme ou à une seule allure.
3. Fixer les vitesses de barre et les durées de manœuvre souhaitées, avec des limites explicites.
4. Établir les scénarios de fonctionnement prolongé et les conditions thermiques du montage.
5. Comparer les vérins sur leurs courbes force/vitesse, courants (en charge et au blocage), facteur de service, maintien hors tension, étanchéité et efforts latéraux admissibles.
6. Choisir le contrôleur selon la tension, le courant continu réel, les transitoires admissibles (idéalement le courant de blocage), la limitation de courant, les inversions et la dissipation dans le boîtier prévu.
7. Dimensionner l'alimentation, les conducteurs, les connecteurs et les protections avec l'ensemble retenu.
8. Vérifier le montage par les scénarios d'essai avant de considérer le choix comme validé.

**Conclusion de conception.** La grille définit ce que le pilote doit faire et comment son comportement sera vérifié. Le choix du contrôleur découlera ensuite des caractéristiques mesurées ou garanties du vérin et du montage, plutôt que d'un classement des modes par puissance supposée.

---

## 16. Cases à cocher

Pour chaque capacité, indique l'étape : **socle**, **extension**, **selon usage**, **ultérieur** ou **non**. Aucune case n'est cochée d'avance ; les décisions d'intention sont rappelées entre parenthèses.

**Modes de pilotage**
- [ ] Cap compas
- [ ] Vent apparent *(intention)*
- [ ] Vent réel (référentiel : eau / fond)
- [ ] Suivi de route OpenCPN *(souhaité)*
- [ ] Follow-up (choisir un angle de barre)
- [ ] Non-follow-up (barre tant qu'on appuie)

**Manœuvres**
- [ ] Virement automatique
- [ ] Empannage automatique
- [ ] Esquive
- [ ] Retour au cap précédent

**Navigation, zones et alarmes**
- [ ] Alarme d'écart de cap
- [ ] Alarme de vent
- [ ] Arrivée au waypoint
- [ ] Alarme de zone
- [ ] Alarme de haut-fond (cartographie / sondeur)
- [ ] Évitement automatique *(intention, chantier ultérieur)*

**Protections** *(chantier sécurité non ouvert)*
- [ ] Table des défauts de la section 9 retenue comme point de départ

**Interface**
- [ ] Mobile ou tablette dédiés (rôle : affichage / commande / calculateur)
- [ ] Boutons physiques
- [ ] Télécommande
- [ ] Commande vocale hors ligne
- [ ] Veille physique accessible indépendamment de l'écran

**Données et journal**
- [ ] Affichage de l'angle de barre
- [ ] Mesure de courant et de tension
- [ ] Journal pour le réglage et les anomalies

---

## Historique de révision

- **2026-11-06, version initiale** : grille par familles avec effet qualitatif (faible / moyen / fort) sur le vérin.
- **2026-11-06, révision fusionnée** : intégration d'une version révisée fournie par Mathieu, après vérification des sources. Vérifié : définitions FU / NFU (manuels Simrad et Furuno ; le lien du manuel FU80 cité par la révision n'a pas pu être ouvert), calcul du vent réel (glossaire Raymarine), alarmes de frontière Watchdog et rôle d'OCPN Draw (manuel OpenCPN), courants de blocage et d'inversion (Pololu). Non relu : document Thomson sur le facteur de service. Conservés de la version initiale : explications de vocabulaire, cases à cocher (adaptées au phasage), lien vers la fiche des six projets. Ajoutés : exemple de puissance mécanique, scénarios probablement dimensionnants, rappel du chantier sécurité non ouvert. Propriétés gardées selon la convention du vault (`statut: en-cours`, `verification: a-verifier`) plutôt que les valeurs proposées par la révision.

## Sources

- [S1 — Pololu : choix du moteur, de l'alimentation et du contrôleur](https://www.pololu.com/docs/0J73/4.1)
- [S2 — Thomson : caractéristiques et facteur de service des actionneurs](https://www.thomsonlinear.com/downloads/actuators/Precision_Linear_Actuators_ctuk.pdf) *(non relu)*
- [S3 — Simrad : manuel FU80/NF80/QS80](https://softwaredownloads.navico.com/Simrad/SimradYachting_Software%20-%20Copy/Downloads/documents/FU80-NF80-QS80_UM_EN_988-10199-005_w.pdf) *(lien non ouvrable)* ; vérification faite sur : [Simrad NSO evo3](https://manualslib.com/manual/1398270/Simrad-Nso-Evo3.html?page=57), [Simrad AP35](https://www.manualslib.com/manual/800371/Simrad-Ap35.html?page=19), [Furuno NavPilot 500](https://www.manualsdir.com/manuals/105001/furuno-navpilot-500.html?page=34)
- [S4 — Raymarine : glossaire et calcul du vent réel](https://docs.raymarine.com/81406/en-US/latest/SailingGlossary-71147499.html)
- [S5 — OpenCPN : Watchdog et alarmes de frontière](https://opencpn-manuals.github.io/main/watchdog/index.html)
- [S6 — OpenCPN Draw : objets et frontières](https://opencpn-manuals.github.io/main/odraw/index.html) *(non relu directement ; son rôle est confirmé par le manuel Watchdog)*
