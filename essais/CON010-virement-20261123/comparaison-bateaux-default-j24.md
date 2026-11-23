# Comparaison des profils SailSim `default` et `j24` (2026-11-23)

Source : `configs/yachts/default.toml` et `configs/yachts/j24.toml`, SailSim `herostrat/sailsim` @ `ef1e293`
(lus avec `tomllib`, valeurs recopiées telles quelles). Le profil J/24 dit être estimé (Clarke 1983 + règles ITTC,
LOA 7,32 m, LWL 6,1 m, BWL 2,72 m, T 1,22 m). `default` n'indique aucune source ni dimension.
Conventions : x vers l'avant depuis l'origine du bateau (CO) ; unités SI.

## Paramètres qui comptent pour la tenue de cap et le virement

| Paramètre | `default` | `j24` | Rapport j24/default | Ce que ça règle |
|---|---|---|---|---|
| `mass` (kg) | 4000 | 1406 | 0,35 | déplacement |
| `Iz` (kg·m²) | 25 000 | 3270 | 0,13 | inertie en lacet |
| `N_rdot` (masse ajoutée en lacet) | −15 000 | −327 | 0,02 | inertie apparente en lacet |
| `Nr` (amortissement linéaire du lacet) | −20 000 | −8035 | 0,40 | freine la rotation |
| `Nrr` (amortissement quadratique du lacet) | −50 000 | −43 761 | 0,88 | freine la rotation rapide |
| `Yv` / `Nv` | −2000 / −500 | −3005 / −737 | 1,5 | résistance latérale |
| `Xu` / `Xuu` (traînée de coque) | −100 / −50 | −76,6 / −42,7 | 0,8 | perte de vitesse |
| `sail_area` (m²) | 50 | 32 | 0,64 | puissance |
| `sail_ce_x` (m) | −0,20 | −0,15 | | centre de voilure |
| `keel_x` (m) | 0,15 | 0,10 | | centre de dérive |
| Lead = `keel_x − sail_ce_x` (m) | 0,35 | 0,25 (4,1 % de LWL) | | équilibre voile/coque |
| `rudder_area` (m²) | 0,25 | **0,10** | 0,40 | efficacité du safran |
| `rudder_x` (m) | −4,5 | −2,9 | 0,64 | bras de levier du safran |
| Aire × bras (m³) | 1,13 | **0,29** | 0,26 | couple de barre disponible |
| Safran / voilure | 0,50 % | 0,31 % | | autorité de barre |
| `rudder_max` (rad) | 0,52 (29,8°) | 0,52 (29,8°) | 1 | butée |
| `keel_area` (m²) | 1,5 | 0,5 | 0,33 | |
| `GM_T` (m) | 1,2 | 0,8 | | stabilité à la gîte |

Table complète (45 paramètres) : rejouer
`.venv\Scripts\python.exe -c "import tomllib; print(tomllib.load(open('configs/yachts/j24.toml','rb')))"`.

## Comportement mesuré sur le banc (SIMULÉ, une exécution par cas)

| | `default` | `j24` |
|---|---|---|
| Vent de près, 8 m/s de vent vrai | tient le près, mais **mou** : barre moyenne +2,6° vers le vent ; le pilote interne se stabilise 8° sous la consigne | **ne tient pas le près** : lofe jusqu'à environ 341° puis recule, quels que soient le cap (270–325°) et le pilote |
| Vitesse au près | 10–12 nd (irréaliste pour 4 t) | 5–8 nd |
| Contre-barre −15° tenue | (non essayé) | à 7,8 nd : équilibré environ 4 s puis **abat** ; à 4,9 nd : lofe quand même → instable |
| Virement complet | **oui** : témoin Nomoto en 45 s ; séquence de Mathieu (essai 4b) en 65 s | **jamais** (l'approche échoue déjà) |

## Lecture (HYPOTHÈSES, non isolées)

- J/24 : **peu d'autorité de barre** (couple de barre 4 fois plus faible pour 0,64 fois la voilure) et **très peu
  d'inertie en lacet** (`N_rdot` 46 fois plus faible). Le bateau part vite et le safran le rattrape mal, d'où l'instabilité.
  Le safran de 0,10 m² paraît petit pour un J/24 (non vérifié sur une fiche du bateau réel). Agrandi à 0,2 ou 0,3 m²,
  rien ne change (essais `j24_safran_*`), ce qui pointe aussi vers le pilote (plafond de l'intégrale du Nomoto).
- `default` : l'inverse : **forte inertie et fort amortissement en lacet**, d'où une rotation lente (virement de 45 s)
  mais stable.
