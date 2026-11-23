"""Tests de preparer_essai contre un FAUX Skiff qui joue une suite d'états scriptée."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from pont_skiff import SkiffClient
from preparer_essai import (BABORD, TRIBORD, DetecteurPassageVent, EssaiConfig, angle_symetrique,
                            EssaiImpossible, SuiviRotation, preparer, _requete_environnement)


def brut(awa_vient_de):
    """Ce que Skiff publie réellement : convention « va vers », décalée de 180°."""
    return (awa_vient_de + 360.0) % 360.0 - 180.0


def etat(t, heading=293.7, awa=40.0, stw=3.0, rudder=-2.0, aground=False):
    """awa : angle « vient de » voulu ; l'état contient la valeur brute Skiff."""
    return {"elapsed_s": t, "heading_true_deg": heading, "awa_deg": brut(awa), "stw_mps": stw,
            "rudder_deg": rudder, "aground": aground, "route_guidance": None,
            "ap_heading_deg": None,
            "control": {"helm": 0.0, "sail_trim": 0.5, "reef": 0.0, "thrust_port": 0.0,
                        "thrust_stbd": 0.0, "mass_scale": 1.0, "traveler": 0.0,
                        "fuel_burn_max_lph": 9.0}}


class FauxSkiff:
    def __init__(self, etats):
        self.etats, self.posts = list(etats), []
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
                st = faux.etats.pop(0) if len(faux.etats) > 1 else faux.etats[0]
                self._send(st)

            def do_POST(self):
                n = int(self.headers["content-length"])
                faux.posts.append((self.path, json.loads(self.rfile.read(n) or b"{}")))
                self._send(etat(0.0, awa=0.0, stw=0.0, rudder=0.0))   # comme au reset

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class Horloge:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def dort(self, d):
        self.t += d


def stable(t0, n, dt=0.1, **kw):
    return [etat(t0 + i * dt, **kw) for i in range(n)]


class TestPreparer(unittest.TestCase):
    def _run(self, etats, **cfg):
        faux = FauxSkiff(etats)
        self.addCleanup(faux.close)
        h = Horloge()
        c = EssaiConfig(**cfg)
        return faux, (lambda: preparer(SkiffClient(faux.url), c, clock=h, sleep=h.dort))

    def test_requetes_dans_l_ordre_et_vent_converti(self):
        faux, go = self._run([etat(0.0, awa=0.0, stw=0.0)] + stable(1.0, 40),
                             lat_deg=12.0, lon_deg=-61.9)
        go()
        chemins = [p for p, _ in faux.posts]
        self.assertEqual(chemins, ["/v1/sim/reset", "/v1/sim/position", "/v1/sim/environment",
                                   "/v1/sim/course", "/v1/sim/control"])
        self.assertEqual(faux.posts[0][1], {"heading_true_deg": 293.7})
        env = faux.posts[2][1]
        self.assertEqual(env["wind_to_deg"], 180.0)          # vent DU 000° -> VERS 180°
        self.assertIs(env["manual"], True)
        self.assertEqual(faux.posts[3][1], {"heading_true_deg": 293.7, "track_hold": False})
        ctrl = faux.posts[4][1]
        self.assertEqual((ctrl["sail_trim"], ctrl["thrust_port"]), (0.76, 0.0))
        self.assertEqual(ctrl["mass_scale"], 1.0)            # champ non géré : conservé

    def test_zero_du_reset_ne_declenche_pas_et_cap_final_tribord(self):
        etats = [etat(0.0, awa=0.0, stw=0.0)] * 3 + stable(1.0, 40, heading=294.0)
        _, go = self._run(etats)
        d = go()
        self.assertGreaterEqual(d.skiff_elapsed_s - 1.0, 3.0 - 1e-9)   # 3 s de stabilité
        self.assertAlmostEqual(d.cap_final_deg, 14.0)        # (294 + 80) % 360
        self.assertAlmostEqual(d.awa_deg, 40.0)

    def test_stw_qui_accelere_retarde_le_declenchement(self):
        accel = [etat(1.0 + i * 0.1, stw=1.5 + 0.05 * i) for i in range(30)]   # +0,5 m/s/s
        _, go = self._run(accel + stable(4.0, 40, stw=3.0))
        # Sans le critère de vitesse, il déclencherait à 4,0 s (1,0 + 3 s).
        # La fenêtre peut commencer dans la fin de l'accélération (2,95 m/s est
        # à moins de 0,1 m/s de 3,0) : on vérifie seulement qu'elle n'a pas
        # couvert l'accélération.
        self.assertGreater(go().skiff_elapsed_s, 6.5)

    def test_awa_hors_tolerance_delai_depasse(self):
        _, go = self._run(stable(0.0, 5, awa=48.0), delai_max_s=5.0)
        with self.assertRaisesRegex(EssaiImpossible, "awa 48.0"):
            go()

    def test_mauvaise_amure_ne_declenche_pas(self):
        _, go = self._run(stable(0.0, 5, awa=-40.0), delai_max_s=2.0)
        with self.assertRaises(EssaiImpossible):
            go()

    def test_echouage_arrete(self):
        _, go = self._run([etat(0.0, aground=True)])
        with self.assertRaisesRegex(EssaiImpossible, "échoué"):
            go()


class TestConventionAwa(unittest.TestCase):
    def test_valeurs_mesurees_sur_skiff(self):
        from pont_skiff import awa_vient_de
        self.assertAlmostEqual(awa_vient_de({"awa_deg": -139.5}), 40.5)    # tribord
        self.assertAlmostEqual(awa_vient_de({"awa_deg": 146.9}), -33.1)    # bâbord
        self.assertAlmostEqual(abs(awa_vient_de({"awa_deg": 0.0})), 180.0) # brut 0 = vent arrière

    def test_brut_zero_du_reset_n_arme_pas(self):
        from pont_skiff import awa_vient_de
        d = DetecteurPassageVent()
        for i in range(10):
            self.assertFalse(d.maj(i * 0.1, awa_vient_de({"awa_deg": 0.0})))
        self.assertFalse(d.arme)


class TestRotation(unittest.TestCase):
    def test_passage_359_vers_0(self):
        r = SuiviRotation()
        r.maj(359.0, 10.0)
        self.assertAlmostEqual(r.maj(1.0, 11.0), 2.0)        # +2 °/s vers tribord

    def test_meme_instant_skiff_ignore(self):
        r = SuiviRotation()
        r.maj(10.0, 5.0)
        self.assertIsNone(r.maj(12.0, 5.0))


class TestDetecteur(unittest.TestCase):
    def _jouer(self, d, awas):
        return [d.maj(i * 0.1, a) for i, a in enumerate(awas)]

    def test_zero_d_initialisation_ignore(self):
        d = DetecteurPassageVent()
        self.assertFalse(any(self._jouer(d, [0.0, 0.0, -1.0, 1.0])))
        self.assertFalse(d.arme)

    def test_passage_detecte_une_seule_fois(self):
        d = DetecteurPassageVent()
        res = self._jouer(d, [40.0] * 5 + [30.0, 12.0, 2.0, -3.0, -10.0, -40.0])
        self.assertEqual(res.count(True), 1)
        self.assertAlmostEqual(d.t_passage_s, 0.8)            # première valeur négative

    def test_empannage_pres_de_180_ignore(self):
        d = DetecteurPassageVent()
        self.assertFalse(any(self._jouer(d, [40.0] * 5 + [120.0, 179.0, -179.0, -150.0])))

    def test_symetrie_babord(self):
        d = DetecteurPassageVent(sens_depart=BABORD)
        self.assertTrue(any(self._jouer(d, [-40.0] * 5 + [-5.0, 4.0])))

    def test_armement_interrompu_repart_de_zero(self):
        d = DetecteurPassageVent(n_armement=3)
        self._jouer(d, [40.0, 40.0, 10.0, 40.0, 40.0])
        self.assertFalse(d.arme)


class TestConfig(unittest.TestCase):
    def test_invalides(self):
        for kw in ({"sens_depart": 0}, {"lat_deg": 12.0}, {"angle_virement_deg": 200.0},
                   {"vent_mps": float("nan")}, {"duree_stable_s": 0.0}):
            with self.assertRaises(ValueError):
                EssaiConfig(**kw)

    def test_angle_symetrique(self):
        self.assertAlmostEqual(angle_symetrique(293.1, EssaiConfig()), 133.8)       # -> 066,9°
        self.assertAlmostEqual(angle_symetrique(66.9, EssaiConfig(sens_depart=BABORD)), 133.8)
        with self.assertRaises(ValueError):
            angle_symetrique(66.9, EssaiConfig())                                    # mauvaise amure

    def test_cap_final_selon_amure(self):
        self.assertEqual(EssaiConfig().cap_final_signe, 80.0)
        self.assertEqual(EssaiConfig(sens_depart=BABORD).cap_final_signe, -80.0)

    def test_vent_converti(self):
        self.assertEqual(_requete_environnement(EssaiConfig(vent_vient_de_deg=330.0))["wind_to_deg"],
                         150.0)                                # valeur du reset Skiff


if __name__ == "__main__":
    unittest.main()
