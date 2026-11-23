"""CON-010, virement v3 (SIMULÉ) : barre à 29° et sortie en survirage (idée de Mathieu, 2026-11-23).

Trois choses dans un même passage :
  1. DIAGNOSTIC : un échantillonneur enregistre toutes les 0,1 s ce que pypilot renvoie
     (wind.direction, imu.heading, gps.speed, rudder.angle) → <tag>_pypilot.csv,
     à comparer au vent apparent du CSV SailSim ;
  2. A29 : comme la séquence A, mais 29° demandés (butée pypilot à 30°) ;
  3. C : A29, puis « abattre » = pilote sur cible + 10° jusqu'à ce que la vitesse remonte,
     puis « remonter » = pilote sur la cible.

Étape barre  : ("barre", nom, angle, vitesse %, durée max s, (événement, seuil), repli cap tourné °)
Étape pilote : ("pilote", nom, décalage de consigne °, durée max s, vitesse de fin en nœuds ou None)
Banc : conteneur `pp`, bateau `default`, voiles réglées, servo.speed.min = 30. Lancer avec `python`.
"""
import json, threading, time
from banc import *

SEQ = {
    "A29": [("barre", "lancer", 29, 100, 10.0, ("vent_nez", 0), 45),
            ("barre", "tenir", 29, 100, 40.0, ("vent_porte", 25), 75)],
    "C": [("barre", "lancer", 29, 100, 10.0, ("vent_nez", 0), 45),
          ("barre", "tenir", 29, 100, 40.0, ("vent_porte", 25), 75),
          ("pilote", "abattre", 10, 15.0, 6.0),
          ("pilote", "remonter", 0, 0.0, None)],
    # D : demande de Mathieu (2026-11-23) — toute la séquence en 30 s au maximum
    "D30": [("barre", "lancer", 29, 100, 12.0, ("vent_nez", 0), 45),
            ("barre", "tenir", 29, 100, 12.0, ("vent_porte", 20), 75),
            ("pilote", "abattre", 10, 6.0, 6.0),
            ("pilote", "remonter", 0, 0.0, None)],
}
DUREE_MAX = 70.0
DUREE_MAX_SEQ = {"D30": 30.0}
VOILES = OUT / "pypilot_servo_voiles.toml"
SCENARIO = "tack_port_to_starboard"
CLES = ["wind.direction", "imu.heading", "gps.speed", "rudder.angle", "ap.enabled", "ap.heading_command"]


def resolv(a):
    return (a + 180) % 360 - 180


def echantillonne(c, out, stop):
    with open(out, "w", encoding="utf-8") as f:
        f.write("t_client," + ",".join(CLES) + "\n")
        while not stop.is_set():
            f.write(f"{c.t()}," + ",".join("" if c.v.get(k) is None else str(c.v.get(k)) for k in CLES) + "\n")
            time.sleep(0.1)


def joue(c, nom):
    log = c.log
    while c.num("rudder.angle") is None:
        time.sleep(0.1)
    time.sleep(3)
    h0 = c.num("ap.heading_command")
    while True:
        h = c.num("ap.heading_command")
        if h is not None and h0 is not None and abs(resolv(h - h0)) > 20:
            break
        time.sleep(0.05)
    cible = h
    sens = 1 if resolv(cible - h0) > 0 else -1
    cap0, t0 = c.num("imu.heading"), time.monotonic()
    awa0 = c.num("wind.direction")
    signe0 = 1 if resolv(awa0 or 0) >= 0 else -1
    log.append((c.t(), "DÉBUT", nom, {"consigne_avant": h0, "cible": cible, "sens": sens, "cap": cap0, "awa": awa0}))

    def secours(raison):
        log.append((c.t(), "ARRÊT", raison, None))
        c.set("ap.heading_command", c.num("imu.heading"), "cap actuel"); c.set("servo.speed.max", 100)
        c.set("ap.enabled", True)

    for e in SEQ[nom]:
        if e[0] == "pilote":
            _, etape, decal, duree, v_fin = e
            c.set("servo.speed.max", 100)
            c.set("ap.heading_command", (cible + sens * decal) % 360, etape)
            c.set("ap.enabled", True, etape)
            te = time.monotonic()
            while time.monotonic() - te < duree:
                time.sleep(0.05)
                v = c.num("gps.speed")
                if v_fin is not None and v is not None and v >= v_fin:
                    log.append((c.t(), "FIN ÉTAPE", etape, f"vitesse remontée ({v:.1f} nd)")); break
            else:
                if duree > 0:
                    log.append((c.t(), "FIN ÉTAPE", etape, "durée (garde-fou)"))
            continue
        _, etape, angle, vit, duree, (evt, seuil), repli = e
        c.set("ap.enabled", False, etape)
        c.set("servo.speed.max", vit, etape)
        c.set("servo.command", 0, "contournement veille")
        c.set("servo.position_command", round(-sens * angle, 2), etape)  # pypilot : + = bâbord
        te = time.monotonic()
        while True:
            time.sleep(0.05)
            if c.num("rudder.angle") is None:
                return secours("potentiomètre invalide")
            if time.monotonic() - t0 > DUREE_MAX_SEQ.get(nom, DUREE_MAX):
                return secours("durée maximale")
            if time.monotonic() - te >= duree:
                log.append((c.t(), "FIN ÉTAPE", etape, "durée (garde-fou)")); break
            awa, cap = c.num("wind.direction"), c.num("imu.heading")
            a = resolv(awa) if awa is not None else None
            if evt == "vent_nez" and a is not None and a * signe0 < 0 and abs(a) < 90:
                log.append((c.t(), "FIN ÉTAPE", etape, f"vent au nez (awa {a:.1f})")); break
            if evt == "vent_porte" and a is not None and a * signe0 < 0 and abs(a) >= seuil:
                log.append((c.t(), "FIN ÉTAPE", etape, f"vent porte sur l'autre bord (awa {a:.1f})")); break
            if repli and cap is not None and abs(resolv(cap - cap0)) >= repli:
                log.append((c.t(), "FIN ÉTAPE", etape, f"cap tourné de {repli}° (repli)")); break
    c.set("servo.speed.max", 100)
    c.set("ap.heading_command", cible, "sortie : le pilote tient la cible")
    c.set("ap.enabled", True, "sortie")
    log.append((c.t(), "FIN", nom, {"durée_s": round(time.monotonic() - t0, 2)}))


def cas(nom):
    tag = f"virement_v3_{nom}"
    restart()
    c = Client(CLES + ["servo.speed.max"])
    c.set("servo.speed.min", 30)
    stop = threading.Event()
    threading.Thread(target=echantillonne, args=(c, OUT / f"{tag}_pypilot.csv", stop), daemon=True).start()
    p = sailsim(SCENARIO, OUT / f"{tag}.csv", VOILES)
    joue(c, nom)
    out = p.communicate()[0]
    stop.set(); time.sleep(0.3)
    c.close()
    (OUT / f"{tag}_sortie.txt").write_text(out, encoding="utf-8")
    json.dump(c.log, open(OUT / f"{tag}_journal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {tag} : code {p.returncode}", flush=True)
    for e in c.log:
        if e[1] != "ENVOI":
            print("   ", e, flush=True)


if __name__ == "__main__":
    import sys
    for nom in (sys.argv[1:] or ["A29", "C"]):
        cas(nom)
