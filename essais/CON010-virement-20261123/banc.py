"""Outils communs : conteneur pypilot, client JSON-TCP avec surveillance, lancement de SailSim."""
import json, socket, subprocess, threading, time, pathlib

SAILSIM = pathlib.Path(r"C:\Users\mat_g\Documents\sailsim-test")
PY = str(SAILSIM / ".venv" / "Scripts" / "python.exe")
OUT = pathlib.Path(__file__).parent


def restart():
    subprocess.run(["docker", "restart", "pp"], check=True, capture_output=True)
    time.sleep(6)


class Client:
    """Connexion JSON-TCP à pypilot ; garde la dernière valeur de chaque clé surveillée."""

    def __init__(self, watch):
        self.s = socket.create_connection(("localhost", 23322), timeout=5)
        self.v, self.log, self.t0, self.stop = {}, [], time.monotonic(), False
        self.lock = threading.Lock()
        self.send("watch=" + json.dumps({k: True for k in watch}))
        threading.Thread(target=self._reader, daemon=True).start()

    def t(self):
        return round(time.monotonic() - self.t0, 2)

    def send(self, line):
        with self.lock:
            self.s.sendall((line + "\n").encode())

    def set(self, key, value, note=""):
        self.send(f"{key}={json.dumps(value)}")
        self.log.append((self.t(), "ENVOI", key, value, note))

    def _reader(self):
        buf = ""
        self.s.settimeout(0.5)
        while not self.stop:
            try:
                d = self.s.recv(8192).decode(errors="replace")
            except socket.timeout:
                continue
            except OSError:
                break
            if not d:
                break
            buf += d
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                k, _, val = line.strip().partition("=")
                try:
                    self.v[k] = json.loads(val)
                except ValueError:
                    pass

    def num(self, key):
        x = self.v.get(key)
        return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None

    def close(self):
        self.stop = True
        self.s.close()


def sailsim(scenario, csv, autopilot="pypilot_servo"):
    return subprocess.Popen([PY, "-m", "sailsim", "--scenario", str(scenario), "--yacht", "default",
                             "--autopilot", str(autopilot), "--output", str(csv)],
                            cwd=SAILSIM, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
