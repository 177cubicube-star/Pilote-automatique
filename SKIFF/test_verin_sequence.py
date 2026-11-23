import math
import unittest
from verin_sequence import (Step, VerinConfig, build_profile, simulate, step_verin,
                            run_closed_loop, max_tracking_error)

CFG = VerinConfig()  # ±35°, 8 °/s, tau 0.1 s, dt 0.05 s
NAN = float("nan")


class TestProfile(unittest.TestCase):
    def test_vitesse_donne_bonne_duree(self):
        self.assertAlmostEqual(build_profile([Step(10, speed_dps=5.0)], CFG).duration_s, 2.0)

    def test_duree_donne_bonne_vitesse(self):
        p = build_profile([Step(12, duration_s=3.0)], CFG)
        self.assertAlmostEqual(p.duration_s, 3.0)
        self.assertAlmostEqual(p.at(1.5), 6.0)

    def test_hold_garde_langle(self):
        p = build_profile([Step(10, speed_dps=5.0, hold_s=2.0)], CFG)
        self.assertAlmostEqual(p.duration_s, 4.0)
        self.assertAlmostEqual(p.at(3.0), 10.0)

    def test_sequence_multi_rythmes(self):
        p = build_profile([Step(10, duration_s=2.0), Step(-10, speed_dps=4.0, hold_s=1.0),
                           Step(0)], CFG)
        self.assertAlmostEqual(p.duration_s, 9.25)       # 2 + 5 + 1 + 1.25
        self.assertAlmostEqual(p.at(2.0), 10.0)
        self.assertAlmostEqual(p.at(7.0), -10.0)
        self.assertFalse(p.warnings)

    def test_vitesse_trop_elevee_avertit_et_limite(self):
        p = build_profile([Step(16, duration_s=1.0)], CFG)
        self.assertEqual(len(p.warnings), 1)
        self.assertAlmostEqual(p.duration_s, 2.0)

    def test_demande_et_consigne_limitee_distinctes(self):
        p = build_profile([Step(16, duration_s=1.0)], CFG)   # 16 °/s demandé, 8 permis
        self.assertAlmostEqual(p.requested_at(1.0), 16.0)    # le Pi a demandé 16° en 1 s
        self.assertAlmostEqual(p.at(1.0), 8.0)               # la consigne n'a fait que 8°
        s = simulate(p, CFG)[20]                             # t = 1.0 s
        self.assertAlmostEqual(s.req_deg, 16.0)
        self.assertAlmostEqual(s.cmd_deg, 8.0)
        self.assertLess(s.pos_deg, 8.0)

    def test_angle_hors_butee_avertit(self):
        p = build_profile([Step(50, speed_dps=5.0)], CFG)
        self.assertEqual(len(p.warnings), 1)
        self.assertAlmostEqual(p.at(p.duration_s), 35.0)
        self.assertAlmostEqual(p.requested_at(p.duration_s), 50.0)   # la demande reste visible

    def test_depart_hors_butees_avertit(self):
        p = build_profile([Step(0)], CFG, start_deg=80)
        self.assertEqual(p.points[0][1], 35.0)
        self.assertTrue(any("départ" in w for w in p.warnings))

    def test_entrees_invalides_et_nan(self):
        bad = [lambda: Step(10, speed_dps=5.0, duration_s=2.0), lambda: Step(10, speed_dps=-1),
               lambda: Step(NAN), lambda: Step(1, speed_dps=NAN), lambda: Step(1, duration_s=NAN),
               lambda: Step(1, hold_s=NAN), lambda: Step(1, hold_s=math.inf),
               lambda: VerinConfig(tau_s=NAN), lambda: VerinConfig(angle_min_deg=10, angle_max_deg=-10),
               lambda: build_profile([], CFG), lambda: build_profile([Step(1)], CFG, start_deg=NAN)]
        for f in bad:
            with self.assertRaises(ValueError):
                f()


class TestSimulation(unittest.TestCase):
    def test_depart_par_defaut_suit_le_profil(self):
        p = build_profile([Step(0, duration_s=2.0)], CFG, start_deg=-20)
        s0 = simulate(p, CFG)[0]
        self.assertEqual(s0.pos_deg, -20.0)
        self.assertEqual(s0.cmd_deg - s0.pos_deg, 0.0)       # plus d'erreur artificielle

    def test_decalage_volontaire_possible(self):
        p = build_profile([Step(0, duration_s=2.0)], CFG, start_deg=-20)
        s0 = simulate(p, CFG, start_deg=0.0)[0]
        self.assertEqual(s0.cmd_deg - s0.pos_deg, -20.0)

    def test_parametres_invalides(self):
        p = build_profile([Step(5)], CFG)
        for kw in ({"settle_s": -1}, {"settle_s": NAN}, {"start_deg": 99}, {"start_deg": NAN}):
            with self.assertRaises(ValueError):
                simulate(p, CFG, **kw)

    def test_ne_depasse_jamais_la_vitesse_max_ni_les_butees(self):
        p = build_profile([Step(35), Step(-35)], CFG)
        for s in simulate(p, CFG):
            self.assertLessEqual(abs(s.speed_dps), CFG.max_speed_dps + 1e-9)
            self.assertTrue(CFG.angle_min_deg <= s.pos_deg <= CFG.angle_max_deg)

    def test_converge_vers_la_cible_finale(self):
        p = build_profile([Step(20, duration_s=5.0, hold_s=2.0)], CFG)
        self.assertAlmostEqual(simulate(p, CFG)[-1].pos_deg, 20.0, places=2)

    def test_suivi_bon_si_rampe_lente(self):
        p = build_profile([Step(20, speed_dps=2.0)], CFG)
        self.assertLess(max_tracking_error(simulate(p, CFG)), 0.5)


class TestStepVerin(unittest.TestCase):
    def test_un_pas_limite_par_la_vitesse(self):
        pos, speed = step_verin(0.0, 30.0, CFG)
        self.assertAlmostEqual(pos, CFG.max_speed_dps * CFG.dt_s)
        self.assertAlmostEqual(speed, CFG.max_speed_dps)

    def test_un_pas_ne_depasse_pas_la_butee(self):
        pos, _ = step_verin(34.9, 90.0, CFG)
        self.assertLessEqual(pos, CFG.angle_max_deg)

    def test_simulate_equivaut_a_appeler_step_verin_en_boucle(self):
        p = build_profile([Step(10, duration_s=2.0, hold_s=1.0), Step(-5)], CFG)
        pos, ref = p.points[0][1], simulate(p, CFG)
        for s in ref[1:]:
            pos, _ = step_verin(pos, s.cmd_deg, CFG)
            self.assertAlmostEqual(pos, s.pos_deg)


    def test_dt_reel_change_la_course_permise(self):
        pos50, _ = step_verin(0.0, 30.0, CFG)              # 50 ms
        pos80, _ = step_verin(0.0, 30.0, CFG, dt_s=0.08)   # 80 ms
        self.assertAlmostEqual(pos50, 0.40)
        self.assertAlmostEqual(pos80, 0.64)

    def test_dt_invalide(self):
        for dt in (0.0, -0.05, NAN):
            with self.assertRaises(ValueError):
                step_verin(0.0, 10.0, CFG, dt_s=dt)


class TestClosedLoop(unittest.TestCase):
    def test_maintien_demarre_quand_la_position_arrive(self):
        r = run_closed_loop([Step(10, duration_s=2.0, hold_s=1.0), Step(0)], CFG, tol_deg=0.2)
        t_in = next(s.t for s in r.samples if abs(s.pos_deg - 10) <= 0.2)
        t_leave = next(s.t for s in r.samples if s.t > t_in and s.cmd_deg < 10 - 1e-9)
        self.assertGreater(t_in, 2.0)                        # après la consigne (2,0 s)
        self.assertGreaterEqual(t_leave - t_in, 1.0 - 1e-6)  # 1 s pleine depuis la position
        self.assertFalse(r.warnings)

    def test_chronometre_plus_long_que_le_profil_chronometre(self):
        step = [Step(10, duration_s=2.0, hold_s=1.0), Step(0)]
        p = build_profile(step, CFG)
        open_loop_leave = 3.0                                # consigne atteint 10° à 2,0 s + 1 s
        r = run_closed_loop(step, CFG)
        t_leave = next(s.t for s in r.samples if s.t > 2.0 and s.cmd_deg < 10 - 1e-9)
        self.assertGreater(t_leave, open_loop_leave)
        self.assertEqual(p.at(3.0), 10.0)

    def test_etape_non_atteinte_avertit_et_saute_le_maintien(self):
        r = run_closed_loop([Step(10, duration_s=2.0, hold_s=5.0)], CFG,
                            tol_deg=1e-9, step_timeout_s=0.5, settle_s=0.0)
        self.assertTrue(any("non atteint" in w for w in r.warnings))
        self.assertLess(r.samples[-1].t, 5.0)                # pas de maintien de 5 s

    def test_garde_demande_consigne_position_cote_a_cote(self):
        r = run_closed_loop([Step(16, duration_s=1.0, hold_s=0.5)], CFG)
        self.assertTrue(any("vitesse demandée" in w for w in r.warnings))
        mid = next(s for s in r.samples if abs(s.t - 1.0) < 1e-9)
        self.assertAlmostEqual(mid.req_deg, 16.0)
        self.assertAlmostEqual(mid.cmd_deg, 8.0)
        self.assertLess(mid.pos_deg, mid.cmd_deg)

    def test_respecte_butees_et_vitesse(self):
        r = run_closed_loop([Step(50), Step(-50)], CFG)
        for s in r.samples:
            self.assertTrue(CFG.angle_min_deg <= s.pos_deg <= CFG.angle_max_deg)
            self.assertLessEqual(abs(s.speed_dps), CFG.max_speed_dps + 1e-9)

    def test_parametres_invalides(self):
        for kw in ({"tol_deg": 0}, {"tol_deg": NAN}, {"step_timeout_s": -1}, {"settle_s": -1}):
            with self.assertRaises(ValueError):
                run_closed_loop([Step(1)], CFG, **kw)


if __name__ == "__main__":
    unittest.main()
