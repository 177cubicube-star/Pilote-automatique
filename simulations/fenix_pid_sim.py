#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation du PID de Fenix (port de PID_ext::Compute, variante PID_ADVANCED1)
couplé à un bateau de Nomoto du premier ordre et à un vérin à vitesse limitée.

Ce que ce script est :
  - un port ligne à ligne de libraries_ext/PID_v1_ext.cpp (lecture du code, pas
    d'exécution sur Arduino) ;
  - un banc d'essai simple pour regarder l'effet du facteur de vitesse, de son
    plafond et du filtre dérivé.

Ce que ce script n'est PAS :
  - une validation en mer. Le bateau est un modèle linéaire du 1er ordre, sans
    vagues, sans filtre d'observation de houle, sans modèle de référence de
    Fossen ni feedforward (FF = 0, windFF = 0). Sans modèle de référence, un
    écart brusque est plus sévère que ce que Fenix voit réellement lors d'un
    changement de cap (où l'intégrale est gelée pendant la transition).

Hypothèses (à contester si besoin) :
  - PID_v1 standard (non inclus dans le dépôt) : ki *= Te, kd /= Te, et
    signes inversés si ControllerDirection == REVERSE (c'est le cas par défaut).
  - Période d'échantillonnage 100 ms (HC_PIDGAIN.sampleTime).
  - Bateau 12 m : T = 2,26 s, K = 0,19 1/s à la vitesse de référence (setTK du
    constructeur de Autopilot). À la vitesse relative f : K_eff = K*f et
    T_eff = T/f (même mise à l'échelle que OnlineNomotoIdentifier::scaleKTeff).
  - Vérin : 7 deg/s (70 deg parcourus en ~10 s), bande morte de 0,7 deg. Le
    délai de 1,8 s entre inversions (ACTUATOR_STOP_TIME) n'est PAS modélisé.
  - Écart de barre transmis au PID = (cible - barre réelle), en dixièmes de degré
    (je n'ai pas relu la valeur de retour exacte de controlActuator).

Usage :  python3 -I fenix_pid_sim.py
"""
import os

import numpy as np

# ---- constantes reprises de PID_v1_ext.h / .cpp -----------------------------
SAMPLE_S = 0.1
MAX_PID_TURN = 100.0
I_MAX_COEFICIENT = 1.5
I_ACTUATOR_BUSY_THRESHOLD = 10
D_DERR_UMBRAL = 0.5
D_RUDDER_ERROR_UMBRAL = 10.0
MIN_DEADBAND = 0.5
ALFA_10, ALFA_90, ALFA_20, ALFA_80 = 0.1, 0.9, 0.2, 0.8

# ---- bateau (Autopilot.cpp : setTK(2.26, 0.19, 1.0)) -------------------------
T0, K0 = 2.26, 0.19


def sgn(x):
    """Équivalent de (x > 0) ? 1 : -1 en C++ (0 donne -1)."""
    return 1 if x > 0 else -1


class FenixPID:
    def __init__(self, Kp=3.5, Ki=0.10, Kd=3.0, out_max=350.0,
                 sched="fenix", reverse=True, fix_kd_prev=False,
                 deadband=MIN_DEADBAND):
        Kp, Ki, Kd = (round(v * 100) / 100.0 for v in (Kp, Ki, Kd))
        self.kp, self.ki, self.kd = Kp, Ki * SAMPLE_S, Kd / SAMPLE_S
        if reverse:
            self.kp, self.ki, self.kd = -self.kp, -self.ki, -self.kd
        self.out_max, self.out_min = out_max, -out_max
        self.IoutMax = self.out_max / I_MAX_COEFICIENT
        self.IoutMin = self.out_min / I_MAX_COEFICIENT
        self.sched = sched            # "fenix" (plafonné), "none" ou "inverse" (hypothèse)
        self.fix_kd_prev = fix_kd_prev
        self.deadband = deadband      # calcDeadband() n'est jamais appelé : reste à 0,5
        self.in_deadband = False
        self.ITerm = 0.0
        self.last_input = 0.0
        self.dInput_prev = 0.0
        self.kd_prev = 0.0
        self.timon_en_posicion = False
        self.error_prev = 1.0
        self.derr_prev = 0.0
        self.avg_rudder_error = 0.0
        self.clamp_I = False
        self.info = {}

    def start(self, input0):
        self.last_input = input0      # PID::Initialize()

    def compute(self, input_, rudder_error, factor):
        FF = 0.0
        windFF = 0.0
        error = 0.0 - input_          # consigne = 0

        cap = abs(self.out_max / (self.kp * MAX_PID_TURN))
        if self.sched == "fenix":
            factor = min(factor, cap)           # ligne 102 de PID_v1_ext.cpp
        elif self.sched == "inverse":
            factor = 1.0 / factor               # hypothèse : sens opposé, sans plafond
        else:
            factor = 1.0
        sqr = factor * factor
        kp_eff, ki_eff, kd_eff = self.kp * sqr, self.ki * sqr, self.kd / factor
        out_max_eff = min(self.out_max * sqr, self.out_max)
        out_min_eff = max(self.out_min * sqr, self.out_min)

        error_eff = error - self.deadband * sgn(error)
        kp_contrib = kp_eff * error_eff

        busy = abs(rudder_error) > I_ACTUATOR_BUSY_THRESHOLD
        if (not busy) and (not self.timon_en_posicion):
            self.timon_en_posicion = True
        elif busy:
            self.timon_en_posicion = False

        derr = error_eff - self.error_prev
        derr = derr * ALFA_10 + ALFA_90 * self.derr_prev
        self.avg_rudder_error = rudder_error * ALFA_10 + ALFA_90 * self.avg_rudder_error
        sin_reaccion = (abs(derr) < D_DERR_UMBRAL and
                        abs(self.avg_rudder_error) <= D_RUDDER_ERROR_UMBRAL)

        permitir = not (self.clamp_I or self.in_deadband)
        if self.timon_en_posicion and not sin_reaccion:
            permitir = False
        if FF != 0:
            permitir = False
        if permitir:
            self.ITerm += ki_eff * error_eff
        self.ITerm = min(max(self.ITerm, self.IoutMin), self.IoutMax)

        dInput = input_ - self.last_input
        dInput = dInput * ALFA_20 + ALFA_80 * self.dInput_prev
        kd_contrib = (-kd_eff * dInput) * ALFA_20 + self.kd_prev * ALFA_80
        if self.fix_kd_prev:          # variante : ce que le commentaire laisse entendre
            self.kd_prev = kd_contrib

        out_libre = kp_contrib + self.ITerm + kd_contrib + FF + windFF
        out, saturated = out_libre, False
        if out_libre > out_max_eff:
            out, saturated = out_max_eff, True
        elif out_libre < out_min_eff:
            out, saturated = out_min_eff, True

        al_mismo_lado = not ((sgn(error_eff) * sgn(out)) == 1)
        self.clamp_I = (saturated and al_mismo_lado) or busy
        if self.clamp_I and saturated and self.ITerm != 0:
            self.ITerm *= 0.99

        self.last_input = input_
        self.error_prev = error_eff
        self.derr_prev = derr
        self.dInput_prev = dInput

        self.info = dict(factor=factor, cap=cap, kp_eff=abs(kp_eff),
                         kd_eff=abs(kd_eff), out_max_deg=out_max_eff / 10.0)
        return out


def simulate(f_boat, sched="fenix", Kp=3.5, Ki=0.10, Kd=3.0, fix_kd_prev=False,
             psi0=20.0, helm=0.0, noise=0.2, t_end=300.0, seed=1,
             rate=7.0, stop_band=0.7, deadband=MIN_DEADBAND):
    dt = 0.05
    n = int(t_end / dt)
    T, K = T0 / f_boat, K0 * f_boat
    psi, r, delta, target = psi0, 0.0, 0.0, 0.0
    pid = FenixPID(Kp, Ki, Kd, sched=sched, fix_kd_prev=fix_kd_prev,
                   deadband=deadband)
    rng = np.random.default_rng(seed)
    pid.start(-psi0)
    t_arr, psi_arr, del_arr = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        if i % 2 == 0:                      # PID à 10 Hz
            meas = psi + noise * rng.standard_normal()
            rudder_error = int(round((target - delta) * 10.0))
            u = pid.compute(-meas, rudder_error, f_boat)
            target = float(np.clip(u / 10.0, -35.0, 35.0))
        e = target - delta
        if abs(e) > stop_band:
            delta += float(np.clip(e, -rate * dt, rate * dt))
        r += (K * (delta + helm) - r) / T * dt
        psi += r * dt
        t_arr[i], psi_arr[i], del_arr[i] = i * dt, psi, delta
    return t_arr, psi_arr, del_arr, pid.info


def metrics(t, psi, delta, psi0, band=1.0):
    over = max(0.0, -psi.min()) / abs(psi0) * 100.0 if psi0 else float("nan")
    out = np.where(np.abs(psi) > band)[0]
    settle = 0.0 if len(out) == 0 else t[out[-1]]
    if len(out) and out[-1] >= len(t) - 2:
        settle = float("inf")
    last = t > (t[-1] - 100.0)
    rms = float(np.sqrt(np.mean(psi[last] ** 2)))
    travel = float(np.sum(np.abs(np.diff(delta[last]))) / 100.0 * 60.0)  # deg/min
    return dict(overshoot=over, settle=settle, rms=rms, travel=travel,
                max_delta=float(np.abs(delta).max()))


def fs(s, tmax):
    return f">{tmax:.0f}" if s == float("inf") else f"{s:.0f}"


def main():
    print("=== S0 : validation du banc (PD pur, sans bande morte ni bruit, vérin idéal) ===")
    print("Théorie : T s² + (1 + K·kd) s + K·kp = 0 ; kp = 0,35 deg/deg ; "
          "kd réel = 0,06 (filtre tel que codé) ou 0,30 (filtre corrigé)")
    for f in (0.4, 1.0):
        T, K = T0 / f, K0 * f
        for fix, kd in ((False, 0.06), (True, 0.30)):
            z = (1 + K * kd) / (2 * np.sqrt(T * K * 0.35))
            t, psi, de, _ = simulate(f, sched="none", Ki=0.0, psi0=5.0, noise=0.0,
                                     deadband=0.0, stop_band=0.0, rate=1e3,
                                     t_end=600, fix_kd_prev=fix)
            m = metrics(t, psi, de, 5.0, band=0.5)
            print(f"  f={f:.1f} filtre {'corrigé' if fix else 'codé  '} : "
                  f"ζ théorique = {z:4.2f} (suramorti) | dépassement simulé = "
                  f"{m['overshoot']:.2f} % | |cap|<0,5° à {fs(m['settle'], 600)} s")

    print("\n=== S1 : écart de 5° à la mise en route, gains par défaut (Kp 3,5 / Ki 0,1 / Kd 3) ===")
    print("  (vérin sans bande morte : on isole l'effet de la loi de commande)")
    print("  modes : fenix = tel que codé | none = pas de facteur de vitesse | "
          "inverse = hypothèse (gains ÷ f²)")
    print(f"{'f':>4} | {'mode':<8} | {'f_ctl':>5} {'Kp_eff':>6} | "
          f"{'dépass.%':>8} {'<1° à (s)':>9} {'barre°/min':>10}")
    for f in (0.4, 0.6, 0.8, 1.0, 1.6):
        for mode in ("fenix", "none", "inverse"):
            t, psi, de, info = simulate(f, sched=mode, psi0=5.0, t_end=600, stop_band=0.0)
            m = metrics(t, psi, de, 5.0)
            print(f"{f:4.1f} | {mode:<8} | {info['factor']:5.2f} {info['kp_eff']:6.2f} | "
                  f"{m['overshoot']:8.1f} {fs(m['settle'], 600):>9} {m['travel']:10.1f}")

    print("\n=== S2 : balayage de Kp configuré, f = 1,0, embardée de 20° ===")
    print(f"{'Kp':>4} | {'plafond':>7} {'f_ctl':>5} {'Kp_eff':>6} {'Kd_eff':>6} {'lim.barre':>9} | "
          f"{'barre max':>9} {'dépass.%':>8}")
    for Kp in (2.0, 3.5, 5.0, 7.0, 10.0):
        t, psi, de, info = simulate(1.0, Kp=Kp, psi0=20.0)
        m = metrics(t, psi, de, 20.0)
        print(f"{Kp:4.1f} | {info['cap']:7.2f} {info['factor']:5.2f} {info['kp_eff']:6.2f} "
              f"{info['kd_eff']:6.1f} {info['out_max_deg']:8.1f}° | "
              f"{m['max_delta']:8.1f}° {m['overshoot']:8.1f}")

    print("\n=== S3 : filtre dérivé codé vs corrigé (f = 1,0, bruit de cap 0,2°) ===")
    print(f"{'variante':<10} | {'RMS cap°':>8} {'barre°/min':>10}")
    for fix in (False, True):
        t, psi, de, _ = simulate(1.0, fix_kd_prev=fix, psi0=5.0, t_end=600)
        m = metrics(t, psi, de, 5.0)
        print(f"{'corrigé' if fix else 'codé':<10} | {m['rms']:8.2f} {m['travel']:10.1f}")

    print("\n=== S4 : bande morte « décalée » (écart initial 0,3°, PD seul, vérin idéal) ===")
    for db in (MIN_DEADBAND, 0.0):
        t, psi, de, _ = simulate(1.0, sched="none", Ki=0.0, psi0=0.3, noise=0.0,
                                 deadband=db, stop_band=0.0, rate=1e3, t_end=300)
        print(f"  bande morte {db:.1f}° -> cap final après 300 s : {psi[-1]:+.2f}°")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 2, figsize=(12, 8))
        for k, f in enumerate((0.5, 1.6)):
            for mode, lab in (("fenix", "Fenix tel que codé"),
                              ("none", "sans facteur de vitesse"),
                              ("inverse", "hypothèse : gains ÷ f²")):
                t, p, _, _ = simulate(f, sched=mode, psi0=5.0, t_end=600, stop_band=0.0)
                ax[0, k].plot(t, p, label=lab, ls="--" if mode == "none" else "-")
            ax[0, k].set_title(f"({'ab'[k]}) f = {f} : écart de 5° à la mise en route")
            ax[0, k].set_ylabel("cap (deg)"); ax[0, k].set_xlim(0, 400)
            ax[0, k].legend(); ax[0, k].grid(alpha=.3)
        for Kp in (2.0, 3.5, 7.0):
            t, pk, dk, info = simulate(1.0, Kp=Kp, psi0=20.0, t_end=300)
            ax[1, 0].plot(t, pk, label=f"Kp = {Kp}")
            ax[1, 1].plot(t, dk, label=f"Kp = {Kp} (limite barre {info['out_max_deg']:.1f}°)")
        ax[1, 0].set_title("(c) Balayage de Kp (f = 1,0) : cap"); ax[1, 0].set_ylabel("cap (deg)")
        ax[1, 1].set_title("(d) Balayage de Kp : angle de barre"); ax[1, 1].set_ylabel("barre (deg)")
        for a in (ax[1, 0], ax[1, 1]):
            a.set_xlim(0, 150); a.legend(); a.grid(alpha=.3)
        for a in ax.ravel():
            a.set_xlabel("temps (s)")
        fig.tight_layout()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fenix_pid_sim.png")
        fig.savefig(out, dpi=130)
        print("\nFigure :", out)
    except Exception as e:  # matplotlib absent : on ne bloque pas
        print("\n(pas de figure :", e, ")")


if __name__ == "__main__":
    main()
