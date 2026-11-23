"""Essai SIMULÉ : pilote basic vs absolute, servo.speed.min 100 vs 30 (banc Q1 v5, Docker, couche servo).

Pour chaque cas : redémarre le conteneur, règle pypilot par JSON-TCP (pilote, speed.min),
lance SailSim, surveille ap.pilot pendant la course (repli éventuel vers basic) et
réaffirme le pilote demandé dès que l'angle de barre est valide.
"""
import json, socket, subprocess, sys, threading, time, pathlib

SAILSIM = pathlib.Path(r"C:\Users\mat_g\Documents\sailsim-test")
OUT = pathlib.Path(__file__).parent
PY = str(SAILSIM / ".venv" / "Scripts" / "python.exe")

CASES = [("basic", 100), ("basic", 30), ("absolute", 100), ("absolute", 30)]


def run_case(pilot, smin, tag):
    subprocess.run(["docker", "restart", "pp"], check=True, capture_output=True)
    time.sleep(6)
    s = socket.create_connection(("localhost", 23322), timeout=5)
    s.sendall(f"servo.speed.min={smin}\nap.pilot=\"{pilot}\"\n".encode())
    s.sendall(b'watch={"ap.pilot":true,"rudder.angle":0.5,"servo.speed.min":true}\n')
    log, state = [], {"pilot": None, "rudder_ok": False, "reasserts": 0, "stop": False}
    t0 = time.monotonic()

    def reader():
        buf = ""
        s.settimeout(0.5)
        while not state["stop"]:
            try:
                data = s.recv(4096).decode(errors="replace")
            except socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                k, _, v = line.strip().partition("=")
                t = round(time.monotonic() - t0, 2)
                if k == "ap.pilot":
                    state["pilot"] = json.loads(v)
                    log.append((t, "ap.pilot", state["pilot"]))
                    if pilot != "basic" and state["pilot"] != pilot and state["rudder_ok"]:
                        s.sendall(f'ap.pilot="{pilot}"\n'.encode()); state["reasserts"] += 1
                elif k == "rudder.angle":
                    ok = v not in ("false", "true")
                    if ok and not state["rudder_ok"]:
                        log.append((t, "rudder.angle valide", v))
                        if pilot != "basic" and state["pilot"] != pilot:
                            s.sendall(f'ap.pilot="{pilot}"\n'.encode()); state["reasserts"] += 1
                    state["rudder_ok"] = ok
                elif k == "servo.speed.min":
                    log.append((t, "servo.speed.min", v))

    th = threading.Thread(target=reader, daemon=True); th.start()
    time.sleep(1)
    csv = OUT / f"{tag}.csv"
    r = subprocess.run([PY, "-m", "sailsim", "--scenario", "pypilot_heading_hold", "--yacht", "default",
                        "--autopilot", "pypilot_servo", "--output", str(csv)],
                       cwd=SAILSIM, capture_output=True, text=True)
    state["stop"] = True; th.join(2); s.close()
    (OUT / f"{tag}_sortie.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    pilots_seen = sorted({e[2] for e in log if e[1] == "ap.pilot"})
    res = {"cas": tag, "pilote_demande": pilot, "speed_min": smin, "pilotes_vus": pilots_seen,
           "reaffirmations": state["reasserts"], "pilote_final": state["pilot"], "journal": log[:40],
           "code_retour": r.returncode}
    (OUT / f"{tag}_bilan.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res, r.stdout


if __name__ == "__main__":
    for pilot, smin in CASES:
        tag = f"{pilot}_min{smin}"
        res, out = run_case(pilot, smin, tag)
        gate = [l for l in out.splitlines() if "[OK]" in l or "[FAIL]" in l or "Result" in l]
        print(f"== {tag} : pilotes vus {res['pilotes_vus']}, final {res['pilote_final']}, "
              f"réaffirmations {res['reaffirmations']}, code {res['code_retour']}")
        print("\n".join(gate), flush=True)
