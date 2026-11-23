"""Tests du programme de virement à phases, hors ligne (vérin simulé, bateau fictif)."""
import unittest

from verin_sequence import VerinConfig, step_verin
from virement_phases import (PHASES_ESSAI4, Phase, ProgrammeVirementPhases, mesurer,
                             norm180, vers_signe_skiff)

DT = 0.05


def brut(awa):
    return (awa + 360.0) % 360.0 - 180.0


def jouer(prog, cfg=VerinConfig(max_speed_dps=10.0), duree=40.0, cap0=293.0, taux=0.25):
    """Bateau fictif : vitesse de rotation = -taux x barre (signe Skiff : barre < 0 -> tribord)."""
    pos, cap, t, rows = 0.0, cap0, 0.0, []
    etat = lambda: {"heading_true_deg": cap, "rudder_deg": pos, "awa_deg": brut(norm180(0 - cap) * 0.6),
                    "stw_mps": 3.5}
    cmd = prog(0.0, etat(), pos)
    while t < duree:
        pos, _ = step_verin(pos, cmd, cfg, dt_s=DT)
        cap = (cap - taux * pos * DT) % 360.0
        t += DT
        st = etat()
        rows.append({"t_reponse_s": t, "cmd_deg": cmd, "pos_deg": pos,
                     "heading_true_deg": cap, "awa_vient_de_deg": norm180(brut(norm180(0 - cap) * 0.6) + 180),
                     "stw_mps": 3.5})
        cmd = prog(t, st, pos)
    return rows


def evts(prog, nom):
    return [e for e in prog.journal if e[1].startswith(nom)]


class TestSignes(unittest.TestCase):
    def test_virage_tribord_barre_negative(self):
        self.assertEqual(vers_signe_skiff(20, +1), -20)
        self.assertEqual(vers_signe_skiff(-15, +1), 15)        # contre-barre vers bâbord
        self.assertEqual(vers_signe_skiff(20, -1), 20)
        with self.assertRaises(ValueError):
            vers_signe_skiff(20, 0)

    def test_hfinal_selon_sens(self):
        p = ProgrammeVirementPhases(PHASES_ESSAI4, angle_virement_deg=80, sens_virage=1)
        p(0.0, {"heading_true_deg": 293.0, "rudder_deg": 0.0, "awa_deg": -139.0}, 0.0)
        self.assertAlmostEqual(p.Hfinal, 13.0)


class TestPhases(unittest.TestCase):
    def test_ordre_des_phases_et_contre_barre(self):
        p = ProgrammeVirementPhases(PHASES_ESSAI4)
        rows = jouer(p)
        self.assertEqual([e[2]["phase"] for e in evts(p, "ATTEINT")], [1, 2, 3, 4, 5])
        self.assertTrue(evts(p, "FIN SÉQUENCE"))
        # +15 Skiff d'abord (rampe à 10 °/s : atteint en 1,5 s)
        self.assertGreater(max(r["cmd_deg"] for r in rows[:40]), 14.0)

    def test_maintien_compte_depuis_l_arrivee(self):
        p = ProgrammeVirementPhases(PHASES_ESSAI4)
        jouer(p)
        t_att = next(e[0] for e in evts(p, "ATTEINT") if e[2]["phase"] == 3)
        t_fin = next(e[0] for e in evts(p, "FIN PHASE") if e[2]["phase"] == 3)
        self.assertGreaterEqual(t_fin - t_att, 8.0 - 1e-6)

    def test_rampe_a_la_vitesse_de_la_phase(self):
        p = ProgrammeVirementPhases((Phase(20, 5, 0.0),))
        rows = jouer(p, duree=2.0)
        v = max(abs(b["cmd_deg"] - a["cmd_deg"]) / DT for a, b in zip(rows, rows[1:]))
        self.assertLessEqual(v, 5.0 + 1e-6)

    def test_non_atteint_apres_5_s_puis_maintien(self):
        p = ProgrammeVirementPhases((Phase(25, 10, 1.0), Phase(0, 10, 0.0)))
        jouer(p, cfg=VerinConfig(max_speed_dps=1.0), duree=12.0)  # vérin trop lent
        na = evts(p, "NON ATTEINT")
        self.assertTrue(na)
        self.assertAlmostEqual(na[0][0], 5.05, delta=0.06)

    def test_duree_max_declenche_le_secours(self):
        p = ProgrammeVirementPhases((Phase(20, 10, 40.0),), duree_max_s=10.0)
        jouer(p, duree=15.0)
        self.assertTrue(evts(p, "ARRÊT"))
        self.assertEqual(p.etat, "reprise")


class TestReprise(unittest.TestCase):
    def test_loi_de_cap_de_skiff(self):
        p = ProgrammeVirementPhases((Phase(0, 10, 0.0),))
        st = {"heading_true_deg": 3.0, "rudder_deg": 0.0, "awa_deg": 0.0}
        p(0.0, st, 0.0)
        cmd = p(0.1, st, 0.0)                                   # séquence finie -> reprise
        self.assertEqual(p.etat, "reprise")
        self.assertAlmostEqual(cmd, -2.1 * norm180(p.Hfinal - 3.0))  # 10° à faire -> -21°


class TestMesures(unittest.TestCase):
    def test_virement_fictif_reussi_et_mesures(self):
        p = ProgrammeVirementPhases(PHASES_ESSAI4)
        m = mesurer(jouer(p, duree=60.0), p)
        self.assertIsNotNone(m["lit_du_vent_s_apres_TACK"])
        self.assertIsNotNone(m["alignement_Hfinal_s_apres_TACK"])
        self.assertTrue(m["REUSSI"])

    def test_sans_tack(self):
        self.assertEqual(mesurer([], ProgrammeVirementPhases(PHASES_ESSAI4))["verdict"], "pas de TACK")

    def test_parametres_invalides(self):
        for kw in ({"phases": ()}, {"phases": PHASES_ESSAI4, "sens_virage": 0},
                   {"phases": PHASES_ESSAI4, "duree_max_s": 0}):
            with self.assertRaises(ValueError):
                ProgrammeVirementPhases(**kw)
        with self.assertRaises(ValueError):
            Phase(10, 0, 1)


if __name__ == "__main__":
    unittest.main()
