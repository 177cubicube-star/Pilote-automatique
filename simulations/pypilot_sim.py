#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation du pilote « basic » de pypilot (autopilot.py + pilots/basic.py +
servo.py::do_command) couplé au même bateau de Nomoto que la simulation de Fenix.

Ce que ce script est :
  - un port des parties de commande de pypilot 0.71 : calcul de l'erreur de cap
    (écrêtée à ±30°), filtres passe-bas de cap / vitesse de rotation /
    accélération de rotation, somme pondérée du pilote `basic`, anticipation (FF)
    sur la variation de consigne, et mécanisme « période / windup » du servo ;
  - un banc d'essai pour regarder la sensibilité à la vitesse du vérin, au
    mécanisme de période et à la vitesse du bateau.

Ce que ce script n'est PAS :
  - une validation en mer. Pas de vagues, pas de calibration de servo réelle,
    pas de limitation de pente (« slew ») dans le firmware Arduino du moteur.

Hypothèses (à contester si besoin) :
  - Bateau 12 m identique à la simulation de Fenix : T = 2,26 s, K = 0,19 1/s,
    avec K*f et T/f à la vitesse relative f (aucun gain n'est adapté à f dans
    pypilot).
  - La commande du pilote `basic` est une VITESSE normalisée du servo (±1). On
    suppose le servo bien calibré : vitesse de barre = vitesse_normalisée * V,
    avec V = 7 deg/s par défaut (même vérin que la simulation de Fenix). V est
    balayé car les gains de pypilot n'y sont pas normalisés.
  - Boucle à 20 Hz (rate = 20 par défaut), course de barre ±45° (rudder.range).
  - Bruit : cap 0,2° et gyroscope 0,1 deg/s (hypothèses).
  - Réglages du servo par défaut : speed.min = speed.max = 100 %, period = 0,4 s.

Usage :  python3 -I pypilot_sim.py
"""
import os

import numpy as np

T0, K0 = 2.26, 0.19
DT = 0.05                      # 20 Hz
SUB = 4                        # sous-pas d'intégration du bateau
RUDDER_RANGE = 45.0


def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


class Servo:
    """Port de Servo.do_command (branche « période »), sans protections moteur."""

    def __init__(self, mode="real", period=0.4, smin=1.0, smax=1.0):
        self.mode, self.period, self.smin, self.smax = mode, period, smin, smax
        self.windup = 0.0
        self.windup_change = 0.0
        self.speed = 0.0

    def command(self, cmd, t, dt):
        if self.mode == "ideal":                # pas de mécanisme de période
            self.speed = min(max(cmd, -self.smax), self.smax)
            return self.speed
        speed = cmd
        if not speed:
            self.speed = 0.0
            return 0.0
        max_speed = self.smax
        min_speed = min(self.smin, max_speed)   # speed_gain = 0 par défaut
        period = max(self.period, 2 * dt)
        self.windup += (speed - self.speed) * dt
        if abs(self.windup) > period * min_speed / 1.5:
            if abs(speed) < min_speed:
                speed = min_speed if self.windup > 0 else -min_speed
        else:
            speed = 0.0
        max_windup = 1.5 * period
        if abs(self.windup) > max_windup:
            self.windup = max_windup * sign(self.windup)
        last_speed = self.speed
        if speed or last_speed:
            m = speed * last_speed
            if m <= 0:                          # départ, arrêt ou inversion
                if t - self.windup_change < self.period:
                    if last_speed > 0:
                        speed = min_speed
                    elif last_speed < 0:
                        speed = -min_speed
                    else:
                        speed = 0.0
                else:
                    self.windup_change = t
                    if m < 0:
                        speed = 0.0
        speed = min(max(speed, -max_speed), max_speed)
        self.speed = speed
        return speed


def simulate(f=1.0, V=7.0, servo="real", period=0.4, smin=1.0, smax=1.0,
             P=.003, D=.09, DD=.075, PR=.005, FF=.6,
             psi0=5.0, cmd_step=0.0, helm=0.0, noise_h=0.2, noise_r=0.1,
             t_end=300.0, seed=1, filters=True):
    n = int(t_end / DT)
    T, K = T0 / f, K0 * f
    psi, r, delta = psi0, 0.0, 0.0
    command = cmd_step                  # consigne de cap (deg)
    last_command = 0.0 if cmd_step else command
    rng = np.random.default_rng(seed)
    sv = Servo(servo, period, smin, smax)
    heading_lp, hr_lp, hrr_lp, prev_r = psi0, 0.0, 0.0, 0.0
    cmd_rate = 0.0
    t_arr, psi_arr, del_arr, spd_arr = (np.zeros(n) for _ in range(4))
    for i in range(n):
        t = i * DT
        mh = psi + noise_h * rng.standard_normal()
        mr = r + noise_r * rng.standard_normal()
        hrr_raw = (mr - prev_r) / DT
        prev_r = mr
        if filters:                     # boatimu.py : constantes .2 / .2 / .1
            heading_lp = .2 * mh + .8 * heading_lp
            hr_lp = .2 * mr + .8 * hr_lp
            hrr_lp = .1 * hrr_raw + .9 * hrr_lp
        else:
            heading_lp, hr_lp, hrr_lp = mh, mr, hrr_raw
        err = min(max(heading_lp - command, -30.0), 30.0)
        diff = -(command - last_command)            # mode compas : signe inversé
        cmd_rate = .9 * cmd_rate + .1 * diff
        last_command = command
        pr = np.sqrt(abs(err)) * (-1 if err < 0 else 1)
        cmd = P * err + D * hr_lp + DD * hrr_lp + PR * pr + FF * cmd_rate
        speed = sv.command(cmd, t, DT)
        new_delta = delta + V * speed * DT
        if abs(new_delta) > RUDDER_RANGE:           # butée (défaut de barre)
            new_delta = max(min(new_delta, RUDDER_RANGE), -RUDDER_RANGE)
            speed = 0.0
        delta = new_delta
        h = DT / SUB
        for _ in range(SUB):                        # positif = fait baisser le cap
            r += (-r - K * (delta - helm)) / T * h
            psi += r * h
        t_arr[i], psi_arr[i], del_arr[i], spd_arr[i] = t, psi, delta, speed
    return t_arr, psi_arr, del_arr, spd_arr


def metrics(t, psi, delta, speed, target, e0):
    e = psi - target
    s = 1 if e0 > 0 else -1
    over = max(0.0, (-s * e).max()) / abs(e0) * 100.0 if e0 else float("nan")
    out = np.where(np.abs(e) > 1.0)[0]
    settle = 0.0 if len(out) == 0 else t[out[-1]]
    if len(out) and out[-1] >= len(t) - 2:
        settle = float("inf")
    last = t > (t[-1] - 100.0)
    rms = float(np.sqrt(np.mean(e[last] ** 2)))
    travel = float(np.sum(np.abs(np.diff(delta[last]))) / 100.0 * 60.0)
    # impulsions du servo : suites de vitesses non nulles de même signe
    runs, cur, sg = [], 0.0, 0
    for sp, dl in zip(speed, np.diff(np.concatenate(([0.0], delta)))):
        if sp != 0 and (sg == 0 or sign(sp) == sg):
            cur += abs(dl)
            sg = sign(sp)
        else:
            if sg != 0:
                runs.append(cur)
            cur, sg = (abs(dl), sign(sp)) if sp != 0 else (0.0, 0)
    quantum = float(np.mean(runs)) if runs else 0.0
    return dict(overshoot=over, settle=settle, rms=rms, travel=travel,
                quantum=quantum, pulses_min=len(runs) / (t[-1] / 60.0))


def fs(s, tmax):
    return f">{tmax:.0f}" if s == float("inf") else f"{s:.0f}"


def theory_psi(f, V, ts, P=.003, D=.09, DD=.075):
    """Réponse linéaire exacte du système bouclé (servo idéal, sans filtres)."""
    T, K = T0 / f, K0 * f
    A = np.array([[0, 1, 0],
                  [0, -1 / T, -K / T],
                  [V * P, V * D - V * DD / T, -V * DD * K / T]])
    w, vec = np.linalg.eig(A)
    c = np.linalg.solve(vec, np.array([5.0, 0.0, 0.0]))
    return [float(np.real(sum(c[k] * vec[0, k] * np.exp(w[k] * t) for k in range(3))))
            for t in ts], w


def main():
    print("=== S0 : validation (servo idéal, sans filtre ni bruit ni terme racine) ===")
    for f in (0.4, 1.0):
        ts = (20, 60, 120)
        th, poles = theory_psi(f, 7.0, ts)
        t, psi, de, sp = simulate(f=f, servo="ideal", filters=False, noise_h=0, noise_r=0,
                                  PR=0.0, FF=0.0, psi0=5.0, t_end=200)
        simv = [psi[int(x / DT)] for x in ts]
        print(f"  f={f:.1f} pôles={np.round(poles, 3)}")
        print("      cap à t=20/60/120 s  théorie :", [f"{x:+.2f}" for x in th],
              "| simulé :", [f"{x:+.2f}" for x in simv])

    print("\n=== S1 : écart initial de 5° (gains par défaut de `basic`), servo réel vs idéal ===")
    print(f"{'f':>4} | {'servo':<6} | {'dépass.%':>8} {'<1° à (s)':>9} {'RMS°':>5} "
          f"{'barre°/min':>10} {'quantum°':>8} {'impuls./min':>11}")
    for f in (0.4, 0.6, 1.0, 1.6):
        for mode in ("ideal", "real"):
            t, psi, de, sp = simulate(f=f, servo=mode, psi0=5.0, t_end=600)
            m = metrics(t, psi, de, sp, 0.0, 5.0)
            print(f"{f:4.1f} | {mode:<6} | {m['overshoot']:8.1f} {fs(m['settle'], 600):>9} "
                  f"{m['rms']:5.2f} {m['travel']:10.1f} {m['quantum']:8.2f} {m['pulses_min']:11.1f}")

    print("\n=== S2 : sensibilité à la vitesse du vérin V (f = 1,0, servo idéal puis réel) ===")
    print(f"{'V°/s':>5} | {'servo':<6} | {'pôle le + lent':>14} {'dépass.%':>8} {'<1° à (s)':>9} {'RMS°':>5}")
    for V in (3.0, 7.0, 12.0, 20.0):
        _, w = theory_psi(1.0, V, (0,))
        slow = max(w, key=lambda z: z.real)
        for mode in ("ideal", "real"):
            t, psi, de, sp = simulate(f=1.0, V=V, servo=mode, psi0=5.0, t_end=600)
            m = metrics(t, psi, de, sp, 0.0, 5.0)
            print(f"{V:5.0f} | {mode:<6} | {slow.real:+7.3f}{slow.imag:+.3f}j {m['overshoot']:8.1f} "
                  f"{fs(m['settle'], 600):>9} {m['rms']:5.2f}")

    print("\n=== S3 : mécanisme de période du servo (barre de compensation 3°, f = 1,0, V = 7°/s) ===")
    print(f"{'période':>7} {'speed.min':>9} | {'quantum°':>8} {'impuls./min':>11} {'RMS cap°':>8} {'barre°/min':>10}")
    for period in (0.1, 0.2, 0.4, 1.0):
        for smin in (1.0, 0.3):
            t, psi, de, sp = simulate(f=1.0, servo="real", period=period, smin=smin,
                                      psi0=0.0, helm=3.0, t_end=600)
            m = metrics(t, psi, de, sp, 0.0, 1.0)
            print(f"{period:7.1f} {smin * 100:8.0f}% | {m['quantum']:8.2f} {m['pulses_min']:11.1f} "
                  f"{m['rms']:8.2f} {m['travel']:10.1f}")

    print("\n=== S4 : changement de consigne de +20° (f = 1,0, servo réel) ===")
    print(f"{'FF':>4} | {'dépass.%':>8} {'<1° à (s)':>9}")
    for FF in (0.6, 0.0):
        t, psi, de, sp = simulate(f=1.0, FF=FF, psi0=0.0, cmd_step=20.0, t_end=600)
        m = metrics(t, psi, de, sp, 20.0, -20.0)
        print(f"{FF:4.1f} | {m['overshoot']:8.1f} {fs(m['settle'], 600):>9}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 2, figsize=(12, 8))
        for mode, lab in (("ideal", "servo idéal"), ("real", "servo réel (période 0,4 s)")):
            t, psi, de, sp = simulate(f=1.0, servo=mode, psi0=5.0, t_end=300)
            ax[0, 0].plot(t, psi, label=lab)
            ax[0, 1].plot(t, de, label=lab, drawstyle="steps-post")
        ax[0, 0].set_title("(a) écart de 5° : cap"); ax[0, 0].set_ylabel("cap (deg)")
        ax[0, 1].set_title("(b) angle de barre : le servo réel avance par impulsions")
        ax[0, 1].set_ylabel("barre (deg)")
        for V in (3.0, 7.0, 12.0, 20.0):
            t, psi, de, sp = simulate(f=1.0, V=V, servo="ideal", psi0=5.0, t_end=300)
            ax[1, 0].plot(t, psi, label=f"V = {V:.0f} °/s")
        ax[1, 0].set_title("(c) mêmes gains, vérins plus ou moins rapides"); ax[1, 0].set_ylabel("cap (deg)")
        for FF in (0.6, 0.0):
            t, psi, de, sp = simulate(f=1.0, FF=FF, psi0=0.0, cmd_step=20.0, t_end=300)
            ax[1, 1].plot(t, psi, label=f"FF = {FF}")
        ax[1, 1].axhline(20, color="gray", lw=.6)
        ax[1, 1].set_title("(d) changement de consigne de +20°"); ax[1, 1].set_ylabel("cap (deg)")
        for a in ax.ravel():
            a.set_xlabel("temps (s)"); a.set_xlim(0, 250); a.grid(alpha=.3); a.legend()
        fig.tight_layout()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pypilot_sim.png")
        fig.savefig(out, dpi=130)
        print("\nFigure :", out)
    except Exception as e:
        print("\n(pas de figure :", e, ")")


if __name__ == "__main__":
    main()
