"""Preuve de concept CON-010 (SIMULÉ) : lecteur de séquences de manœuvre, client de pypilot.

Cas : virement et empannage SailSim, (a) natif = saut de consigne géré par le pilote basic,
(b) séquence = pilote en veille, étapes angle/vitesse/fin rejouées par position_command.
Réglage commun : servo.speed.min = 30 (meilleur réglage de l'essai du jour).
"""
import json, sys, time
from banc import *

# (nom, angle du côté du virage en °, vitesse en %, durée max en s, événement)
SEQ = {
    "virement": [("lancer", 15, 60, 4.0, ("vent", 0, 45)),
                 ("passage", 8, 40, 3.0, None),
                 ("laisser courir", 0, 40, 2.0, None)],
    "empannage": [("lancer", 8, 40, 6.0, ("vent", 180, 20)),
                  ("contre-barre", -5, 100, 2.0, None)],
}
SCEN = {"virement": "tack_port_to_starboard", "empannage": "gybe_starboard_to_port"}
DUREE_MAX = 20.0


def resolv(a):
    return (a + 180) % 360 - 180


def joue_sequence(c, nom):
    log = c.log
    while c.num("rudder.angle") is None:
        time.sleep(0.1)
    time.sleep(3)
    h0 = c.num("ap.heading_command")
    while True:  # attendre le changement de consigne de SailSim (t = 30 s simulé)
        h = c.num("ap.heading_command")
        if h is not None and h0 is not None and abs(resolv(h - h0)) > 20:
            break
        time.sleep(0.05)
    cible = h
    sens = 1 if resolv(cible - h0) > 0 else -1  # +1 = virage à tribord (cap qui augmente)
    cap0, t0 = c.num("imu.heading"), time.monotonic()
    log.append((c.t(), "DÉBUT", nom, {"consigne_avant": h0, "consigne_après": cible, "sens": sens, "cap": cap0}))
    c.set("ap.enabled", False, "séquence : pilote en veille")
    if nom == "empannage":
        log.append((c.t(), "CONFIRMATION", "empannage confirmé (automatique en simulation)", None))
    for etape, angle, vit, duree, evt in SEQ[nom]:
        c.set("servo.speed.max", vit, etape)
        c.set("servo.command", 0, "contournement veille")
        c.set("servo.position_command", round(-sens * angle, 2), etape)  # pypilot : + = bâbord
        te, awa_prec = time.monotonic(), None
        while True:
            time.sleep(0.05)
            if c.num("rudder.angle") is None:
                log.append((c.t(), "ARRÊT", "potentiomètre invalide", None))
                c.set("ap.heading_command", c.num("imu.heading"), "cap actuel"); c.set("servo.speed.max", 100)
                c.set("ap.enabled", True); return
            if time.monotonic() - t0 > DUREE_MAX:
                log.append((c.t(), "ARRÊT", "durée maximale", None))
                c.set("ap.heading_command", c.num("imu.heading"), "cap actuel"); c.set("servo.speed.max", 100)
                c.set("ap.enabled", True); return
            if time.monotonic() - te >= duree:
                log.append((c.t(), "FIN ÉTAPE", etape, "durée"))
                break
            if evt:
                _, cible_awa, repli = evt
                awa = c.num("wind.direction")
                if awa is not None:
                    a = resolv(awa - cible_awa)
                    if awa_prec is not None and a * awa_prec < 0 and abs(a) < 90:
                        log.append((c.t(), "FIN ÉTAPE", etape, f"vent passe {cible_awa}° (awa {awa:.1f})"))
                        break
                    awa_prec = a
                cap = c.num("imu.heading")
                if cap is not None and abs(resolv(cap - cap0)) >= repli:
                    log.append((c.t(), "FIN ÉTAPE", etape, f"cap tourné de {repli}° (repli)"))
                    break
    c.set("servo.speed.max", 100)
    c.set("ap.heading_command", cible, "sortie : le pilote reprend")
    c.set("ap.enabled", True, "sortie")
    log.append((c.t(), "FIN", nom, {"durée_s": round(time.monotonic() - t0, 2)}))


def cas(nom, mode):
    tag = f"{nom}_{mode}"
    restart()
    c = Client(["imu.heading", "rudder.angle", "wind.direction", "ap.heading_command", "ap.enabled", "servo.speed.max"])
    c.set("servo.speed.min", 30)
    p = sailsim(SCEN[nom], OUT / f"{tag}.csv")
    if mode == "sequence":
        joue_sequence(c, nom)
    out = p.communicate()[0]
    c.close()
    (OUT / f"{tag}_sortie.txt").write_text(out, encoding="utf-8")
    json.dump(c.log, open(OUT / f"{tag}_journal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {tag} : code {p.returncode}", flush=True)
    for e in c.log:
        if e[1] != "ENVOI":
            print("   ", e, flush=True)


if __name__ == "__main__":
    for nom, mode in [(n, m) for n in ("virement", "empannage") for m in ("natif", "sequence")]:
        cas(nom, mode)
