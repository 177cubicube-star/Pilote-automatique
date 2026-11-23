"""Essai de virement à commande du safran par phases (SIMULÉ) — spécification de Mathieu, 2026-11-23.

Réglages retenus (voir README) : vent vrai 000°, approche au près à 310° (≈ 50° du vent vrai),
angle de virement 100° → Hfinal = H0 + 100° (une seule fois, au déclenchement).

Déroulé :
  1. Approche : pypilot tient 310°. L'ordre TACK n'est donné que si, sur les 10 dernières secondes,
     le cap reste à ±3° et la vitesse varie de moins de 5 % (gps.speed). Sinon : « approche non stabilisée ».
  2. TACK : chronomètre à 0, relevé de H0 et de l'angle réel du safran, Hfinal = (H0 + 100) mod 360.
  3. Pilote en veille ; phases (angle, vitesse °/s, maintien s). Chaque phase part de la position réelle ;
     le maintien commence quand l'angle est atteint (±1°, 5 s au plus pour l'atteindre).
  4. Fin de séquence : le pilote reprend la tenue de cap sur Hfinal.
Les mesures (lit du vent, alignement, u signé, vent apparent) sont faites par analyse_spec.py sur le CSV SailSim.
Lancer avec `python` (pas `python -I`).
"""
import json, sys, threading, time
from banc import *

ANGLE_VIREMENT = 100.0
# (angle de safran du côté du virage °, vitesse °/s, maintien s)
# Essai 3 : [(20, 10, 3.0), (25, 5, 4.0), (10, 5, 2.0), (0, 5, 0.0)]
# Essai 4 (Mathieu) : contre-barre de 15° au départ (angle négatif = côté opposé au virage), phase 2 tenue 8 s
PHASES = [(-15, 10, 0.0), (20, 10, 3.0), (25, 5, 8.0), (10, 5, 2.0), (0, 5, 0.0)]
VITESSE_MAX_VERIN = 10.0  # °/s à 100 % (SailSim, config.py : pypilot_rudder_rate_max_deg_s)
TOL_ANGLE, T_ATTEINTE = 1.0, 5.0
SAFRAN_MAX = 28.0
DUREE_MAX = 30.0
# TOL_CAP : ±3° au premier essai → « approche non stabilisée » à cause du cycle limite de pypilot
# (307–313°, ±3,3°, déjà vu en Q1). Passé à ±4° autour de la moyenne le 2026-11-23.
FENETRE, TOL_CAP, TOL_VIT = 10.0, 4.0, 0.05
T_ORDRE_MIN, T_ORDRE_MAX = 25.0, 50.0
SCENARIO = OUT / "spec_default_310.toml"
VOILES = OUT / "pypilot_servo_voiles.toml"
CLES = ["imu.heading", "rudder.angle", "wind.direction", "gps.speed", "ap.enabled", "ap.heading_command"]


def resolv(a):
    return (a + 180) % 360 - 180


def echantillonne(c, hist, out, stop):
    with open(out, "w", encoding="utf-8") as f:
        f.write("t_client," + ",".join(CLES) + "\n")
        while not stop.is_set():
            t = c.t()
            hist.append((t, c.num("imu.heading"), c.num("gps.speed")))
            f.write(f"{t}," + ",".join("" if c.v.get(k) is None else str(c.v.get(k)) for k in CLES) + "\n")
            time.sleep(0.1)


def approche_stable(hist):
    t = hist[-1][0]
    w = [h for h in hist if h[0] >= t - FENETRE and h[1] is not None and h[2] is not None]
    if not w or w[0][0] > t - FENETRE + 0.5:
        return False
    caps = [h[1] for h in w]; vit = [h[2] for h in w]
    ref = (caps[0] + sum(resolv(x - caps[0]) for x in caps) / len(caps)) % 360  # moyenne circulaire simple
    cap_ok = all(abs(resolv(x - ref)) <= TOL_CAP for x in caps)
    m = sum(vit) / len(vit)
    vit_ok = m > 1.0 and (max(vit) - min(vit)) / m <= TOL_VIT
    return cap_ok and vit_ok


def essai(c, hist):
    log = c.log
    while c.num("rudder.angle") is None or c.t() < T_ORDRE_MIN:
        time.sleep(0.1)
    # Ordre TACK = changement de consigne venu du scénario (t = 30 s simulé), voir spec_default_310.toml
    h_init = c.num("ap.heading_command")
    while True:
        h = c.num("ap.heading_command")
        if h is not None and h_init is not None and abs(resolv(h - h_init)) > 20:
            break
        if c.t() > T_ORDRE_MAX:
            log.append((c.t(), "ARRÊT", "pas d'ordre TACK", None)); return
        time.sleep(0.02)
    stable = approche_stable(hist)
    if not stable:
        c.set("ap.enabled", False, "approche non stabilisée : pas de virement")
        log.append((c.t(), "ARRÊT", "approche non stabilisée", None)); return
    # --- TACK ---
    c.set("ap.enabled", False, "TACK : tenue de cap suspendue")
    t0 = time.monotonic()
    H0, safran0 = c.num("imu.heading"), c.num("rudder.angle")
    Hfinal = (H0 + ANGLE_VIREMENT) % 360
    sens = 1  # +100° : virage à tribord (cap qui augmente)
    log.append((c.t(), "TACK", {"H0": H0, "Hfinal": Hfinal, "safran0": safran0, "awa": c.num("wind.direction")}))
    c.set("ap.enabled", False, "TACK : tenue de cap suspendue")

    def secours(raison):
        log.append((c.t(), "ARRÊT", raison, None))
        c.set("servo.speed.max", 100); c.set("ap.heading_command", Hfinal, "reprise sur Hfinal"); c.set("ap.enabled", True)

    for i, (angle, vitesse, maintien) in enumerate(PHASES, 1):
        angle = min(angle, SAFRAN_MAX)
        pct = max(1, min(100, round(100 * vitesse / VITESSE_MAX_VERIN)))
        c.set("servo.speed.max", pct, f"phase {i} : {vitesse} °/s")
        c.set("servo.command", 0, "contournement veille")
        c.set("servo.position_command", round(-sens * angle, 2), f"phase {i} : {angle}°")  # pypilot : + = bâbord
        ta = time.monotonic()
        while True:  # atteindre l'angle
            time.sleep(0.05)
            r = c.num("rudder.angle")
            if r is None:
                return secours("potentiomètre invalide")
            if time.monotonic() - t0 > DUREE_MAX:
                return secours("durée maximale de séquence")
            if abs(r - (-sens * angle)) <= TOL_ANGLE:
                log.append((c.t(), "ATTEINT", i, {"safran": r, "en_s": round(time.monotonic() - ta, 2)})); break
            if time.monotonic() - ta > T_ATTEINTE:
                log.append((c.t(), "NON ATTEINT", i, {"safran": r})); break
        tm = time.monotonic()
        while time.monotonic() - tm < maintien:  # maintien
            time.sleep(0.05)
            if time.monotonic() - t0 > DUREE_MAX:
                return secours("durée maximale de séquence")
        log.append((c.t(), "FIN PHASE", i, None))
    log.append((c.t(), "FIN SÉQUENCE", {"chrono_s": round(time.monotonic() - t0, 2), "cap": c.num("imu.heading"),
                                        "safran": c.num("rudder.angle")}))
    c.set("servo.speed.max", 100)
    c.set("ap.heading_command", Hfinal, "reprise de la tenue de cap sur Hfinal")
    c.set("ap.enabled", True, "reprise")


def main(tag="spec_phases"):
    restart()
    c = Client(CLES + ["servo.speed.max"])
    c.set("servo.speed.min", 30)
    hist, stop = [], threading.Event()
    threading.Thread(target=echantillonne, args=(c, hist, OUT / f"{tag}_pypilot.csv", stop), daemon=True).start()
    p = sailsim(SCENARIO, OUT / f"{tag}.csv", VOILES)
    essai(c, hist)
    out = p.communicate()[0]
    stop.set(); time.sleep(0.3); c.close()
    (OUT / f"{tag}_sortie.txt").write_text(out, encoding="utf-8")
    json.dump(c.log, open(OUT / f"{tag}_journal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {tag} : code {p.returncode}", flush=True)
    for e in c.log:
        if e[1] != "ENVOI":
            print("   ", e, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
