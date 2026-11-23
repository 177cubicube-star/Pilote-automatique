# Issues pour `herostrat/sailsim`

> **Publiées le 2026-11-23 sur GO de Mathieu** : A = https://github.com/herostrat/sailsim/issues/1,
> B = https://github.com/herostrat/sailsim/issues/2. Les renvois « issue A / issue B » ci-dessous sont devenus
> `#1` / `#2` dans les textes publiés. Le texte ci-dessous est le brouillon d'origine.

Rédigés le 2026-11-23. Vérifié avant rédaction : le dépôt n'a aucune issue (ouverte ou fermée), les issues sont
activées, `master` = `ef1e293` (2026-03-04) = notre copie locale. Publication seulement sur GO de Mathieu.

---

## Issue A

**Title:** `NomotoAutopilot: integral clamp is in error units, so the steady-state rudder it can hold depends on Ki (≈1° on j24)`

**Body:**

In `src/sailsim/autopilot/nomoto.py` (lines 237–238 at `ef1e293`), the anti-windup clamps the integral of the
heading error, not the rudder it produces:

```python
integral_max = 1.0
self._integral = np.clip(self._integral, -integral_max, integral_max)
...
rudder = Kp * error + Ki * self._integral - Kd * sensors.yaw_rate
```

The largest steady rudder the integral term can hold is therefore `Ki × 1.0` rad, and `Ki` comes from the
speed-scheduled pole placement. For `j24` in `heading_hold` I get:

| Speed | Ki | Max steady rudder from the integral |
|---|---|---|
| 2.5 m/s | 0.022 | ≈ 1.3° |
| 4.0 m/s | 0.008 | ≈ 0.5° |

A boat that needs a few degrees of weather helm to hold a heading upwind can never be trimmed out: the
steady-state error has to supply the missing rudder through `Kp`. On `j24` it does not manage to, and the boat
luffs up until it stops.

**Observed (j24, 8 m/s true wind from 000°, target 310°, `heading_hold`):** the pilot starts at 0° rudder
(nothing integrated yet), the boat luffs at up to 8–10°/s, and the pilot only reaches full opposite rudder
(−29.8°) after the boat is head to wind and below about 3 kn. It ends at 341°, going backwards. Starting the pilot
from −15° rudder, or setting `_integral` so that `Ki × _integral = −15°` before the run, changes nothing, because
the clamp brings the integral back to ±1.0.

**Suggested fix:** clamp the rudder contribution instead of the raw integral, for example
`self._integral = np.clip(self._integral, -self.rudder_max / Ki, self.rudder_max / Ki)`. A conditional
integration scheme (stop integrating while the rudder is saturated) would also work.

**Not verified:** whether this alone makes `j24` hold close-hauled; see issue B for the other factors.

---

## Issue B

**Title:** `Tacking under rudder is unrealistic or impossible with the bundled yachts (default: 45–65 s; j24: cannot hold close-hauled)`

**Body:**

Context: we use SailSim with pypilot (servo layer, Docker) to test a tack sequence for a small keelboat
autopilot. A real 7–10 m keelboat tacks in roughly 5–10 s. In SailSim:

| Yacht | Result (8 m/s true wind, close-hauled approach about 50° TWA) |
|---|---|
| `default` | Tacks, but slowly: 45 s with the built-in Nomoto (`tack_port_to_starboard`); 65 s with a rudder sequence driven through pypilot. Speed falls from 9.7 kn to about 4 kn during the 13 s it takes to reach head to wind |
| `j24` | Never reaches a tack: it cannot hold close-hauled at any heading from 270° to 325° (luffs to about 341° and goes backwards). With −15° rudder held and no pilot, at 7.8 kn it balances for about 4 s and then bears away all the way around; at 4.9 kn it luffs anyway. Rudder area 0.2 or 0.3 m² (instead of 0.1) makes no difference |
| `swan45` | Reported by a separate test run (not reproduced here): it never crosses head to wind, with rudder held at 16°, 20° or 35°, or with rudder angle of attack controlled at 19.7° |

Model features that seem to combine here (we have **not** isolated which one dominates):

1. Sail lift is zero below 20° apparent wind angle (`physics/aerodynamics.py`, around line 101). The boat gets no
   drive at all across about 40° of the turn and has to carry its way through.
2. Rudder lift is capped at CL 0.6 beyond the stall angle (`physics/hydrodynamics.py`, lines 33 and 65–71).
   Above about 20° effective angle of attack, more helm adds no yaw moment, so 20° and 35° give identical results.
3. Yaw damping on `default` is very high (`Nr = −20000`, `Nrr = −50000`, `Iz = 25000`) compared with `j24`
   (`Nr = −8035`, `Iz = 3270`, `N_rdot = −327` vs −15000).
4. On `j24`: low rudder authority (rudder area × arm = 0.29 m³ vs 1.13 on `default`), plus the integral clamp in
   issue A.

**Questions:**
- Is a turn rate in the 5–10°/s range through a tack expected to be reachable with the bundled yachts?
- Would a gradual sail-lift decay near the luffing angle (instead of a hard zero at 20°) be acceptable?

Repro files (scenarios, scripts, CSV) can be shared if useful.

---

## Notes pour Mathieu (non publiées)

- Les deux textes sont factuels et citent le code de la version `ef1e293`. Les données du Swan 45 sont présentées
  comme « non reproduites ici ».
- L'issue B ne nomme ni le Capri 22 ni le projet : seulement « small keelboat autopilot ».
- Publication : `gh issue create -R herostrat/sailsim --title "…" --body-file …`, sous ton compte GitHub, publique.
