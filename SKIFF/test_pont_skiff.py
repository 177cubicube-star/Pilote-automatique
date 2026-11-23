"""Tests du pont contre un FAUX serveur Skiff (http.server local).
Le faux serveur reproduit seulement les règles lues dans main.rs : {} libère le
cap, /control remplace la structure, l'état publie rudder_deg, awa_deg, etc."""
import csv
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from pont_skiff import (Pont, PilotageRefuse, SkiffClient, deg_to_helm, helm_to_deg,
                        prendre_la_barre, COLONNES, MaintienApresArrivee)
from verin_sequence import VerinConfig, step_verin


def etat_initial():
    return {"elapsed_s": 0.0, "rudder_deg": 0.0, "awa_deg": -40.0, "heading_true_deg": 293.7,
            "ap_heading_deg": 293.7, "route_guidance": None,
            "control": {"helm": 0.0, "sail_trim": 0.76, "reef": 0.2, "thrust_port": 500.0,
                        "thrust_stbd": 500.0, "mass_scale": 1.1, "traveler": 0.3,
                        "fuel_burn_max_lph": 9.0}}


class FauxSkiff:
    def __init__(self):
        self.state = etat_initial()
        self.posts = []
        faux = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, obj):
                b = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                self._send(faux.state)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["content-length"])) or b"{}")
                faux.posts.append((self.path, body))
                if self.path == "/v1/sim/course" and body == {}:
                    faux.state["ap_heading_deg"] = None
                elif self.path == "/v1/sim/control":
                    faux.state["control"] = body
                    faux.state["rudder_deg"] = body["helm"] * 35.0   # sans retard, suffit ici
                self._send(faux.state)

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class FausseHorloge:
    def __init__(self, pas):
        self.t, self.pas = 100.0, list(pas)

    def __call__(self):
        return self.t

    def avance(self):
        self.t += self.pas.pop(0)


class TestConversion(unittest.TestCase):
    def test_position_atteinte_vers_helm(self):
        self.assertAlmostEqual(deg_to_helm(6.0), 6 / 35)         # +0,171
        self.assertAlmostEqual(deg_to_helm(6.0, signe=-1), -6 / 35)
        self.assertEqual(deg_to_helm(50.0), 1.0)
        self.assertAlmostEqual(helm_to_deg(deg_to_helm(12.0) * 35), 12.0)

    def test_entrees_invalides(self):
        with self.assertRaises(ValueError):
            deg_to_helm(1.0, signe=2)
        with self.assertRaises(ValueError):
            deg_to_helm(float("nan"))


class TestAwaJournal(unittest.TestCase):
    def test_colonne_convertie(self):
        self.assertIn("awa_vient_de_deg", COLONNES)
        self.assertIn("awa_deg", COLONNES)          # le brut reste journalisé


class TestPont(unittest.TestCase):
    def setUp(self):
        self.faux = FauxSkiff()
        self.client = SkiffClient(self.faux.url)

    def tearDown(self):
        self.faux.close()

    def test_prendre_la_barre_envoie_corps_vide(self):
        st = prendre_la_barre(self.client)
        self.assertEqual(self.faux.posts[0], ("/v1/sim/course", {}))
        self.assertIsNone(st["ap_heading_deg"])

    def test_route_active_refusee(self):
        self.faux.state["route_guidance"] = {"bearing_true_deg": 10.0}
        with self.assertRaises(PilotageRefuse):
            prendre_la_barre(self.client)

    def test_garde_control_et_envoie_position_pas_consigne(self):
        h = FausseHorloge([0.05])
        pont = Pont(self.client, VerinConfig(), lambda t, s, p: 20.0, clock=h)
        pont.demarrer()
        h.avance()
        row = pont.tick()
        envoye = self.faux.posts[-1][1]
        for k in ("sail_trim", "reef", "thrust_port", "thrust_stbd", "mass_scale", "traveler"):
            self.assertEqual(envoye[k], etat_initial()["control"][k])
        self.assertEqual(row["cmd_deg"], 20.0)
        self.assertLess(row["pos_deg"], 20.0)                    # le vérin n'y est pas encore
        self.assertAlmostEqual(envoye["helm"], row["pos_deg"] / 35)

    def test_dt_reel_et_intervalle_de_l_ancienne_consigne(self):
        h = FausseHorloge([0.08, 0.08])
        consignes = iter([0.0, 30.0, 30.0])                      # démarrage, puis ticks
        pont = Pont(self.client, VerinConfig(), lambda t, s, p: next(consignes), clock=h)
        pont.demarrer()
        h.avance()
        r1 = pont.tick()                                         # intervalle sous consigne 0°
        self.assertAlmostEqual(r1["pos_deg"], 0.0)
        h.avance()
        r2 = pont.tick()                                         # intervalle sous consigne 30°
        self.assertAlmostEqual(r2["dt_s"], 0.08)
        self.assertAlmostEqual(r2["pos_deg"], 0.64)              # 8 °/s x 80 ms

    def test_barre_ecrasee_par_un_tiers_detectee(self):
        h = FausseHorloge([0.05, 0.05])
        pont = Pont(self.client, VerinConfig(), lambda t, s, p: 20.0, clock=h)
        pont.demarrer()
        h.avance()
        pont.tick()
        self.faux.state["control"]["helm"] = 0.0                 # le cockpit réécrit la barre
        h.avance()
        self.assertEqual(pont.tick()["barre_ecrasee"], 1)

    def test_arret_si_cap_interne_reengage(self):
        h = FausseHorloge([0.05])
        pont = Pont(self.client, VerinConfig(), lambda t, s, p: 20.0, clock=h)
        pont.demarrer()
        self.faux.state["ap_heading_deg"] = 200.0
        h.avance()
        with self.assertRaises(PilotageRefuse):
            pont.tick()

    def test_run_et_csv(self):
        pas = [0.0] + [0.05] * 400
        h = FausseHorloge(pas)
        pont = Pont(self.client, VerinConfig(), lambda t, s, p: 20.0 if t < 0.5 else 0.0,
                    clock=h, sleep=lambda d: h.avance())
        rows = pont.run(1.0)
        self.assertGreaterEqual(len(rows), 19)
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "essai.csv")
            pont.ecrire_csv(chemin)
            with open(chemin, encoding="utf-8") as f:
                lignes = list(csv.DictReader(f))
        self.assertEqual(list(lignes[0].keys()), COLONNES)
        self.assertEqual(len(lignes), len(rows))


class HorlogeQuiAvance:
    """Chaque lecture avance de 1 ms : rend visibles les instants distincts."""
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        self.t += 0.001
        return self.t


class TestHorodatageEtDecision(unittest.TestCase):
    def setUp(self):
        self.faux = FauxSkiff()
        self.client = SkiffClient(self.faux.url)

    def tearDown(self):
        self.faux.close()

    def test_deux_instants_distincts_et_decision_sur_la_meme_ligne(self):
        vus = []
        def consigne(t, state, pos):
            vus.append(t)
            return 20.0 if len(vus) < 3 else 0.0      # décide le retour au 2e tick
        pont = Pont(self.client, VerinConfig(), consigne, clock=HorlogeQuiAvance())
        pont.demarrer()
        r1, r2, r3 = pont.tick(), pont.tick(), pont.tick()
        self.assertGreater(r1["t_reponse_s"], r1["t_pi_s"])
        self.assertAlmostEqual(vus[1], r1["t_reponse_s"])  # décision prise à t_reponse_s
        self.assertEqual(r2["cmd_deg"], 20.0)
        self.assertEqual(r2["cmd_suivante_deg"], 0.0)      # « le Pi commande maintenant le retour »
        self.assertEqual(r3["cmd_deg"], 0.0)               # visible comme consigne active ensuite


class TestMaintienApresArrivee(unittest.TestCase):
    def _jouer(self, prog, duree=12.0, dt=0.05):
        cfg, pos, t = VerinConfig(), 0.0, 0.0
        cmd = prog(0.0, {}, pos)
        while t < duree:
            pos, _ = step_verin(pos, cmd, cfg)
            t += dt
            cmd = prog(t, {}, pos)
        return prog

    def test_chrono_demarre_a_l_arrivee_pas_au_lancement(self):
        p = self._jouer(MaintienApresArrivee(20.0, 4.0, tol_deg=0.2))
        self.assertGreater(p.t_arrivee_s, 2.5)             # 20° à 8 °/s = au moins 2,5 s
        self.assertGreaterEqual(p.t_retour_s - p.t_arrivee_s, 4.0 - 1e-9)
        self.assertGreater(p.t_retour_s, 6.5)              # l'ancienne démo revenait à 4 s

    def test_cible_jamais_atteinte_ne_revient_pas(self):
        p = self._jouer(MaintienApresArrivee(20.0, 4.0), duree=1.0)
        self.assertIsNone(p.t_arrivee_s)
        self.assertIsNone(p.t_retour_s)

    def test_parametres_invalides(self):
        for kw in ({"tenue_s": -1.0}, {"tol_deg": 0.0}, {"cible_deg": float("nan")}):
            args = {"cible_deg": 20.0, "tenue_s": 4.0, **kw}
            with self.assertRaises(ValueError):
                MaintienApresArrivee(**args)


if __name__ == "__main__":
    unittest.main()
