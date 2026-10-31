#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banc de comparaison COMMUN Fenix / pypilot (supplément du plan de tests, § 10).

Ce que ce script ajoute aux deux scripts existants (qui ne sont pas modifiés) :
  - un seul bateau, un seul vérin (vitesse max V), une seule limite de barre L,
    les mêmes conditions initiales et les mêmes perturbations pour tous ;
  - des perturbations : vent (P1), houle (P2), changement de vitesse du bateau (P3),
    combinaison (P4) ;
  - les cinq indicateurs demandés : temps d'établissement (±0,5°), dépassement
    maximal (°), erreur RMS, nombre d'activations du vérin, énergie (estimation) ;
    plus le temps de marche (cycle de service 20 %) et les saturations ;
  - un modèle du vérin de Fenix plus fidèle : seuils d'arrêt / redémarrage, deux
    niveaux de vitesse, rampes, attente de 1,8 s entre inversions (port de
    ActuatorManager::controlActuator, lecture du code, jamais exécuté sur Arduino).

DÉPEND de fenix_pid_sim.py et pypilot_sim.py : les placer dans le MÊME dossier.

HYPOTHÈSES (aucune n'est mesurée ; toutes à remplacer, voir plan de tests M2, M3, M7, M8) :
  - Bateau Nomoto T = 2,26 s, K = 0,19 (bateau de 12 m, valeurs par défaut de Fenix).
  - Vérin : V_MAX = 7,4 °/s à pleine vitesse, vitesse proportionnelle au PWM, pas de
    PWM minimal de démarrage (PWM_MIN_MOVE = 0).
  - Fenix : controlActuator appelé à ACT_HZ (10 ou 100 Hz, À VÉRIFIER dans le firmware :
    cela fixe la durée des rampes de ±5 par appel). Seuil d'arrêt 0,3° et de redémarrage
    1,2° (rudDamping = 5 de HC_INSTPARAM, converti par _ratio = course de barre /
    course du potentiomètre, supposé 700/1023) ; variante 0,6° / 2,4° (valeur 10 de
    DEFAULT_ERROR_FEEDBACK). Le vrai rapport dépend de l'étalonnage du potentiomètre.
  - Fenix connaît exactement la vitesse relative f du bateau.
  - Houle : lacet direct de 1,2° à 6 s, 0,8° à 9 s, 0,5° à 4 s (phases aléatoires par graine).
  - Vent : décalage de barre équivalent (« helm ») en échelon puis rampe.
  - Courant du vérin : 1 A (à vide) à 10 A (pleine charge) d'après la fiche, supposé
    proportionnel au rapport PWM ; énergie = ordre de grandeur, pas une mesure.
  - Bruit capteur : cap 0,2°, gyroscope 0,1 °/s.
  - Piste A (vitesse proportionnelle, Fenix) : paramètres de ma main (plancher PWM 60,
    saturation à 6° d'écart), non validés.

Usage :  python3 comparaison_pilotes.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fenix_pid_sim as fx          # noqa: E402
import pypilot_sim as pp            # noqa: E402

DT = 0.05
T0, K0 = 2.26, 0.19
V_MAX = 7.4          # °/s de barre à pleine vitesse (calcul du montage, rapport § 10.3)
L_DEF = 20.0         # limite de barre commune (°)
ACT_HZ = 10.0        # fréquence supposée d'appel de controlActuator
STOP_DEF = 0.3       # seuil d'arrêt (°) : rudDamping = 5 dans HC_INSTPARAM -> toRudder(5) ~ 3 dixièmes
PWM_MIN_MOVE = 0.0   # PWM minimal de démarrage (inconnu : M3)
SEEDS = (1, 2, 3, 4, 5)
VOLT = 12.0
I_LOW, I_HIGH = 1.0, 10.0


def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


# ---------------------------------------------------------------- perturbations
def make_disturbances(profile, n, seed, wave_scale=1.0):
    """Retourne (d, f, wave_psi, wave_r) : décalage de barre équivalent (°), vitesse
    relative du bateau, lacet de houle (°) et sa vitesse (°/s)."""
    t = np.arange(n) * DT
    d, f = np.zeros(n), np.ones(n)
    wpsi, wr = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(1000 + seed)
    if profile in ("P1", "P4"):                          # vent
        w = np.zeros(n)
        w[t >= 100] = 2.0
        ramp = (t >= 250) & (t < 330)
        w[ramp] = 2.0 - 3.0 * (t[ramp] - 250) / 80.0
        w[(t >= 330) & (t < 450)] = -1.0
        d += w
    if profile in ("P2", "P4"):                          # houle
        for amp, per in ((1.2, 6.0), (0.8, 9.0), (0.5, 4.0)):
            ph = rng.uniform(0, 2 * np.pi)
            om = 2 * np.pi / per
            wpsi += wave_scale * amp * np.sin(om * t + ph)
            wr += wave_scale * amp * om * np.cos(om * t + ph)
    if profile == "P3":                                  # P3 seul : barre de compensation constante
        d[t >= 100] += 2.0
    if profile in ("P3", "P4"):                          # vitesse du bateau
        down = (t >= 200) & (t < 260)
        f[down] = 1.0 - 0.5 * (t[down] - 200) / 60.0
        f[(t >= 260) & (t < 400)] = 0.5
        up = (t >= 400) & (t < 460)
        f[up] = 0.5 + 0.5 * (t[up] - 400) / 60.0
    return d, f, wpsi, wr


# ---------------------------------------------------------------- vérin de Fenix
class FenixActuator:
    """Port simplifié de ActuatorManager::controlActuator (lecture du code).

    Décisions évaluées à chaque pas de 50 ms ; les rampes (±5 PWM par appel) sont
    ramenées au temps continu avec ACT_HZ appels par seconde. Le test de blocage,
    les fins de course et le courant ne sont pas modélisés."""

    def __init__(self, mode="coded", hz=ACT_HZ, stop=STOP_DEF, slow=3.0, V=V_MAX,
                 L=L_DEF, floor=60.0, sat=6.0):
        self.mode, self.hz, self.stop, self.slow = mode, hz, stop, slow
        self.restart = 4 * stop
        self.V, self.L, self.floor, self.sat = V, L, floor, sat
        self.pwm, self.dir, self.last_dir = 0.0, 1, 1
        self.estados, self.timer, self.t_timer, self.double = 0, 0, 0.0, False

    def step(self, e, t, dt, delta):
        desired = 1 if e >= 0 else -1
        if self.pwm == 0 and self.timer == 0:           # horloge de la protection
            self.timer, self.t_timer = 1, t
        if self.timer == 1 and t - self.t_timer >= 1.8:
            self.timer = 2
        if abs(e) <= self.stop:                         # 3. bande d'arrêt
            self.pwm = 0.0
            return self._move(delta, dt)
        if self.pwm == 0 and self.restart > abs(e):     # ne pas redémarrer
            return self._move(delta, dt)
        speed_cmd = None
        if desired != self.last_dir or self.estados != 0:   # 4. changement de sens
            speed_cmd = 0.0
            if self.estados == 0:
                if not self.double:
                    self.double = True                  # première lecture : on garde l'état
                    return self._move(delta, dt)
                self.double = False
                self.estados = 1
            elif self.estados == 1:
                if self.pwm == 0:
                    self.estados = 2
            elif self.estados == 2:
                if self.timer == 2:
                    self.estados, self.timer = 0, 0
        if self.estados == 0:                           # 5. choix de la vitesse
            if self.mode == "coded":
                speed_cmd = 255.0 if abs(e) > self.slow else 255.0 / 3
            else:                                       # piste A : proportionnelle
                speed_cmd = min(255.0, max(self.floor, 255.0 * abs(e) / self.sat))
        if self.last_dir != desired and self.estados == 0:
            self.dir = desired
            self.last_dir = desired
        ds = speed_cmd - self.pwm                       # 6. rampes
        if abs(ds) < 5:
            ds = 0.0
        step = 5.0 * self.hz * dt
        new = self.pwm + (step if ds > 0 else -step if ds < 0 else 0.0)
        if (ds > 0 and new > speed_cmd) or (ds < 0 and new < speed_cmd):
            new = speed_cmd
        if new < 5:
            new = 0.0
        self.pwm = min(new, 255.0)
        return self._move(delta, dt)

    def _move(self, delta, dt):
        v = 0.0
        if self.pwm > PWM_MIN_MOVE:
            v = self.dir * self.V * self.pwm / 255.0
        nd = delta + v * dt
        if abs(nd) > self.L:                            # fin de course commune
            nd = self.L * sign(nd)
            self.pwm, v = 0.0, 0.0
        return nd, v


# ---------------------------------------------------------------- simulation commune
def run(algo, profile, seed, psi0=0.0, t_end=600.0, L=L_DEF, V=V_MAX, sub=4,
        noise=1.0, f_const=1.0, wave_scale=1.0):
    """algo : dict(kind='fenix'|'pyp', ...)."""
    n = int(t_end / DT)
    rng = np.random.default_rng(seed)
    nh = 0.2 * noise * rng.standard_normal(n)
    nr = 0.1 * noise * rng.standard_normal(n)
    d, f, wpsi, wr = make_disturbances(profile, n, seed, wave_scale)
    f = f * f_const
    psi, r, delta = psi0, 0.0, 0.0
    t_a, e_a, del_a, v_a, tgt_clip = (np.zeros(n) for _ in range(5))
    kind = algo["kind"]
    if kind == "fenix":
        pid = fx.FenixPID(sched=algo.get("sched", "fenix"))
        pid.start(-psi0)
        target = 0.0
        act = None if algo.get("act") == "ideal" else FenixActuator(
            algo.get("act", "coded"), algo.get("hz", ACT_HZ), stop=algo.get("stop", STOP_DEF), V=V, L=L)
    else:
        sv = pp.Servo(algo.get("servo", "real"), algo.get("period", 0.4),
                      algo.get("smin", 1.0), algo.get("smax", 1.0))
        heading_lp, hr_lp, hrr_lp, prev_r = psi0, 0.0, 0.0, 0.0
    for i in range(n):
        t = i * DT
        psi_true, r_true = psi + wpsi[i], r + wr[i]
        mh, mr = psi_true + nh[i], r_true + nr[i]
        v = 0.0
        if kind == "fenix":
            if i % 2 == 0:                               # PID à 10 Hz
                rudder_error = int(round((target - delta) * 10.0))
                u = pid.compute(-mh, rudder_error, f[i])
                raw = u / 10.0
                target = float(np.clip(raw, -L, L))
                tgt_clip[i] = 1.0 if abs(raw) > L else 0.0
            elif i > 0:
                tgt_clip[i] = tgt_clip[i - 1]
            e = target - delta
            if act is None:                              # vérin idéal (validation)
                step = float(np.clip(e, -V * DT, V * DT))
                delta = float(np.clip(delta + step, -L, L))
                v = step / DT
            else:
                delta, v = act.step(e, t, DT, delta)
            phys = delta
        else:
            hrr_raw = (mr - prev_r) / DT
            prev_r = mr
            heading_lp = .2 * mh + .8 * heading_lp
            hr_lp = .2 * mr + .8 * hr_lp
            hrr_lp = .1 * hrr_raw + .9 * hrr_lp
            err = min(max(heading_lp - 0.0, -30.0), 30.0)
            pr = np.sqrt(abs(err)) * (-1 if err < 0 else 1)
            cmd = .003 * err + .09 * hr_lp + .075 * hrr_lp + .005 * pr
            speed = sv.command(cmd, t, DT)
            nd = delta + V * speed * DT
            if abs(nd) > L:
                nd = L * sign(nd)
                speed = 0.0
            v = (nd - delta) / DT if speed != 0 else 0.0
            delta = nd
            phys = -delta                                # convention pypilot : signe inversé
        T, K = T0 / f[i], K0 * f[i]
        h = DT / sub
        for _ in range(sub):
            r += (-r + K * (phys + d[i])) / T * h
            psi += r * h
        t_a[i], e_a[i], del_a[i], v_a[i] = t, psi + wpsi[i], delta, v
    return dict(t=t_a, e=e_a, delta=del_a, v=v_a, clip=tgt_clip, L=L, V=V)


# ---------------------------------------------------------------- indicateurs
def indicators(res, e0=0.0, tol=0.5, win=(60.0, None)):
    t, e, delta, v = res["t"], res["e"], res["delta"], res["v"]
    L, V = res["L"], res["V"]
    dur = t[-1] + DT
    out_idx = np.where(np.abs(e) > tol)[0]
    settle = 0.0 if len(out_idx) == 0 else t[out_idx[-1]]
    if len(out_idx) and out_idx[-1] >= len(t) - 2:
        settle = float("inf")
    s = 1 if e0 > 0 else -1
    over = float(max(0.0, (-s * e).max())) if e0 else float("nan")
    w = t >= win[0] if win[1] is None else (t >= win[0]) & (t < win[1])
    rms = float(np.sqrt(np.mean(e[w] ** 2)))
    emax = float(np.abs(e[w]).max())
    moving = np.abs(v) > 1e-9
    starts = int(np.sum(moving[1:] & ~moving[:-1]) + (1 if moving[0] else 0))
    duty = float(np.mean(moving))
    eq = float(np.mean(np.abs(v)) / V)
    travel = float(np.sum(np.abs(np.diff(delta))) / dur * 60.0)
    sat = float(np.mean((np.abs(delta) >= L - 0.05)) * 100.0)
    return dict(settle=settle, over=over, rms=rms, emax=emax, starts_min=starts / dur * 60.0,
                duty=duty * 100.0, travel=travel, sat=sat, tclip=float(np.mean(res["clip"]) * 100.0),
                wh_lo=VOLT * I_LOW * eq, wh_hi=VOLT * I_HIGH * eq)


ALGOS = {
    "Fenix codé (10 Hz)":      dict(kind="fenix", act="coded", hz=10.0),
    "Fenix codé (100 Hz)":     dict(kind="fenix", act="coded", hz=100.0),
    "Fenix codé 100Hz arrêt0,6": dict(kind="fenix", act="coded", hz=100.0, stop=0.6),
    "Fenix piste A (100 Hz)":  dict(kind="fenix", act="A", hz=100.0),
    "pypilot défaut":          dict(kind="pyp", servo="real", period=0.4, smin=1.0),
    "pypilot réglé 0,1 s/30%": dict(kind="pyp", servo="real", period=0.1, smin=0.3),
    "pypilot servo idéal*":    dict(kind="pyp", servo="ideal"),
}


def avg(list_of_dicts):
    keys = list_of_dicts[0].keys()
    out = {}
    for k in keys:
        vals = np.array([d[k] for d in list_of_dicts], dtype=float)
        if np.all(np.isnan(vals)):
            out[k] = float("nan")
        else:
            out[k] = float("inf") if np.any(np.isinf(vals)) else float(np.nanmean(vals))
    return out


def fmt_s(x):
    return ">600" if x == float("inf") else f"{x:.0f}"


# ---------------------------------------------------------------- validation
def validation():
    print("=== V0 : validation du banc commun contre les deux scripts d'origine ===")
    print("(bruit et houle coupés, mêmes réglages, écart maximal de cap entre ancien et nouveau code)")
    # pypilot : mêmes paramètres que pypilot_sim.simulate (V = 7, course 45°)
    for mode in ("ideal", "real"):
        pp.RUDDER_RANGE = 45.0
        t0, psi0_, de0, sp0 = pp.simulate(f=1.0, V=7.0, servo=mode, psi0=5.0, noise_h=0.0,
                                          noise_r=0.0, t_end=300, FF=0.0)
        res = run(dict(kind="pyp", servo=mode), "P0", 1, psi0=5.0, t_end=300, L=45.0, V=7.0,
                  noise=0.0)
        dmax = float(np.max(np.abs(res["e"] - psi0_)))
        print(f"  pypilot {mode:<5} : écart max de cap = {dmax:.2e} °")
    # Fenix : vérin idéal comme dans fenix_pid_sim.simulate(stop_band=0, rate=7)
    t1, p1, d1, _ = fx.simulate(1.0, sched="fenix", psi0=5.0, noise=0.0, stop_band=0.0,
                                rate=7.0, t_end=300)
    res = run(dict(kind="fenix", act="ideal"), "P0", 1, psi0=5.0, t_end=300, L=35.0, V=7.0,
              sub=1, noise=0.0)
    print(f"  Fenix  idéal  : écart max de cap = {float(np.max(np.abs(res['e'] - p1))):.2e} °")
    print("  (un écart de l'ordre de 1e-9 à 1e-6 signifie : même logique de commande)")


# ---------------------------------------------------------------- scénarios
def scenario(profile, psi0, t_end, win, title, tol=0.5):
    print(f"\n=== {title} ===")
    hdr = (f"{'algorithme':<27}| {'établ.±0,5°':>11} {'dépass.°':>8} {'RMS°':>5} {'max|e|°':>7} | "
           f"{'activ./min':>10} {'marche%':>7} {'barre°/min':>10} | {'Wh/h bas–haut':>13} | {'sat.%':>5} {'cible écr.%':>11}")
    print(hdr)
    rows = {}
    for name, algo in ALGOS.items():
        ind = avg([indicators(run(algo, profile, s, psi0=psi0, t_end=t_end), e0=psi0, tol=tol, win=win)
                   for s in SEEDS])
        rows[name] = ind
        st = fmt_s(ind["settle"]) if profile == "P0" else "—"
        ov = f"{ind['over']:.2f}" if profile == "P0" else "—"
        print(f"{name:<27}| {st:>11} {ov:>8} {ind['rms']:5.2f} {ind['emax']:7.2f} | "
              f"{ind['starts_min']:10.1f} {ind['duty']:7.1f} {ind['travel']:10.1f} | "
              f"{ind['wh_lo']:5.2f}–{ind['wh_hi']:5.2f} | {ind['sat']:5.1f} {ind['tclip']:11.1f}")
    return rows


def main():
    validation()
    print("\nMoyenne sur 5 graines (même bruit et mêmes perturbations pour tous les algorithmes).")
    print("* servo idéal : référence théorique, pas un vérin réel ; ses « activations » ne sont pas comparables.")
    print("Wh/h : 12 V × (1 A à 10 A) × rapport PWM moyen — ordre de grandeur, électronique de commande exclue.")
    all_rows = {}
    all_rows["P0"] = scenario("P0", 5.0, 600.0, (400.0, None),
                              "E0 : écart initial de 5°, sans perturbation (RMS sur t > 400 s)")
    titles = {"P1": "P1 : variation de vent (échelon +2° à 100 s, rampe vers −1°, retour à 0)",
              "P2": "P2 : houle (lacet direct ±2,5° environ, périodes 4 à 9 s)",
              "P3": "P3 : changement de vitesse du bateau (f : 1,0 → 0,5 → 1,0), avec barre de compensation de 2° dès 100 s",
              "P4": "P4 : combinaison P1 + P2 + P3"}
    for p in ("P1", "P2", "P3", "P4"):
        all_rows[p] = scenario(p, 0.0, 600.0, (60.0, None), titles[p] + " (RMS sur t > 60 s)")
    print("\nLecture : aucun classement n'est tiré ici. Les compromis précision / usure / énergie")
    print("se jugent avec des seuils que Mathieu doit fixer (plan de tests § 10.6).")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        names = ["Fenix codé (100 Hz)", "Fenix piste A (100 Hz)", "pypilot défaut", "pypilot réglé 0,1 s/30%"]
        fig, ax = plt.subplots(2, 2, figsize=(13, 8))
        for nm in names:
            r0 = run(ALGOS[nm], "P0", 1, psi0=5.0, t_end=300)
            ax[0, 0].plot(r0["t"], r0["e"], label=nm)
            r4 = run(ALGOS[nm], "P4", 1, psi0=0.0, t_end=600)
            ax[0, 1].plot(r4["t"], r4["e"], label=nm, lw=.8)
            ax[1, 0].plot(r4["t"], r4["delta"], label=nm, lw=.8)
        ax[0, 0].set_title("E0 : écart initial de 5° (cap)")
        ax[0, 1].set_title("P4 : vent + houle + changement de vitesse (cap)")
        ax[1, 0].set_title("P4 : angle de barre")
        for a in ax.ravel()[:3]:
            a.set_xlabel("temps (s)"); a.grid(alpha=.3); a.legend(fontsize=7)
        ax[0, 0].set_ylabel("cap (°)"); ax[0, 1].set_ylabel("cap (°)"); ax[1, 0].set_ylabel("barre (°)")
        x = np.arange(len(names))
        ax[1, 1].bar(x - 0.2, [all_rows["P4"][n]["starts_min"] for n in names], 0.4, label="activations/min")
        ax2 = ax[1, 1].twinx()
        ax2.bar(x + 0.2, [all_rows["P4"][n]["duty"] for n in names], 0.4, color="C1", label="temps de marche %")
        ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels([n.replace(" (100 Hz)", " 100Hz") for n in names],
                                                         rotation=15, fontsize=7)
        ax[1, 1].set_title("P4 : sollicitation du vérin"); ax[1, 1].set_ylabel("activations / min")
        ax2.set_ylabel("temps de marche (%)")
        fig.tight_layout()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparaison_pilotes.png")
        fig.savefig(out, dpi=130)
        print("\nFigure :", out)
    except Exception as e:
        print("\n(pas de figure :", e, ")")


if __name__ == "__main__":
    main()
