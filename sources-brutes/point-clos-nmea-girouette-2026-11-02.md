# Point clos : girouette-anémomètre NMEA et pilotes (Fenix, pypilot)

Rédigé le 2026-11-02. **Statut : NOTE DE CONNAISSANCE PROVISOIRE (à vérifier).** Clôt le point « NMEA girouette (windvane) » de la session. Elle ne concerne que la girouette **électronique** ; les régulateurs d'allure à girouette **mécaniques** sont hors sujet (Mathieu a confirmé le 2026-11-02 qu'il ne s'agit pas d'une girouette mécanique).

**Non exécuté :** lecture de code seulement. **Décision de Mathieu (2026-11-02)** : voir `conception/decisions-et-dispositions-2026-11-02.md`, DP-03.

**Rangement :** `sources-brutes/`. Analyse détaillée : `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md` ; concept lié : `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`. Version du vault : `04 - Connaissances/Girouette-anémomètre NMEA et pilotes - point clos.md`.

Légende : **CONFIRMÉ** = lu dans le code ou la documentation · **INFÉRENCE** = déduit · **HYPOTHÈSE** = non vérifié · **À VÉRIFIER** = question ouverte · **NON EXÉCUTÉ** = lecture seule. Statut d'une décision : **PROPOSÉE** (recommandation) · **À DÉCIDER** (par Mathieu) · **VALIDÉE** (aucune à ce jour dans ce dépôt).

---

## Mises à jour postérieures à la rédaction (2026-11-02)

- Le **commentaire sur l'issue n° 13** de Fenix a été publié (2026-11-01).
- La **cible de 80 %** est confirmée : `targetFeedforwardShare()` renvoie `0.80f` (`WindFeedforwardEvaluatorSimple.h`).
- **Reste À VÉRIFIER** : le feedforward vent agit-il en mode compas, ou seulement dans les modes vent ?

## 1. Ce que la lecture du code et de la documentation établit

**Fenix** (lu dans cette session, rien n'est testé) :
- **Réception.** `IF_NMEA.cpp` et `emcNMEA.cpp` traitent les phrases **MWV** et **VWR** : angle de vent apparent, et direction du vent vrai dans le cas de MWV. VWR est marquée obsolète dans le code. La vitesse fond est aussi reçue.
- **Modes (RELEASE.md).** Le mode Vent (depuis la v2.6.B2) exige une source de vent externe (AP-30). La réception des vents réel et apparent est notée comme partiellement implémentée (AP-26). Un mode « Aile » maintient l'angle de vent apparent (AP-29). Le virement en mode Vent est partiel (AP-37) ; il est impossible en mode Nav (AP-38). Nuance : le texte du 2026-10-30 parlait d'un « angle de vent relatif » ; RELEASE.md distingue vent réel et vent apparent selon le mode. À préciser dans le guide de l'utilisateur.
- **Données périmées.** Les valeurs de vent ne sont considérées valides que si les données sont récentes (`MAX_VWR_TIME`, valeur non lue).
- **Anticipation par le vent** (`WindFeedforward.h`, appelée à chaque boucle) : le modèle utilise la **vitesse** et l'**angle du vent apparent**, filtrés sur 1 s, avec un seuil d'activation de 0,6 m/s (arrêt à 0,4 m/s). Sa table de 36 coefficients est **un jeu d'exemple à remplacer par des coefficients identifiés pour le bateau**. Sa sortie est bornée à ±10° de barre. Si la mesure devient invalide, la sortie décroît vers zéro en 1,5 s. Je n'ai pas vérifié si cette anticipation agit dans tous les modes ou seulement en mode Vent.
- **Issue #13** : le ratio qui règle l'importance de cette anticipation ne peut que baisser, tant que la ligne 1775 d'`Autopilot.cpp` n'est pas corrigée (voir l'analyse des dépôts, 3.2.2).

**pypilot** (manuel et code lus) : modes **Wind** (angle de vent apparent, utile au près) et **True Wind** (combine vent apparent et vitesse pour le vent réel, utile au portant). Les données de vent arrivent par le NMEA 0183 ou par Signal K.

**Nautinect** : le README annonce le vent apparent et réel comme sources de cap (phrases MWV analysées, PGN de vent 130306) ; ce n'est **pas confirmé dans le code source lu** (voir l'analyse des dépôts, 3.3).

**Milo, SimplePilot** : aucune entrée de vent dans le code lu.

## 2. Ce que la girouette doit fournir

- **Pour Fenix** : une phrase NMEA 0183 **MWV** (angle et vitesse du vent, avec l'indication de référence « relatif » ou « vrai »). Un capteur qui parle seulement NMEA 2000 (PGN de vent 130306) exigerait une passerelle NMEA 2000 vers 0183, car Fenix n'a pas d'entrée NMEA 2000. Les modèles de capteurs ne sont pas examinés ici.
- **Pour pypilot** : du NMEA 0183 ou une source Signal K.

## 3. Précautions

- L'angle de vent apparent mesuré en tête de mât est faussé par la **gîte** et par le mouvement du mât. Un pilote haut de gamme (guide de réglage B&G H5000) propose une correction de gîte et de mouvement pour le mode vent ; un autre constructeur (NKE) corrige le vent du mouvement du bateau (d'après un résumé d'une conversation antérieure). C'est lié à la note de concept sur l'anticipation par capteurs inertiels.
- Le mode Vent ne sert pas à éviter les obstacles et ne remplace pas la veille : il suit un angle de vent, pas une trajectoire.
- Virer ou empanner automatiquement est un point de sécurité : le virement automatique au portant est désactivé par sécurité chez un constructeur (d'après un résumé d'une conversation antérieure, non revérifié ici), et la prise en charge du virement est partielle ou absente dans Fenix.
- Une alarme de changement de vent existe chez Raymarine (ST4000+), selon une conversation antérieure : idée possible, non étudiée.

## 4. Lien avec les décisions de Mathieu

- **Décision (2026-11-02) :** la conception doit prévoir un **mode vent** et la réception, par le système du pilote, du signal NMEA d'une girouette-anémomètre **électronique**, qui devient **une donnée de plus pour la gestion du gouvernail** (et pas seulement un mode isolé). Pas de girouette mécanique.
- Le mode compas reste la base. *(Phrase d'origine retirée : « un mode vent n'a pas été demandé », devenue inexacte.)*

**Dispositions proposées par Claude (non validées par Mathieu) pour que cette décision reste réalisable :**
1. Une **entrée NMEA 0183** capable de recevoir la phrase **MWV** (et la vitesse), idéalement branchée **directement au pilote** et non via l'ordinateur du traceur : le vent ne doit pas dépendre d'un appareil dont on peut perdre l'affichage ou la liaison. Le port prévu pour le traceur (disposition 4 de `conception/decisions-et-dispositions-2026-11-02.md (DP-02)`) peut être le même ou un second, à décider.
2. Une **validité des données de vent** avec délai d'expiration, comme le fait Fenix : si le vent manque ou devient douteux, le pilote **revient au mode compas** et alerte, sans garder une consigne figée.
3. Trois usages du vent à distinguer dans la conception : maintenir un **angle de vent** (mode vent), **anticiper** le moment de lacet dû au vent (feedforward, avec des coefficients à identifier pour ce bateau), et plus tard une éventuelle **alarme de changement de vent**.
4. Un emplacement pour une **correction de la gîte et du mouvement** du vent apparent, à relier à la note de concept sur l'anticipation par capteurs.
5. **Pas de virement ni d'empannage automatique** par défaut : c'est un point de sécurité, et la prise en charge est partielle dans Fenix.
6. Une **calibration** de la girouette (décalage d'alignement, étalonnage de la vitesse), à prévoir dans la procédure de mise en service.

## 5. Ce qui reste ouvert

- Valeur de `MAX_VWR_TIME`, et validité du mode Vent de Fenix en pratique (version bêta, virement partiel).
- Savoir si l'anticipation par le vent agit en mode compas, et ses coefficients pour un petit voilier.
- Choix éventuel d'un capteur de vent (sortie NMEA 0183, alimentation, fixation en tête de mât, coût) : non étudié.
- Comportement réel de la correction par le bug de l'issue #13 sur un bateau.
- Un ou deux ports NMEA 0183 sur le pilote (traceur et girouette).

## Sources

- Dépôt Fenix : `IF_NMEA.cpp`, `emcNMEA.cpp`, `Autopilot.cpp`, `WindFeedforward.h`, `RELEASE.md`.
- Manuel pypilot ; README de Nautinect ; guide de réglage B&G H5000 (copie sur vs.j109.org).
- Conversations antérieures de Mathieu (2026-10-30), utilisées comme contexte et marquées « d'après un résumé » lorsqu'elles n'ont pas été revérifiées.
- `sources-brutes/analyse-depots-open-source-pilotes-2026-11-02.md`, `conception/concept-anticipation-barre-capteurs-inertiels-2026-11-02.md`.
