# Fenix — anticipation du vent (wind feedforward) : explication

Rédigé le 2026-10-26 à partir d'une lecture du commit `b8410e5`
(2026-10-23, « Add wind feedforward and tuning updates »,
https://github.com/spascual90/Fenix/commit/b8410e5), source n° 1 du registre.

**Fichiers lus en entier ou en partie :** `WindFeedforward.h`, `WindFeedforward.cpp`,
`Autopilot.cpp` (fonctions `compute_OperationalMode`, `computeLongLoop`,
`getWindDir`, `getWindSpeed`, `updateWindFeedforwardEvaluation`),
`ActuatorManager.cpp/.h` et `libraries_ext/PID_v1_ext.cpp` (passages touchant au vent).
**Ajouté le 2026-10-26 (2e lecture) :** `WindFeedforwardEvaluatorSimple.cpp` et `.h` en entier.
**Non exécuté :** rien n'a été compilé ni testé. Tout ce qui suit est une lecture de code.

Légende : **CONFIRMÉ** = lu dans le code · **À VALIDER** = observation ou hypothèse.

---

## 1. L'idée en une phrase

Un PID corrige **après** que le bateau a dévié. Le vent pousse le bateau tout le temps.
Le feedforward **calcule à l'avance** de combien le vent fait tourner le bateau,
et donne tout de suite au PID un coup de barre dans l'autre sens, sans attendre l'erreur de cap.

## 2. Le trajet de l'information (5 étapes)

```
Vent (NMEA) ──► [1] WindFeedforward ──► moment de lacet (N·m)
                                              │
                                  [2] conversion en degrés de barre
                                              │
                         × ratio d'étalonnage × facteur de vitesse
                                              │
                                  [3] ajouté à la sortie du PID
                                              │
                                  [4] barre = vérin bouge
                                              │
                    [5] un évaluateur compare le résultat et corrige le ratio
```

### Étape 1 — Estimer la force du vent sur le cap (`WindFeedforward.cpp`)

**CONFIRMÉ.** Formule : `moment = kAir × vitesse² × Cn(angle)`

| Terme | Sens |
|---|---|
| `vitesse` | vitesse du vent en m/s (au carré : un vent deux fois plus fort pousse quatre fois plus) |
| `angle` | angle du vent par rapport à l'étrave |
| `Cn` | coefficient lu dans une table de 36 valeurs (un point tous les 10°), interpolée linéairement |
| `kAir` | constante = 0,5 × densité de l'air × surface latérale × longueur de référence. Valeur de départ dans le code : **0,50** (constructeur d'`ActuatorManager`) |

La table `Cn` est symétrique : Cn(−γ) = −Cn(γ), nulle à 0° et 180°, maximale vers 90° (1,00) et 270° (−1,00).
Sens : un vent venant du travers fait le plus tourner le bateau ; vent debout ou vent arrière, presque rien.

Protections prévues dans le code :

| Protection | Valeur | Rôle |
|---|---|---|
| Filtre d'entrée | 1 000 ms | lisse le vent (filtré en composantes x/y, pas en angle, pour éviter le saut 359° → 0°) |
| Hystérésis | démarre à 0,6 m/s, s'arrête à 0,4 m/s | évite que la fonction clignote par vent très faible |
| Plafond | ±100 N·m | limite le moment calculé |
| Vent invalide | décroissance sur 1 500 ms | si le capteur se tait, la correction retombe doucement à zéro au lieu de rester figée |
| Cadence | un calcul toutes les 1,5 s au maximum | entre deux, la dernière valeur est renvoyée |

### Étape 2 — Convertir en degrés de barre

**CONFIRMÉ** (`getWindFF`) : `degrés = −moment × 0,1`, limité à ±10°.
Le signe est inversé volontairement : on pousse **contre** le vent. Le coefficient 0,1 est une
conversion fixe, sans lien visible avec une propriété du bateau.

### Étape 3 — Injecter dans le PID (`PID_v1_ext.cpp`)

**CONFIRMÉ.** Dans `ActuatorManager`, la valeur est multipliée par le **ratio d'étalonnage**
(`windFFratio`, borné entre 0,5 et 2,0) puis passée au PID avec le **facteur de vitesse**
du bateau. Le PID la convertit en unités de barre (× 10, car 1 unité = 0,1°) et la **somme** :

`sortie = P + I + D + FF(modèle de référence) + windFF`

Le terme intégral (I) n'a donc plus à « apprendre » seul l'effet du vent.

### Étape 4 — Quand c'est actif

**CONFIRMÉ.** `compute_OperationalMode` appelle `update_windFF` à chaque cycle avec la vitesse
et la direction du vent. `getWindSpeed()` / `getWindDir()` ne rendent des données que si le mode
vent est **AWA** (angle de vent apparent) ou **TWA** (vent vrai) **et** que la donnée NMEA est valide.
Sinon ils rendent −1 / −360 et le calcul reçoit « vent invalide ».

### Étape 5 — L'évaluateur qui ajuste le ratio (auto-étalonnage)

**CONFIRMÉ** (`WindFeedforwardEvaluatorSimple.cpp/.h` lus en entier). Appelé à chaque boucle longue
par `updateWindFeedforwardEvaluation()`. Il fonctionne comme une petite machine à 4 états :

| Phase | Ce qui se passe | Durée |
|---|---|---|
| Repos | attend que les conditions soient bonnes | — |
| Qualification | vérifie que tout est **stable** | 10 s de stabilité continue |
| Mesure | accumule les moyennes pondérées par le temps | 7 s de stabilité |
| Estimation prête | fournit `Cwind`, puis retourne au repos (`acknowledgeEstimate`) | — |

**Ce qu'il exige** (sinon il rejette, 14 motifs prévus) :
pilote actif · vent valide · vent d'au moins 0,5° de barre · intégrale autorisée et non saturée ·
feedforward non saturé · barre non saturée · changement de consigne = abandon immédiat.
Une interruption de plus de 0,5 s en mesure, ou un intervalle entre échantillons de plus de 1 s, annule tout.

**Critère de stabilité** : trois moyennes mobiles (constante 3 s), une pour la correction vent, une pour le
cap, une pour la part intégrale. Chacune doit varier lentement :

| Signal | Variation maximale tolérée |
|---|---|
| Correction vent | 0,17 °/s |
| Cap | 0,97 °/s |
| Part intégrale | 0,057 °/s |

**Le calcul** (c'est le cœur) :

`barre statique = feedforward appliqué + intégrale`   (moyennes sur les 7 s)

`Cwind = 0,8 × barre statique ÷ feedforward appliqué`

**Lecture simple :** l'auteur vise que le **feedforward porte 80 %** de la barre nécessaire et que l'intégrale
n'en porte que 20 %. `Cwind` est le facteur à appliquer au ratio :

| Situation mesurée | Intégrale / feedforward | `Cwind` | Effet voulu |
|---|---|---|---|
| Feedforward fait tout le travail | 0 | 0,8 | ratio réduit de 20 % |
| Partage exact visé | 0,25 | 1,0 | ratio inchangé |
| L'intégrale compense beaucoup | 1,0 | 1,6 | ratio augmenté de 60 % |

Un second calcul (régression `XY ÷ XX`) est fait mais sert **seulement de contrôle de plausibilité**
(rejet si le signe est faux ou si l'échelle sort de 0,1–10). Son résultat n'est pas utilisé pour corriger.
Les lignes qui l'exposaient sont commentées dans le code.

---

## 3. Ce que ça change pour ton projet

- Le gain est surtout visible **au près et au travers par vent établi** : le bateau a tendance
  à lofer ou à abattre, et le pilote anticipe.
- Il demande un **capteur de vent NMEA** (anémomètre/girouette). Le BoM de base décrit dans
  `fenix-liens-et-notes-2026-09-08.md` n'en prévoit pas : **c'est une dépendance matérielle nouvelle**.
- Ce n'est **pas** un réglage « prêt à l'emploi » : la table `Cn` et `kAir` doivent être
  identifiés pour chaque bateau (voir § 4).

## 4. Réserves et points à valider

1. **Table `Cn` générique.** Le commentaire de l'auteur dit : *« not identified coefficients for a
   specific vessel »*. **CONFIRMÉ.** La force réelle sur un bateau donné n'est donc pas modélisée.
   L'ajustement repose sur le ratio (0,5–2,0) et l'évaluateur.
2. **Bogue très probable : le plafond de `Cwind` est à l'envers** (`Autopilot.cpp`, ligne 1775).
   Le code fait `setWindFFratio(constrain(result.Cwind, 0.8f, -0.8f) * ratio)`. Le minimum (0,8) est
   **plus grand** que le maximum (−0,8). Avec la définition standard d'Arduino
   `constrain(x,a,b) = (x<a ? a : (x>b ? b : x))`, le résultat est :
   - `Cwind` < 0,8 → **0,8** (le ratio baisse de 20 %) ;
   - `Cwind` ≥ 0,8 → **−0,8**, donc un ratio négatif, aussitôt ramené à son plancher **0,5** par `setWindFFratio`.

   Or `Cwind` vaut 0,8 ou plus dès que l'intégrale n'est pas négative. Conséquence probable : après quelques
   estimations, le ratio s'effondre vers 0,5 et **ne peut plus remonter**. Le plafond voulu était vraisemblablement
   du genre `constrain(Cwind, 0.8f, 1.2f)` (valeurs exactes **inconnues**). **À VALIDER** : lecture de code,
   non compilé. À signaler à l'auteur (`spascual90`) après test.
3. **Commentaires et code en désaccord** (`WindFeedforward`) : la doc de `update()` parle de `dt`
   en secondes et d'une constante `_TIME_S`, alors que le code compte en millisecondes (`_MS`).
   L'horloge `previousMillis` est `static` : partagée entre toutes les instances. Sans effet tant
   qu'il n'y a qu'une instance. **À VALIDER**.
4. **Conditions d'activation.** Je n'ai pas vérifié si `_windMode` vaut AWA/TWA en mode AUTO au cap
   compas. Si non, le feedforward ne servirait qu'en modes vent. **À VALIDER**.
5. **Mode TWA.** Le code donne au calcul le vent **vrai** (vitesse) combiné à un angle relatif au cap,
   alors que la formule est écrite pour le vent **apparent**. Approximation probable. **À VALIDER**.
6. **Entrées de l'évaluateur mal nommées ou dupliquées** (`Autopilot.cpp`, lignes 1740-1748) :
   `unitWindFeedforward`, `appliedWindFeedforward` et `currentWindScale` reçoivent **la même valeur**
   (`getWindFeedForward()`). La régression de plausibilité ne mesure donc pas ce que son nom annonce.
   De plus `headingErrorDeg` reçoit le **cap** (`getHeadingTforControl`), pas une erreur de cap. Le critère de
   stabilité reste utilisable (cap qui varie peu), mais un passage du cap par 0°/360° peut le faire échouer
   à tort. **À VALIDER.**
7. **Cadence.** L'évaluateur abandonne si deux échantillons sont espacés de plus d'1 s. Il est appelé dans la
   boucle longue : si celle-ci dépasse 1 s, il ne dépasserait jamais la qualification. Période de la boucle
   longue **non vérifiée**. **À VALIDER.**
8. **Beaucoup de seuils codés en dur** (10 s, 7 s, 80 %, 0,5°…) sans justification dans le code.
   Ce sont des choix de l'auteur, non validés pour d'autres bateaux.
9. **Aucun essai réel connu.** Rien dans le commit n'indique de résultat en mer.

## 5. Contexte

Ce commit s'ajoute à une série du dépôt (`56e5304`, 2026-07-05 : modèle de référence de Fossen,
feedforward, observateur de vagues ; `305c193`, 2026-07-16 : RefNomoto, Wave, FF). Le firmware actuel est donc
plus avancé que le PID de base décrit dans les notes du 2026-09-08. Le commit touche aussi :
la saturation de l'actionneur, la calibration IMU, `IF_NMEA.cpp`, `Fenix_config.h`, et ajoute
`libraries_ext/FrequencyTimer.*`.

### Le Handbook officiel ne couvre pas cette fonction

**Vérifié par lecture partielle le 2026-10-26** (clone superficiel de
https://github.com/spascual90/Fenix-User-Handbook.git, dernier commit `6bbc52a`, 2025-12-28).
Lecture des passages contenant « wind », « feedforward » ou « FF » dans les 5 fichiers concernés ;
les fichiers n'ont pas été lus en entier.

- Aucun fichier ne décrit le feedforward vent. `introduction/overview.md` mentionne seulement le mode vent
  (tenir un angle de vent).
- `using-fenix-tiller-pilot/untitled.md` classe « Windvane and calculations » sous *« not available in V2.x »*,
  alors que le dépôt du code a des modes AWA/TWD depuis 2026-02-23.
- Le `untitled.md` de la racine (non listé dans `SUMMARY.md`) donne la section « Wind » comme « TBD ».
- Deux autres fichiers ne contiennent que « Windows » (faux positifs).

Conclusion : pour ce firmware, le code fait foi et le Handbook est en retard. Le dépôt du Handbook est enregistré
sous le **n° 208** (il recoupe le GitBook, sources n° 2, 9, 10 et 11).

## 6. Pour aller plus loin (non fait)

- Décider si le projet veut un capteur de vent (décision de Mathieu, pas une exigence acceptée).
