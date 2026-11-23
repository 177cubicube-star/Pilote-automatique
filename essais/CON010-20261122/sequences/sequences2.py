"""Virement avec réglage des voiles (auto_sail_trim) : natif, séquence 15°, séquence 25° (plus d'inertie)."""
import sequences as S
from banc import *

VOILES = OUT / "pypilot_servo_voiles.toml"
S.SEQ["virement25"] = [("lancer", 25, 60, 4.0, ("vent", 0, 45))] + S.SEQ["virement"][1:]
S.SCEN["virement25"] = S.SCEN["virement"]


def cas(nom, mode, tag):
    restart()
    c = Client(["imu.heading", "rudder.angle", "wind.direction", "ap.heading_command", "ap.enabled", "servo.speed.max"])
    c.set("servo.speed.min", 30)
    p = sailsim(S.SCEN[nom], OUT / f"{tag}.csv", VOILES)
    if mode == "sequence":
        S.joue_sequence(c, nom)
    out = p.communicate()[0]
    c.close()
    (OUT / f"{tag}_sortie.txt").write_text(out, encoding="utf-8")
    json.dump(c.log, open(OUT / f"{tag}_journal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {tag} : code {p.returncode}", flush=True)
    for e in c.log:
        if e[1] != "ENVOI":
            print("   ", e, flush=True)


if __name__ == "__main__":
    cas("virement", "natif", "voiles_virement_natif")
    cas("virement", "sequence", "voiles_virement_seq15")
    cas("virement25", "sequence", "voiles_virement_seq25")
