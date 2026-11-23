"""CON-010, virement v2 (SIMULÉ) : garder la barre jusqu'à ce que les voiles portent sur le nouveau bord.

Leçon du témoin Nomoto (essais du 2026-11-22, relus le 2026-11-23) : il garde la barre à fond
jusqu'à un vent apparent d'environ −26° sur l'autre bord ; les séquences v1 relâchaient bout au vent.

Fin d'étape sur ÉVÉNEMENT, durée seulement comme garde-fou :
  - "vent_nez"    : le vent apparent change de signe (passe 0°) ;
  - "vent_porte"  : le vent apparent est sur l'autre bord d'au moins N° ;
  - "proche_cap"  : le cap est à moins de N° de la cible ;
  - repli sans girouette : cap tourné de N° depuis le début.

Variantes :
  A : lancer 27° → tenir 27° jusqu'à vent_porte 25° → pilote ;
  B : comme A, puis ramener 0° jusqu'à proche_cap 20° → pilote.
Banc : conteneur `pp` (pypilot fdff88f, couche servo), bateau `default`, voiles réglées (auto_sail_trim),
servo.speed.min = 30. Lancer avec `python` (pas `python -I`) depuis n'importe où.
"""
import json, time
from banc import *

# (nom, angle du côté du virage °, vitesse %, durée max s, (événement, seuil), repli cap tourné °)
SEQ = {
    "A": [("lancer", 27, 100, 10.0, ("vent_nez", 0), 45),
          ("tenir", 27, 100, 40.0, ("vent_porte", 25), 75)],
    "B": [("lancer", 27, 100, 10.0, ("vent_nez", 0), 45),
          ("tenir", 27, 100, 40.0, ("vent_porte", 25), 75),
          ("ramener", 0, 60, 8.0, ("proche_cap", 20), None)],
}
DUREE_MAX = 60.0
VOILES = OUT / "pypilot_servo_voiles.toml"
SCENARIO = "tack_port_to_starboard"


def resolv(a):
    return (a + 180) % 360 - 180


def joue(c, nom):
    log = c.log
    while c.num("rudder.angle") is None:
        time.sleep(0.1)
    time.sleep(3)
    h0 = c.num("ap.heading_command")
    while True:  # attendre la consigne de virement de SailSim (t = 30 s simulé)
        h = c.num("ap.heading_command")
        if h is not None and h0 is not None and abs(resolv(h - h0)) > 20:
            break
        time.sleep(0.05)
    cible = h
    sens = 1 if resolv(cible - h0) > 0 else -1  # +1 = virage à tribord
    cap0, t0 = c.num("imu.heading"), time.monotonic()
    awa0 = c.num("wind.direction")
    signe0 = 1 if resolv(awa0 or 0) >= 0 else -1  # bord de départ du vent apparent
    log.append((c.t(), "DÉBUT", nom, {"consigne_avant": h0, "cible": cible, "sens": sens, "cap": cap0, "awa": awa0}))
    c.set("ap.enabled", False, "séquence : pilote en veille")
    for etape, angle, vit, duree, (evt, seuil), repli in SEQ[nom]:
        c.set("servo.speed.max", vit, etape)
        c.set("servo.command", 0, "contournement veille")
        c.set("servo.position_command", round(-sens * angle, 2), etape)  # pypilot : + = bâbord
        te = time.monotonic()
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
                log.append((c.t(), "FIN ÉTAPE", etape, "durée (garde-fou)"))
                break
            awa, cap = c.num("wind.direction"), c.num("imu.heading")
            a = resolv(awa) if awa is not None else None
            if evt == "vent_nez" and a is not None and a * signe0 < 0 and abs(a) < 90:
                log.append((c.t(), "FIN ÉTAPE", etape, f"vent au nez (awa {a:.1f})")); break
            if evt == "vent_porte" and a is not None and a * signe0 < 0 and abs(a) >= seuil:
                log.append((c.t(), "FIN ÉTAPE", etape, f"vent porte sur l'autre bord (awa {a:.1f})")); break
            if evt == "proche_cap" and cap is not None and abs(resolv(cible - cap)) <= seuil:
                log.append((c.t(), "FIN ÉTAPE", etape, f"à {abs(resolv(cible - cap)):.1f}° de la cible")); break
            if repli and cap is not None and abs(resolv(cap - cap0)) >= repli:
                log.append((c.t(), "FIN ÉTAPE", etape, f"cap tourné de {repli}° (repli)")); break
    c.set("servo.speed.max", 100)
    c.set("ap.heading_command", cible, "sortie : le pilote reprend")
    c.set("ap.enabled", True, "sortie")
    log.append((c.t(), "FIN", nom, {"durée_s": round(time.monotonic() - t0, 2)}))


def cas(nom):
    tag = f"virement_v2_{nom}"
    restart()
    c = Client(["imu.heading", "rudder.angle", "wind.direction", "ap.heading_command", "ap.enabled", "servo.speed.max"])
    c.set("servo.speed.min", 30)
    p = sailsim(SCENARIO, OUT / f"{tag}.csv", VOILES)
    joue(c, nom)
    out = p.communicate()[0]
    c.close()
    (OUT / f"{tag}_sortie.txt").write_text(out, encoding="utf-8")
    json.dump(c.log, open(OUT / f"{tag}_journal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {tag} : code {p.returncode}", flush=True)
    for e in c.log:
        if e[1] != "ENVOI":
            print("   ", e, flush=True)


if __name__ == "__main__":
    for nom in ("A", "B"):
        cas(nom)
