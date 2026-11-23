# Essais SailSim du 2026-11-23 : virement en séquence (SIMULÉ)

Suite de `../CON010-20261122/`. Banc Q1 v5 sous Docker (conteneur `pp`, pypilot `fdff88f`, couche servo,
`servo.speed.min` = 30, voiles réglées par `auto_sail_trim`), sauf mention « pilote interne » (Nomoto de SailSim,
sans Docker). **Une exécution par cas. Rien de tout ceci n'est mesuré sur le Capri 22.**

## Constats sur le banc (valables pour tous les essais de séquence)

1. **Le témoin Nomoto du 2026-11-22 a réussi son virement** (45 s), contrairement à ce qu'écrivait le README
   de la veille (correction ajoutée là-bas et dans CON-010). Rejoué : identique (`temoin_nomoto_rejoue.*`).
2. **`wind.direction` arrive bien dans pypilot** (`virement_v3_*_pypilot.csv`). Les fins d'étape « vent »
   ne se déclenchaient pas parce que les durées de garde-fou étaient plus courtes que la manœuvre.
3. **L'adaptateur pypilot de SailSim réimpose la consigne de cap du scénario à chaque pas**
   (`sailsim/autopilot/pypilot.py`, `_reassert_heading_command`). Toute consigne envoyée par un script
   (`ap.heading_command`) est écrasée en 0,1 s. Conséquence : l'étape « abattre » de `virement_v3` C
   (survirage de 10°) **n'a jamais été jouée** ; la reprise se fait sur la consigne du scénario.
4. **Le profil J/24 de SailSim ne tient aucun cap au vent** (310° à 270°) : il lofe à 341° en 3 s, barre en
   butée, et recule. Agrandir le safran (copies `j24_safran_*.toml`) ne change rien. Profil écarté.
5. **Le bateau `default` n'est pas réaliste** : 10–12 nd au près dans 15,6 nd de vent, virement natif de 45 s.
   Au près (310°, 50° du vent vrai), son vent apparent est d'environ 31° ; +40° apparent = 73° du vent vrai.
6. **Modèle des voiles** : portance nulle sous 20° de vent apparent (`aerodynamics.py:101`). Tous les échecs
   finissent coincés à environ −19° de vent apparent.
7. Horloge du script ≈ 0,96 × temps SailSim : les mesures sont recalées sur le cap (`analyse_spec.py`).

## Séries

| Fichiers | Ce qui est essayé | Résultat |
|---|---|---|
| `virement_v2.py` A, B | barre 27° jusqu'au vent qui porte, puis pilote (B : ramener avant) | échec, +18° (barre réelle 26°) |
| `virement_v3.py` A29, C, D30 | 29° ; C = survirage (non joué, constat 3) ; D30 = séquence ≤ 30 s | échec, +18° |
| `virement_spec.py` (spécification de Mathieu) | phases angle / vitesse °/s / maintien, Hfinal = H0 + 100° | voir ci-dessous |

### Essai à phases (spécification de Mathieu)

Réglages : vent vrai 000°, 8 m/s ; approche au près à 310° (≈ 50° du vent vrai, au lieu de +40° apparent,
voir constat 5) ; angle de virement 100° ; approche stabilisée = 10 s avec cap à ±4° de la moyenne
(±3° rejeté par le cycle limite de pypilot, essai 1) et vitesse à ±5 % ; angle atteint à ±1° ; séquence ≤ 30 s.
Phases d'exemple : 20° à 10 °/s, maintien 3 s · 25° à 5 °/s, 4 s · 10° à 5 °/s, 2 s · 0° à 5 °/s, 0 s.

- `essai1_*` : « approche non stabilisée » (cap 307–313°).
- `essai2_*` : séquence valide, reprise faussée par le constat 3 (pilote ramené vers 310°).
- `essai3_*` : ordre TACK = étape du scénario à 30 s (consigne 050°). Lit du vent à 13,3 s, fin de séquence
  à 16,5 s avec 55 % du virement fait ; la barre est relâchée trop tôt, le bateau s'arrête à −19° de vent
  apparent et recule. **Échec.**
- `essai4a_*` : phases de l'essai 4, refusé en approche (cap 300–314°).
- `spec_phases.*` (essai 4b) : contre-barre de 15° ajoutée en phase 0 (demande de Mathieu), phase 2 tenue 8 s.
  Le bateau abat de 45° et prend de l'erre (11,2 nd), passe le vent à 20,4 s à 4,9 nd, aligné sur Hfinal à
  64,7 s. **Réussi, mais non probant** : `default` est mou (barre moyenne +2,6° vers le vent en approche), à
  l'inverse d'un vrai voilier qui lofe en accélérant (remarque de Mathieu). Mesures : `spec_phases_mesures.json`,
  graphique `spec_phases.svg`.

### J/24 avec contre-barre (pilote interne)

`j24_contrebarre.py` (CSV `j24_contre15_*`) : −15° posés dès le premier pas, avant le lof. À 4,9 nd, il lofe
quand même ; à 7,8 nd, équilibré environ 4 s, puis il abat jusqu'à empanner : **instable**. Avec le pilote, la
contre-barre est relâchée et il lofe : l'intégrale du Nomoto est plafonnée (`nomoto.py:237`), précharge sans effet.
Comparaison des profils : `comparaison-bateaux-default-j24.md`.

### Issues publiées chez SailSim (2026-11-23)

[#1](https://github.com/herostrat/sailsim/issues/1) plafond de l'intégrale du Nomoto ·
[#2](https://github.com/herostrat/sailsim/issues/2) virement irréaliste avec les bateaux fournis.
Textes d'origine : `issues-sailsim-brouillon.md`.

## Conclusion

Le banc valide la **mécanique** de la séquence (déclenchement, phases, veille de pypilot, sécurités, mesures),
pas ses **valeurs** : aucun bateau SailSim n'est assez réaliste. Angles et durées se règlent sur le Capri 22.
À vérifier dans pypilot (HYPOTHÈSE) : la reprise du pilote part-elle de la barre réelle, sans à-coup ?

## Plan alternatif gardé en note (non exécuté)

Proposé par Claude avant la spécification de Mathieu : scénario sans changement de consigne, déclenchement par le
script, séquence Lancer 20° (vent au nez ou 8 s) → Tenir 20° (cap tourné de 70° ou 8 s) → Ramener 0° à 60 %
(cap tourné de 90° ou 6 s) → pilote sur le cap final ; comparaison au témoin Nomoto sur le même bateau.

## Rejouer

```powershell
python virement_spec.py          # essai à phases (≈ 2 min 30, conteneur pp requis)
python analyse_spec.py spec_phases
python analyse.py temoin_nomoto_rejoue.csv
<clone sailsim-test>\.venv\Scripts\python.exe j24_contrebarre.py            # J/24, sans Docker
<clone sailsim-test>\.venv\Scripts\python.exe j24_contrebarre.py precharge
```
Lancer avec `python` (pas `python -I`).
