"""Tests de simu_9axes_verin. Lancer depuis ce dossier :

    python -m unittest -v test_simu_9axes

Trois niveaux : la puce et le bus (octets), les briques (fusion, bateau,
vérin, régulateurs), puis la boucle complète (essais courts, graine fixe).
"""
import csv
import json
import math
import os
import socket
import struct
import tempfile
import unittest
from dataclasses import replace

import banc
from bateau_sim import Bateau, ConfigBateau, ConfigPerturbations
from capteur_gite_sim import InclinometreSim, reference_parfaite
from fusion_cap import (FusionCap, FusionMahony, ReferenceGite, _euler_q, _q_euler,
                        cap_compense, construire_fusion, enrouler_180, inclinaison_par_accel)
from icm20948_lecteur import ErreurCapteur, LecteurICM20948, MesureIMU
import bateau_sim
from icm20948_sim import (
    ADRESSE_AK09916, ADRESSE_ICM_DEFAUT, AK_ST1, AK_ST2, ConfigBruit, FauxBusI2C,
    G, PuceICM20948, REG_ACCEL_XOUT_H, REG_BANK_SEL, REG_PWR_MGMT_1, REG_WHO_AM_I,
)
from regulateurs import (EntreeRegulateur, RegulateurPIDPosition, RegulateurPypilotBasic,
                         construire_regulateur)
from verin_moteur_sim import ConfigVerin, Verin

SANS_BRUIT = ConfigBruit(gyro_bruit_dps=0.0, gyro_biais_dps=(0, 0, 0),
                         gyro_derive_dps_par_rac_s=0.0, accel_bruit_g=0.0,
                         accel_biais_g=(0, 0, 0), mag_bruit_ut=0.0)
ICI = os.path.dirname(os.path.abspath(__file__))


def lecteur_pret(bruit=SANS_BRUIT, **kw):
    puce = PuceICM20948(bruit)
    bus = FauxBusI2C(puce)
    lecteur = LecteurICM20948(bus, attente=lambda s: None, **kw)
    lecteur.demarrer()
    return puce, bus, lecteur


class TestPuceEtBus(unittest.TestCase):
    def test_who_am_i(self):
        bus = FauxBusI2C(PuceICM20948())
        self.assertEqual(bus.read_byte_data(ADRESSE_ICM_DEFAUT, REG_WHO_AM_I), 0xEA)

    def test_mauvaise_adresse_comme_smbus2(self):
        bus = FauxBusI2C(PuceICM20948())
        with self.assertRaises(OSError):
            bus.read_byte_data(0x68, REG_WHO_AM_I)

    def test_magnetometre_invisible_sans_bypass(self):
        bus = FauxBusI2C(PuceICM20948())
        with self.assertRaises(OSError):
            bus.read_byte_data(ADRESSE_AK09916, 0x01)

    def test_donnees_nulles_tant_que_la_puce_dort(self):
        puce = PuceICM20948(SANS_BRUIT)
        bus = FauxBusI2C(puce)
        puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (19, 0, 49), 20, 0.01)
        self.assertEqual(bus.read_i2c_block_data(ADRESSE_ICM_DEFAUT, REG_ACCEL_XOUT_H, 6), [0] * 6)

    def test_selection_de_banque(self):
        bus = FauxBusI2C(PuceICM20948())
        bus.write_byte_data(ADRESSE_ICM_DEFAUT, REG_BANK_SEL, 2 << 4)
        self.assertEqual(bus.read_byte_data(ADRESSE_ICM_DEFAUT, REG_BANK_SEL), 0x20)
        self.assertNotEqual(bus.read_byte_data(ADRESSE_ICM_DEFAUT, REG_WHO_AM_I), 0xEA)

    def test_repos_donne_plus_un_g_sur_z_puce(self):
        puce, bus, _ = lecteur_pret()
        puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (19, 0, 49), 20, 0.01)
        octets = bus.read_i2c_block_data(ADRESSE_ICM_DEFAUT, REG_ACCEL_XOUT_H, 6)
        ax, ay, az = struct.unpack(">3h", bytes(octets))
        self.assertEqual((ax, ay), (0, 0))
        self.assertEqual(az, 16384)                       # ±2 g : 16384 LSB/g

    def test_saturation_16_bits(self):
        puce, bus, _ = lecteur_pret()
        puce.mettre_a_jour((0, 0, -G), (0, 0, 400.0), (19, 0, 49), 20, 0.01)   # > 250 °/s
        octets = bus.read_i2c_block_data(ADRESSE_ICM_DEFAUT, 0x37, 2)
        self.assertEqual(struct.unpack(">h", bytes(octets))[0], -32768)       # z puce = -z corps

    def test_st2_libere_la_mesure_et_dor_signale_l_oubli(self):
        puce, bus, _ = lecteur_pret()
        for _ in range(2):                                 # deux mesures sans lecture
            puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (19, 0, 49), 20, 0.01)
        self.assertEqual(bus.read_byte_data(ADRESSE_AK09916, AK_ST1), 0x03)   # DRDY + DOR
        bus.read_byte_data(ADRESSE_AK09916, AK_ST2)
        self.assertEqual(bus.read_byte_data(ADRESSE_AK09916, AK_ST1), 0x00)

    def test_reinitialisation_remet_en_sommeil(self):
        puce, bus, _ = lecteur_pret()
        self.assertFalse(puce.dort)
        bus.write_byte_data(ADRESSE_ICM_DEFAUT, REG_PWR_MGMT_1, 0x80)
        self.assertTrue(puce.dort)

    def test_octet_hors_limites_refuse(self):
        bus = FauxBusI2C(PuceICM20948())
        with self.assertRaises(ValueError):
            bus.write_byte_data(ADRESSE_ICM_DEFAUT, REG_PWR_MGMT_1, 256)


class TestLecteur(unittest.TestCase):
    def test_demarrage_reveille_et_ouvre_le_magnetometre(self):
        puce, _, lecteur = lecteur_pret()
        self.assertTrue(lecteur.demarre)
        self.assertFalse(puce.dort)
        self.assertTrue(puce.magnetometre_accessible)

    def test_mauvaise_puce_refusee(self):
        puce = PuceICM20948()
        puce.regs[0][REG_WHO_AM_I] = 0x71                  # une MPU-9250, par exemple
        puce.ecrire_icm = lambda reg, val: None            # et elle ignore la réinitialisation
        with self.assertRaises(ErreurCapteur):
            LecteurICM20948(FauxBusI2C(puce), attente=lambda s: None).demarrer()

    def test_aller_retour_unites_et_repere_corps(self):
        puce, _, lecteur = lecteur_pret()
        acc, gyr, mag = (1.0, -2.0, -9.0), (3.0, -4.0, 5.0), (19.0, -3.0, 49.0)
        puce.mettre_a_jour(acc, gyr, mag, 25.0, 0.01)
        m = lecteur.lire(0.0)
        for attendu, lu, tol in ((acc, m.accel_ms2, 0.002), (gyr, m.gyro_dps, 0.01),
                                 (mag, m.mag_ut, 0.08)):
            for a, b in zip(attendu, lu):
                self.assertAlmostEqual(a, b, delta=tol)
        self.assertAlmostEqual(m.temp_c, 25.0, delta=0.01)

    def test_pas_de_nouvelle_mesure_mag_si_deja_lue(self):
        puce, _, lecteur = lecteur_pret()
        puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (19, 0, 49), 20, 0.01)
        self.assertIsNotNone(lecteur.lire(0.0).mag_ut)
        self.assertIsNone(lecteur.lire(0.0).mag_ut)

    def test_calibration_fer_dur_retiree(self):
        puce, _, lecteur = lecteur_pret(fer_dur_ut=(5.0, -2.0, 1.0))
        puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (24.0, -2.0, 50.0), 20, 0.01)
        mag = lecteur.lire(0.0).mag_ut
        self.assertAlmostEqual(mag[0], 19.0, delta=0.1)
        self.assertAlmostEqual(mag[1], 0.0, delta=0.1)

    def test_erreur_de_bus_reessayee_puis_signalee(self):
        puce, bus, lecteur = lecteur_pret()
        puce.mettre_a_jour((0, 0, -G), (0, 0, 0), (19, 0, 49), 20, 0.01)
        bus.taux_erreur = 1.0
        with self.assertRaises(ErreurCapteur):
            lecteur.lire(0.0)
        self.assertGreaterEqual(lecteur.erreurs_bus, lecteur.essais)

    def test_lire_sans_demarrer_refuse(self):
        with self.assertRaises(ErreurCapteur):
            LecteurICM20948(FauxBusI2C(PuceICM20948())).lire(0.0)


class TestFusion(unittest.TestCase):
    def _mesures(self, gite_deg, tangage_deg, cap_deg):
        b = Bateau(ConfigBateau())
        b.gite, b.tangage, b.cap = gite_deg, tangage_deg, cap_deg
        return b.mesures_physiques()

    def test_inclinaison_et_cap_compense(self):
        for gite, tangage, cap in ((0, 0, 0), (15, 0, 45), (-20, 5, 200), (10, -8, 300)):
            force, _, champ = self._mesures(gite, tangage, cap)
            g, t = inclinaison_par_accel(force)
            self.assertAlmostEqual(math.degrees(g), gite, places=6)
            self.assertAlmostEqual(math.degrees(t), tangage, places=6)
            self.assertAlmostEqual(enrouler_180(math.degrees(cap_compense(champ, g, t)) - cap),
                                   0.0, places=6)

    def test_fusion_retire_le_biais_du_gyroscope(self):
        bruit = replace(SANS_BRUIT, gyro_biais_dps=(0.0, 0.0, -0.5))   # z puce = -z corps
        puce, _, lecteur = lecteur_pret(bruit)
        fusion = FusionCap(ki_biais=0.05)
        force, rot, champ = self._mesures(0, 0, 120)
        est = None
        for i in range(12000):                              # 120 s
            puce.mettre_a_jour(force, rot, champ, 20, 0.01)
            est = fusion.mettre_a_jour(lecteur.lire(i * 0.01), 0.01) or est
        # sans bruit, la quantification du magnétomètre (0,15 µT ≈ 0,45° sur 19 µT
        # horizontaux) laisse un petit écart fixe : d'où la tolérance de 0,3°
        self.assertAlmostEqual(enrouler_180(est.cap_deg - 120), 0.0, delta=0.3)
        self.assertAlmostEqual(est.taux_lacet_dps, 0.0, delta=0.02)

    def test_attend_le_magnetometre(self):
        m = MesureIMU(0.0, (0, 0, -G), (0, 0, 0), None, 20.0)
        self.assertIsNone(FusionCap().mettre_a_jour(m, 0.01))


class TestBateau(unittest.TestCase):
    def test_barre_fixe_donne_k_fois_angle(self):
        b = Bateau(ConfigBateau())
        for _ in range(3000):
            b.pas(5.0, 0.01)
        self.assertAlmostEqual(b.r, 0.19 * 5.0, places=3)   # barre positive : cap qui augmente

    def test_repos_sans_perturbation(self):
        b = Bateau(ConfigBateau(), cap_initial_deg=33)
        for _ in range(1000):
            b.pas(0.0, 0.01)
        self.assertAlmostEqual(b.cap, 33.0, places=9)

    def test_vagues_reproductibles_par_graine(self):
        p = ConfigPerturbations(vagues_lacet_deg=4.0)
        caps = []
        for _ in range(2):
            b = Bateau(ConfigBateau(), p, graine=7)
            for _ in range(500):
                b.pas(0.0, 0.01)
            caps.append(b.cap)
        self.assertEqual(caps[0], caps[1])


class TestVerin(unittest.TestCase):
    CFG = ConfigVerin(bruit_can_lsb=0.0, jeu_mm=0.0, effort_safran_n_par_deg=0.0)

    def test_rampe_puis_vitesse_max(self):
        v = Verin(self.CFG)
        v.pas(1.0, 0.1)
        self.assertAlmostEqual(v.vitesse, 0.5 * 30.0)       # mi-rampe à 0,1 s
        for _ in range(20):
            v.pas(1.0, 0.01)
        self.assertAlmostEqual(v.vitesse, 30.0)

    def test_butee(self):
        v = Verin(self.CFG)
        for _ in range(1200):
            v.pas(1.0, 0.01)
        self.assertEqual(v.x_tige, 300.0)
        self.assertAlmostEqual(v.angle_barre_deg(), 30.0, places=6)
        self.assertGreater(v.temps_en_butee_s, 0.0)

    def test_seuil_de_demarrage(self):
        v = Verin(self.CFG)
        for _ in range(100):
            v.pas(0.03, 0.01)
        self.assertEqual(v.x_tige, 150.0)

    def test_commande_absurde_au_neutre(self):
        v = Verin(self.CFG)
        v.pas(float("nan"), 0.01)
        self.assertEqual(v.commandes_invalides, 1)
        self.assertEqual(v.vitesse, 0.0)

    def test_effort_ralentit_et_surintensite_coupe(self):
        cfg = replace(self.CFG, effort_safran_n_par_deg=60.0)   # barre très dure
        v = Verin(cfg, angle_initial_deg=20.0)
        for _ in range(50):
            v.pas(1.0, 0.01)
        self.assertGreater(v.surintensites, 0)

    def test_jeu_invisible_au_potentiometre(self):
        v = Verin(replace(self.CFG, jeu_mm=4.0))
        for _ in range(100):
            v.pas(1.0, 0.01)
        for _ in range(100):
            v.pas(-1.0, 0.01)
        ecart = abs(v.x_tige - v.x_barre)
        self.assertAlmostEqual(ecart, 2.0, places=6)

    def test_detache(self):
        v = Verin(self.CFG, angle_initial_deg=10.0)
        v.detache = True
        for _ in range(1000):
            v.pas(1.0, 0.01)
        self.assertLess(abs(v.angle_barre_deg()), 0.1)        # la barre revient au centre
        self.assertGreater(v.angle_mesure_deg(), 25.0)        # le potentiomètre ne le voit pas

    def test_inversions_comptees(self):
        v = Verin(self.CFG)
        for sens in (1, -1, 1):
            for _ in range(50):
                v.pas(sens, 0.01)
        self.assertEqual(v.inversions, 2)


class TestRegulateurs(unittest.TestCase):
    def test_pid_signe_et_bande_morte(self):
        r = RegulateurPIDPosition(kp=1.0, ki=0.0, kd=0.0, bande_morte_deg=0.5)
        self.assertGreater(r.calculer(EntreeRegulateur(0, 0, 10, 0), 0.05), 0)   # cap trop bas
        r = RegulateurPIDPosition(kp=1.0, ki=0.0, kd=0.0, bande_morte_deg=0.5)
        self.assertEqual(r.calculer(EntreeRegulateur(0, 0, 0.3, 0), 0.05), 0.0)

    def test_pid_passe_par_zero_degre(self):
        r = RegulateurPIDPosition(kp=1.0, ki=0.0, kd=0.0)
        r.calculer(EntreeRegulateur(355, 0, 5, 0), 0.05)
        self.assertAlmostEqual(r.dernier["erreur"], 10.0)

    def test_terme_d_freine_la_rotation(self):
        r = RegulateurPIDPosition(kp=0.0, ki=0.0, kd=2.0)
        r.calculer(EntreeRegulateur(0, 3.0, 0, 0), 0.05)
        self.assertAlmostEqual(r.dernier["angle_voulu"], -6.0)

    def test_integrale_bornee_et_zone(self):
        r = RegulateurPIDPosition(kp=0.0, ki=1.0, kd=0.0, i_max_deg=4.0)
        for _ in range(1000):
            r.calculer(EntreeRegulateur(0, 0, 3, 0), 0.05)
        self.assertAlmostEqual(r.integrale, 4.0)
        r = RegulateurPIDPosition(kp=0.0, ki=1.0, kd=0.0, zone_integrale_deg=5.0)
        for _ in range(100):
            r.calculer(EntreeRegulateur(0, 0, 20, 0), 0.05)
        self.assertEqual(r.integrale, 0.0)

    def test_angle_voulu_borne(self):
        r = RegulateurPIDPosition(kp=5.0, ki=0.0, kd=0.0, angle_max_deg=25.0)
        r.calculer(EntreeRegulateur(0, 0, 30, 0), 0.05)
        self.assertEqual(r.dernier["angle_voulu"], 25.0)

    def test_pypilot_corrige_dans_le_bon_sens(self):
        r = RegulateurPypilotBasic()
        commandes = [r.calculer(EntreeRegulateur(10, 0, 0, 0), 0.05)   # cap 10° trop haut
                     for _ in range(300)]
        # le mécanisme « période » accumule avant de bouger, puis donne des impulsions
        self.assertLess(min(commandes), 0)                   # barre pour faire baisser le cap
        self.assertLessEqual(max(commandes), 0)              # jamais dans le mauvais sens

    def test_fabrique_refuse_les_fautes_de_frappe(self):
        with self.assertRaises(ValueError):
            construire_regulateur({"type": "pid_position", "kpp": 1.0})
        with self.assertRaises(ValueError):
            construire_regulateur({"type": "pid_vitesse"})
        self.assertIsInstance(construire_regulateur({"type": "pid_position", "_note": "x"}),
                              RegulateurPIDPosition)

    def test_tous_les_prereglages_se_construisent(self):
        with open(os.path.join(ICI, "gains_pid.json"), encoding="utf-8") as f:
            reglages = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
        self.assertGreater(len(reglages), 3)
        for nom, r in reglages.items():
            with self.subTest(nom=nom):
                construire_regulateur(r)


class TestBoucleComplete(unittest.TestCase):
    """Essais courts : ils vérifient que la chaîne tient, pas qu'un réglage est bon."""

    def test_reproductible(self):
        scn = replace(banc.SCENARIOS["vagues"], duree_s=40.0)
        a = banc.executer(scn, {"type": "pid_position"}, graine=3)
        b = banc.executer(scn, {"type": "pid_position"}, graine=3)
        nan_vers_none = lambda d: {k: (None if isinstance(v, float) and math.isnan(v) else v)
                                   for k, v in d.items()}
        self.assertEqual(nan_vers_none(a), nan_vers_none(b))

    def test_tient_le_cap_par_vagues(self):
        scn = replace(banc.SCENARIOS["vagues"], duree_s=90.0)
        r = banc.executer(scn, {"type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 2.0,
                                "zone_integrale_deg": 5.0})
        self.assertLess(r["erreur_p95_deg"], 4.0)
        self.assertLess(r["ecart_estimation_rms_deg"], 2.0)

    def test_changement_de_cap_atteint(self):
        r = banc.executer(banc.SCENARIOS["calme_pas20"],
                          {"type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 2.0,
                           "zone_integrale_deg": 5.0})
        self.assertLess(r["temps_reponse_max_s"], 60.0)
        self.assertLess(r["depassement_max_deg"], 6.0)

    def test_bus_perturbe_ne_casse_pas_la_boucle(self):
        scn = replace(banc.SCENARIOS["i2c_perturbe"], duree_s=40.0, taux_erreur_i2c=0.3)
        r = banc.executer(scn, {"type": "pid_position"})
        self.assertGreater(r["lectures_ratees"], 0)
        self.assertLess(r["erreur_max_deg"], 10.0)

    def test_detache_se_voit_au_cap_pas_au_potentiometre(self):
        scn = replace(banc.SCENARIOS["verin_detache"], duree_s=120.0)
        r = banc.executer(scn, {"type": "pid_position"})
        self.assertGreater(r["erreur_max_deg"], 10.0)

    def test_journal_ecrit(self):
        chemin = os.path.join(tempfile.gettempdir(), "simu_9axes_test_journal.csv")
        try:
            banc.executer(replace(banc.SCENARIOS["vagues"], duree_s=5.0),
                          {"type": "pid_position"}, chemin_journal=chemin)
            with open(chemin, encoding="utf-8") as f:
                lignes = f.read().splitlines()
            self.assertEqual(lignes[0].split(","), list(banc.COLONNES_JOURNAL))
            self.assertGreater(len(lignes), 50)
        finally:
            if os.path.exists(chemin):
                try:
                    os.remove(chemin)
                except OSError:
                    pass


class TestMahonyEtSourcesDeGite(unittest.TestCase):
    def _mesure(self, gite, tangage, cap):
        b = Bateau(ConfigBateau())
        b.gite, b.tangage, b.cap = gite, tangage, cap
        f, w, c = b.mesures_physiques()
        return MesureIMU(0.0, f, w, c, 20.0)

    def test_quaternion_aller_retour(self):
        for e in ((0.2, -0.1, 2.5), (-0.3, 0.15, -1.0)):
            for a, b in zip(_q_euler(_euler_q(*e)), e):
                self.assertAlmostEqual(a, b, places=9)

    def test_mahony_revient_d_une_mauvaise_orientation(self):
        m = self._mesure(15, -5, 200)
        f = FusionMahony()
        f.mettre_a_jour(m, 0.01)
        f.q = _euler_q(0.0, 0.0, math.radians(150))          # 15° et 50° d'erreur
        for _ in range(6000):
            est = f.mettre_a_jour(m, 0.01)
        self.assertAlmostEqual(est.gite_deg, 15.0, delta=0.3)
        self.assertAlmostEqual(est.tangage_deg, -5.0, delta=0.3)
        self.assertAlmostEqual(enrouler_180(est.cap_deg - 200), 0.0, delta=0.5)

    def test_mahony_apprend_le_biais_sur_trois_axes(self):
        bruit = replace(SANS_BRUIT, gyro_biais_dps=(0.4, -0.3, 0.2))
        puce, _, lecteur = lecteur_pret(bruit)
        f = FusionMahony()
        b = Bateau(ConfigBateau())
        b.gite, b.cap = 10, 70
        force, rot, champ = b.mesures_physiques()
        est = None
        for i in range(30000):                                # 300 s au quai
            puce.mettre_a_jour(force, rot, champ, 20, 0.01)
            est = f.mettre_a_jour(lecteur.lire(i * 0.01), 0.01) or est
        biais_corps = [math.degrees(x) for x in f.biais]
        for attendu, appris in zip((0.4, 0.3, -0.2), biais_corps):   # repère corps = (x, -y, -z) puce
            self.assertAlmostEqual(attendu, appris, delta=0.03)
        self.assertAlmostEqual(est.gite_deg, 10.0, delta=0.2)

    def test_reference_exacte_imposee(self):
        f = FusionMahony()
        m = self._mesure(0, 0, 30)
        f.mettre_a_jour(m, 0.01)
        est = f.mettre_a_jour(m, 0.01, ReferenceGite(math.radians(7), math.radians(-2), exacte=True))
        self.assertAlmostEqual(est.gite_deg, 7.0, places=6)
        c = FusionCap()
        c.mettre_a_jour(m, 0.01)
        est = c.mettre_a_jour(m, 0.01, reference_parfaite(7.0, -2.0))
        self.assertAlmostEqual(est.gite_deg, 7.0, places=6)

    def test_inclinometre_voit_la_force_specifique(self):
        incl = InclinometreSim(bruit_g=0.0)
        b = Bateau(ConfigBateau())
        b.gite = 12
        ref = incl.lire(b.mesures_physiques()[0], 0.01)
        self.assertAlmostEqual(math.degrees(ref.gite_rad), 12.0, places=6)
        self.assertFalse(ref.exacte)

    def test_fabrique_de_fusion(self):
        self.assertIsInstance(construire_fusion("mahony", kp_acc=0.3), FusionMahony)
        with self.assertRaises(ValueError):
            construire_fusion("kalman")
        with self.assertRaises(ValueError):
            construire_fusion("mahony", kp=1.0)

    def test_biais_tires_au_hasard_selon_la_graine(self):
        self.assertNotEqual(PuceICM20948(graine=1).biais_gyro, PuceICM20948(graine=2).biais_gyro)
        self.assertEqual(PuceICM20948(graine=1).biais_accel, PuceICM20948(graine=1).biais_accel)

    def test_le_banc_ne_fabrique_pas_d_erreur_de_gite(self):
        """Sans bruit, sans biais, centrale au centre de rotation, sans embardée : les
        deux filtres doivent retrouver la gîte (contrôle de cohérence du banc)."""
        zero = ConfigBruit(gyro_bruit_dps=0, gyro_biais_dps=(0, 0, 0),
                           gyro_derive_dps_par_rac_s=0, accel_bruit_g=0,
                           accel_biais_g=(0, 0, 0), mag_bruit_ut=0)
        v = banc.SCENARIOS["vagues"]
        scn = replace(v, duree_s=60.0,
                      perturbations=replace(v.perturbations, vagues_embardee_ms2=0.0))
        cfg = replace(bateau_sim.ConfigBateau(), position_imu_m=(0.0, 0.0, 0.0))
        for fusion in ("complementaire", "mahony"):
            with self.subTest(fusion=fusion):
                r = banc.executer(scn, {"type": "pid_position"}, cfg_bateau=cfg,
                                  fusion=fusion, bruit_imu=zero, rodage_s=10.0)
                self.assertLess(r["erreur_gite_rms_deg"], 0.1)

    def test_source_parfaite_et_inconnue(self):
        scn = replace(banc.SCENARIOS["vagues"], duree_s=30.0)
        r = banc.executer(scn, {"type": "pid_position"}, source_gite="parfaite", rodage_s=5.0)
        self.assertLess(r["erreur_gite_rms_deg"], 1e-9)
        with self.assertRaises(ValueError):
            banc.executer(scn, {"type": "pid_position"}, source_gite="pendule")


class TestSignalK(unittest.TestCase):
    ETAT = {"t": 1.0, "consigne": 350.0, "cap_vrai": 10.0, "cap_estime": 9.0, "lacet_vrai": 1.0,
            "lacet_estime": 2.0, "gite_vraie": 5.0, "gite_estimee": 4.0, "tangage_estime": -1.0,
            "u": 0.5, "angle_barre_reel": 3.0, "angle_barre_mesure": 3.2, "x_tige_mm": 160.0,
            "courant_a": 1.5}

    def _valeurs(self, delta):
        return {v["path"]: v["value"] for v in delta["updates"][0]["values"]}

    def test_delta_en_unites_si(self):
        from signalk_emetteur import construire_delta
        d = construire_delta(self.ETAT, "essai")
        self.assertNotIn("context", d)                       # absent = ce bateau (« self »)
        self.assertEqual(d["updates"][0]["$source"], "essai")
        self.assertTrue(d["updates"][0]["timestamp"].endswith("Z"))
        v = self._valeurs(d)
        self.assertAlmostEqual(v["navigation.headingMagnetic"], math.radians(9.0))
        self.assertAlmostEqual(v["navigation.rateOfTurn"], math.radians(2.0))
        self.assertAlmostEqual(v["navigation.attitude"]["roll"], math.radians(4.0))
        self.assertAlmostEqual(v["steering.rudderAngle"], math.radians(3.2))
        self.assertAlmostEqual(v["simulation.headingError"], math.radians(-20.0))   # 350 − 10
        self.assertAlmostEqual(v["simulation.actuator.position"], 0.16)

    def test_valeur_non_finie_refusee(self):
        from signalk_emetteur import construire_delta
        with self.assertRaises(ValueError):
            construire_delta(dict(self.ETAT, courant_a=float("nan")))

    def test_envoi_udp_lisible(self):
        from signalk_emetteur import EmetteurSignalK
        recepteur = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recepteur.bind(("127.0.0.1", 0))
        recepteur.settimeout(2.0)
        e = EmetteurSignalK("127.0.0.1", recepteur.getsockname()[1])
        try:
            e.publier(self.ETAT)
            d = json.loads(recepteur.recv(65535).decode("utf-8"))
            self.assertIn("navigation.headingMagnetic", self._valeurs(d))
            self.assertEqual((e.envoyes, e.erreurs), (1, 0))
        finally:
            e.fermer()
            recepteur.close()

    def test_cadence_et_temps_reel(self):
        from banc_signalk import Cadence
        publies, dodos = [], []
        horloge = {"t": 100.0}
        c = Cadence(type("E", (), {"publier": lambda self, et: publies.append(et["t"])})(),
                    frequence_hz=5.0, vitesse=2.0, horloge=lambda: horloge["t"],
                    dormir=lambda s: (dodos.append(s), horloge.__setitem__("t", horloge["t"] + s)))
        for i in range(41):                                   # 2 s simulées à 20 Hz
            c({"t": i * 0.05})
        self.assertEqual(len(publies), 11)                    # 5 par seconde simulée, plus t = 0
        self.assertAlmostEqual(sum(dodos), 1.0, places=6)     # 2 s simulées à ×2 = 1 s réelle
        self.assertAlmostEqual(horloge["t"], 101.0, places=6)

    def test_observateur_du_banc(self):
        etats = []
        banc.executer(replace(banc.SCENARIOS["vagues"], duree_s=5.0), {"type": "pid_position"},
                      rodage_s=1.0, observateur=etats.append)
        self.assertEqual(len(etats), 100)                     # 20 Hz pendant 5 s
        self.assertEqual(set(etats[0]), set(banc.ETAT_OBSERVATEUR))


class TestFluxNodeRed(unittest.TestCase):
    def test_flux_a_jour_avec_le_code_js(self):
        import importlib.util
        chemin = os.path.join(ICI, "nodered", "generer_flux_nodered.py")
        spec = importlib.util.spec_from_file_location("generer_flux_nodered", chemin)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        with open(gen.SORTIE, encoding="utf-8") as f:
            self.assertEqual(f.read(), gen.texte_flux(),
                             "flux_alarme_ecart_cap.json périmé : relancer generer_flux_nodered.py")
        flux = json.loads(gen.texte_flux())
        types = {n["type"] for n in flux}
        self.assertLessEqual(types, {"tab", "signalk-subscribe", "inject", "function",
                                     "signalk-send-notification", "debug"})
        ids = {n["id"] for n in flux}
        for n in flux:
            for sortie in n.get("wires", []):
                self.assertLessEqual(set(sortie), ids)            # aucun fil vers un bloc absent

    def test_exclure_un_chemin(self):
        from signalk_emetteur import construire_delta
        d = construire_delta(TestSignalK.ETAT, exclure={"navigation.headingMagnetic"})
        chemins = [v["path"] for v in d["updates"][0]["values"]]
        self.assertNotIn("navigation.headingMagnetic", chemins)
        self.assertIn("steering.autopilot.target.headingMagnetic", chemins)


class TestVent(unittest.TestCase):
    def test_bateau_arrete_angle_egal_direction_moins_cap(self):
        from vent_sim import apparent_au_pont
        a, v = apparent_au_pont(270.0, 6.0, 230.0, 0.0)
        self.assertAlmostEqual(a, 40.0, places=6)            # vent de tribord : positif
        self.assertAlmostEqual(v, 6.0, places=6)
        a, _ = apparent_au_pont(190.0, 6.0, 230.0, 0.0)
        self.assertAlmostEqual(a, -40.0, places=6)           # vent de bâbord : négatif

    def test_vitesse_du_bateau_ramene_le_vent_vers_l_avant(self):
        from vent_sim import apparent_au_pont
        a, v = apparent_au_pont(270.0, 6.0, 180.0, 2.5)       # vent réel de travers tribord
        self.assertAlmostEqual(a, math.degrees(math.atan2(6.0, 2.5)), places=6)
        self.assertAlmostEqual(v, math.hypot(6.0, 2.5), places=6)

    def test_tete_de_mat_immobile_et_droite_egale_le_pont(self):
        from vent_sim import apparent_au_pont, apparent_en_tete_de_mat
        a1, v1 = apparent_au_pont(270.0, 6.0, 230.0, 2.5)
        a2, v2 = apparent_en_tete_de_mat(270.0, 6.0, 230.0, 2.5, 0.0, 0.0, (0, 0, 0), 8.5)
        self.assertAlmostEqual(a1, a2, places=9)
        self.assertAlmostEqual(v1, v2, places=9)

    def test_roulis_fausse_l_angle_et_la_correction_le_retrouve(self):
        from vent_sim import apparent_au_pont, apparent_en_tete_de_mat
        from mode_vent import ModeVent
        vrai, _ = apparent_au_pont(270.0, 6.0, 230.0, 2.5)
        p = math.radians(10.0)                               # roulis de 10 °/s vers tribord
        mesure, aws = apparent_en_tete_de_mat(270.0, 6.0, 230.0, 2.5, -15.0, 0.0, (p, 0, 0), 8.5)
        self.assertGreater(abs(mesure - vrai), 3.0)
        mv = ModeVent(40.0, hauteur_mat_m=8.5)
        corrige = mv.corriger(mesure, aws, -15.0, (0.0, p * 8.5))
        self.assertAlmostEqual(corrige, vrai, delta=0.05)

    def test_phrase_mwv_et_lecture(self):
        from girouette_sim import phrase_mwv
        from nmea_mwv import analyser_mwv
        ligne = phrase_mwv(-40.0, 6.0)
        self.assertTrue(ligne.startswith("$WIMWV,320.0,R,11.7,N,A*"))
        m = analyser_mwv(ligne, 3.0)
        self.assertAlmostEqual(m.angle_deg, -40.0)             # comme Signal K : > 180 -> négatif
        self.assertAlmostEqual(m.vitesse_ms, 11.7 * 0.514444, places=6)
        self.assertEqual((m.reference, m.t), ("R", 3.0))

    def test_lecteur_refuse_le_douteux(self):
        from girouette_sim import phrase_mwv, somme_controle
        from nmea_mwv import ErreurPhrase, analyser_mwv
        bonne = phrase_mwv(30.0, 5.0).strip()
        mauvaises = [bonne[:-2] + "00", bonne.replace(",A*", ",V*"), "WIMWV,30,R,5,N,A",
                     "$WIMWV,30.0,R*" + somme_controle("WIMWV,30.0,R")]
        for corps in ("WIMWV,400.0,R,5.0,N,A", "WIMWV,30.0,X,5.0,N,A", "WIMWV,30.0,R,5.0,Q,A",
                      "WIMWV,abc,R,5.0,N,A", "GPRMC,30.0,R,5.0,N,A"):
            mauvaises.append(f"${corps}*{somme_controle(corps)}")
        for ligne in mauvaises:
            with self.subTest(ligne=ligne):
                with self.assertRaises(ErreurPhrase):
                    analyser_mwv(ligne)

    def test_recepteur_age_et_vent_vrai_ignore(self):
        from girouette_sim import somme_controle
        from nmea_mwv import RecepteurVent
        r = RecepteurVent(age_max_s=2.0)
        r.ligne("$WIMWV,30.0,R,10.0,N,A*" + somme_controle("WIMWV,30.0,R,10.0,N,A"), 1.0)
        r.ligne("$WIMWV,99.0,T,10.0,N,A*" + somme_controle("WIMWV,99.0,T,10.0,N,A"), 1.5)
        self.assertAlmostEqual(r.vent_valide(2.9).angle_deg, 30.0)
        self.assertIsNone(r.vent_valide(3.1))
        r.ligne("n'importe quoi", 4.0)
        self.assertEqual(r.refusees, 1)

    def test_girouette_cadence_decalage_et_coupure(self):
        from girouette_sim import ConfigGirouette, GirouetteSim
        from nmea_mwv import analyser_mwv
        g = GirouetteSim(ConfigGirouette(bruit_angle_deg=0, bruit_vitesse_ms=0, amortissement_s=0,
                                         decalage_deg=3.0, coupure_a_s=5.0))
        phrases = []
        for i in range(1000):
            phrases += g.mettre_a_jour(40.0, 6.0, i * 0.01, 0.01)
        self.assertEqual(len(phrases), 20)                    # 4 Hz pendant 5 s, puis silence
        self.assertAlmostEqual(analyser_mwv(phrases[0]).angle_deg, 43.0, places=1)

    def test_mode_vent_consigne_et_refus_de_changer_de_bord(self):
        from mode_vent import ModeVent
        from nmea_mwv import MesureVent
        mv = ModeVent(40.0, tau_s=0.0, corriger_gite=False, corriger_mouvement=False)
        e = mv.mettre_a_jour(0.0, 0.05, 200.0, MesureVent(0.0, 55.0, 6.0, "R"))
        self.assertAlmostEqual(e.consigne_cap_deg, 215.0)     # direction 255° − 40°
        mv.changer_angle(45.0)
        with self.assertRaises(ValueError):
            mv.changer_angle(-40.0)                           # changer de bord = virer : jamais
        with self.assertRaises(ValueError):
            ModeVent(0.0)

    def test_mode_vent_secours_compas_sans_retour_seul(self):
        from mode_vent import ModeVent
        from nmea_mwv import MesureVent
        mv = ModeVent(40.0, age_max_s=2.0)
        e = mv.mettre_a_jour(0.0, 0.05, 200.0, None)          # premier vent pas encore là
        self.assertEqual((e.mode, e.alarme_vent_perdu), ("vent", False))
        e = mv.mettre_a_jour(1.0, 0.05, 200.0, MesureVent(1.0, 40.0, 6.0, "R"))
        consigne = e.consigne_cap_deg
        e = mv.mettre_a_jour(3.5, 0.05, 210.0, MesureVent(1.0, 40.0, 6.0, "R"))   # 2,5 s sans neuf
        self.assertEqual((e.mode, e.alarme_vent_perdu), ("compas_secours", True))
        self.assertAlmostEqual(e.consigne_cap_deg, consigne)  # cap tenu, pas d'angle figé
        e = mv.mettre_a_jour(4.0, 0.05, 210.0, MesureVent(4.0, 40.0, 6.0, "R"))
        self.assertEqual(e.mode, "compas_secours")            # le vent revient : pas de retour seul
        mv.reengager()
        e = mv.mettre_a_jour(4.1, 0.05, 210.0, MesureVent(4.1, 40.0, 6.0, "R"))
        self.assertEqual(e.mode, "vent")

    def test_mode_vent_jamais_de_vent_secours_apres_delai(self):
        from mode_vent import ModeVent
        mv = ModeVent(40.0, age_max_s=2.0)
        mv.mettre_a_jour(0.0, 0.05, 123.0, None)
        e = mv.mettre_a_jour(2.5, 0.05, 125.0, None)
        self.assertEqual((e.mode, e.consigne_cap_deg), ("compas_secours", 123.0))

    def test_banc_suit_la_bascule_sans_changer_de_bord(self):
        r = banc.executer(banc.SCENARIOS["vent_bascule"], {"type": "pid_position", "kp": 1.2,
                          "ki": 0.05, "kd": 2.0, "zone_integrale_deg": 5.0}, fusion="mahony")
        self.assertEqual(r["passages_de_bord"], 0)
        self.assertLess(r["awa_rms_deg"], 5.0)
        self.assertEqual(r["temps_secours_s"], 0.0)

    def test_banc_vent_perdu(self):
        r = banc.executer(banc.SCENARIOS["vent_perdu"], {"type": "pid_position"}, fusion="mahony")
        self.assertAlmostEqual(r["alarme_vent_perdu_s"], 62.0, delta=0.3)   # coupure 60 s + 2 s
        self.assertGreater(r["temps_secours_s"], 80.0)

    def test_signalk_chemins_du_vent(self):
        from signalk_emetteur import construire_delta
        etat = dict(TestSignalK.ETAT, awa_vrai=40.0, aws_vrai=7.0, awa_mesure=-30.0, aws_mesure=6.5,
                    twd=270.0, tws=6.0, angle_voulu=40.0, mode="vent")
        v = {x["path"]: x["value"] for x in construire_delta(etat)["updates"][0]["values"]}
        self.assertAlmostEqual(v["environment.wind.angleApparent"], math.radians(-30.0))
        self.assertAlmostEqual(v["steering.autopilot.target.windAngleApparent"], math.radians(40.0))
        self.assertEqual(v["simulation.autopilot.mode"], "vent")


class TestAnticipation(unittest.TestCase):
    CHEMIN = os.path.join(ICI, "anticipation_vent.json")

    def _ant(self, **r):
        from anticipation_vent import AnticipationVent, charger_config
        return AnticipationVent(charger_config(self.CHEMIN, **r))

    def _vent(self, t, angle, vitesse):
        from nmea_mwv import MesureVent
        return MesureVent(t, angle, vitesse, "R")

    def test_configuration_complete_et_stricte(self):
        from anticipation_vent import charger_config
        cfg = charger_config(self.CHEMIN)
        self.assertEqual(cfg.fenetre_s, 600)                 # les 10 dernières minutes
        self.assertEqual(cfg.borne_deg, 10.0)
        with self.assertRaises(ValueError):
            charger_config(self.CHEMIN, inconnu=1)
        with self.assertRaises(ValueError):
            charger_config(self.CHEMIN, seuil_arret_ms=1.0, seuil_marche_ms=0.5)

    def _apprendre(self, ant, pente=0.05, duree=600, bruit=0.0, t0=0.0):
        import random
        rng = random.Random(5)
        t = t0
        while t < t0 + duree:
            v = 7.0 + 1.0 * math.sin(2 * math.pi * t / 25.0)      # rafales régulières
            x = v * v
            barre = 1.0 + pente * x + rng.gauss(0, bruit)
            ant.mettre_a_jour(t, 0.05, self._vent(t, 40.0, v), barre, 0.0, 0.0, 215.0)
            t += 0.05
        return t

    def test_apprend_la_pente_et_prepare_la_barre(self):
        ant = self._ant(filtre_vent_s=0.0, regime_variation_vent_max_ms2=10.0)
        t = self._apprendre(ant, pente=0.05)
        mod = ant.modele(ant.tranche(ant.angle_base))
        self.assertAlmostEqual(mod[1], 0.05, places=4)
        e = ant.mettre_a_jour(t, 0.05, self._vent(t, 40.0, 9.5), 3.0, 0.0, 0.0, 215.0)   # renforcement
        self.assertEqual((e.etat, e.motif), ("calculee", ""))
        self.assertAlmostEqual(e.correction_deg, 0.05 * (9.5 ** 2 - ant.x_base), delta=0.01)

    def test_correction_toujours_bornee(self):
        ant = self._ant(filtre_vent_s=0.0, regime_variation_vent_max_ms2=10.0, saut_max_ms=30.0)
        t = self._apprendre(ant, pente=0.5)
        e = ant.mettre_a_jour(t, 0.05, self._vent(t, 40.0, 30.0), 3.0, 0.0, 0.0, 215.0)
        self.assertEqual(e.correction_deg, 10.0)

    def test_pas_de_modele_sans_assez_de_points(self):
        ant = self._ant()
        e = ant.mettre_a_jour(0.0, 0.05, self._vent(0.0, 40.0, 7.0), 1.0, 0.0, 0.0, 215.0)
        self.assertEqual((e.correction_deg, e.motif), (0.0, "modele_insuffisant"))

    def test_regime_etabli_seulement(self):
        ant = self._ant()
        t = 0.0
        while t < 300:                                        # le bateau lacet fort : rien n'est appris
            ant.mettre_a_jour(t, 0.05, self._vent(t, 40.0, 7.0), 1.0, 5.0, 0.0, 215.0)
            t += 0.05
        self.assertEqual(sum(len(d) for d in ant.points.values()), 0)

    def test_oubli_au_dela_de_dix_minutes(self):
        ant = self._ant(filtre_vent_s=0.0, regime_variation_vent_max_ms2=10.0)
        self._apprendre(ant, duree=900)
        plus_vieux = min(p[0] for d in ant.points.values() for p in d)
        self.assertGreaterEqual(plus_vieux, 900 - 600 - 1.0)

    def test_coupures_avec_motif(self):
        ant = self._ant(filtre_vent_s=0.0, regime_variation_vent_max_ms2=10.0)
        t = self._apprendre(ant)
        cas = [(None, "vent_absent"), (self._vent(t - 5.0, 40.0, 7.0), "vent_trop_vieux"),
               (self._vent(t, 40.0, 80.0), "hors_plage"), (self._vent(t, 40.0, 13.0), "saut_brutal")]
        for mesure, motif in cas:
            with self.subTest(motif=motif):
                e = ant.mettre_a_jour(t, 0.05, mesure, 1.0, 0.0, 0.0, 215.0)
                self.assertEqual((e.correction_deg, e.etat, e.motif), (0.0, "coupee", motif))
        e = ant.mettre_a_jour(t, 0.05, self._vent(t, 40.0, 7.0), 1.0, 0.0, 0.0, 215.0, engage=False)
        self.assertEqual((e.correction_deg, e.motif), (0.0, "veille"))

    def test_hysteresis_vent_faible(self):
        ant = self._ant(filtre_vent_s=0.0)
        self.assertEqual(ant.mettre_a_jour(0.0, 0.05, self._vent(0.0, 40.0, 0.5), 0, 0, 0, 0).motif,
                         "vent_faible")                       # jamais monté à 0,6 m/s
        ant.mettre_a_jour(0.1, 0.05, self._vent(0.1, 40.0, 0.7), 0, 0, 0, 0)
        self.assertNotEqual(ant.mettre_a_jour(0.2, 0.05, self._vent(0.2, 40.0, 0.5), 0, 0, 0, 0).motif,
                            "vent_faible")                    # 0,5 : au-dessus de l'arrêt (0,4)
        self.assertEqual(ant.mettre_a_jour(0.3, 0.05, self._vent(0.3, 40.0, 0.3), 0, 0, 0, 0).motif,
                         "vent_faible")

    def test_fantome_n_agit_jamais(self):
        """CON-009, critère 1 : en mode fantôme, aucune commande n'est envoyée."""
        scn = replace(banc.SCENARIOS["renfort_compas_ardent"], duree_s=700.0)
        reg = {"type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 2.0, "zone_integrale_deg": 5.0}
        vus = []
        a = banc.executer(scn, reg, fusion="mahony", anticipation="aucune")
        f = banc.executer(scn, reg, fusion="mahony", anticipation="fantome",
                          observateur=lambda e: vus.append(e.get("anticipation_deg", 0.0)))
        for k in ("erreur_rms_deg", "parcours_mm_min", "renfort_erreur_max_deg"):
            self.assertEqual(a[k], f[k], k)
        self.assertTrue(any(v != 0.0 for v in vus))         # elle calcule bien quelque chose…
        self.assertNotIn("anticipation", reg)                # …sans que le régulateur la reçoive

    def test_active_refusee_avec_pypilot(self):
        with self.assertRaises(ValueError):
            banc.executer(banc.SCENARIOS["renfort_compas"], {"type": "pypilot_basic"},
                          anticipation="active")

    def test_journal_con009(self):
        from anticipation_vent import COLONNES_JOURNAL, AnticipationVent, charger_config
        chemin = os.path.join(tempfile.gettempdir(), "simu_9axes_test_anticipation.csv")
        ant = AnticipationVent(charger_config(self.CHEMIN), chemin)
        try:
            for i in range(10):
                ant.mettre_a_jour(i * 0.05, 0.05, self._vent(i * 0.05, 40.0, 7.0), 1.0, 0.0, 0.0, 215.0)
        finally:
            ant.fermer()
        with open(chemin, encoding="utf-8") as f:
            lignes = list(csv.reader(f))
        self.assertEqual(tuple(lignes[0]), COLONNES_JOURNAL)
        self.assertEqual(len(lignes), 11)

    def test_renforcement_du_vent(self):
        from vent_sim import Renforcement
        r = Renforcement(100.0, 0.35, 15.0, montee_s=8.0, palier_s=30.0, descente_s=10.0)
        self.assertEqual([r.part(t) for t in (99.0, 104.0, 120.0, 143.0, 149.0)],
                         [0.0, 0.5, 1.0, 0.5, 0.0])


class TestBancHonnete(unittest.TestCase):
    """Étape 1 : profils de voiliers dont la physique diffère des hypothèses des algorithmes."""

    def test_interpolation_et_tables_verifiees(self):
        from voilure_sim import ProfilVoilier, interpoler
        t = ((0, 0.0), (90, 1.0), (180, 0.0))
        self.assertEqual([interpoler(t, x) for x in (-5, 45, 90, 135, 200)], [0.0, 0.5, 1.0, 0.5, 0.0])
        with self.assertRaises(ValueError):
            ProfilVoilier("x", "table incomplète", table_gite=((0, 0.0), (90, 1.0)))
        with self.assertRaises(ValueError):
            ProfilVoilier("x", "négatif", tau_gite_s=-1.0)

    def test_profil_reference_redonne_le_banc_v3(self):
        """Contrôle : sans différence de physique, mêmes chiffres que l'ancien chemin de code."""
        reg = {"type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 2.0, "zone_integrale_deg": 5.0}
        scn = replace(banc.SCENARIOS["renfort_compas"], duree_s=200.0)
        a = banc.executer(scn, reg, fusion="mahony")
        b = banc.executer(scn, reg, fusion="mahony", voilier="reference")
        for k in ("erreur_rms_deg", "erreur_p95_deg", "parcours_mm_min", "ecart_estimation_rms_deg"):
            self.assertAlmostEqual(a[k], b[k], places=9, msg=k)

    def test_retard_de_gite(self):
        from voilure_sim import ProfilVoilier, Voilure
        v = Voilure(ProfilVoilier("x", "retard", tau_gite_s=3.0))
        v.pas(0.01, 40.0, 1.0, 6.0, 60.0, 0.0)                  # vent faible au départ
        g0 = v.gite_vent
        for _ in range(300):                                    # 3 s de vent fort
            v.pas(0.01, 40.0, 9.0, 6.0, 60.0, 0.0)
        cible = -12.0 * (9.0 / 7.0) ** 2 * math.sin(math.radians(40))
        self.assertAlmostEqual((v.gite_vent - g0) / (cible - g0), 1 - math.exp(-1), delta=0.02)

    def test_ardeur_progressive_et_couple_des_voiles(self):
        from voilure_sim import ProfilVoilier, Voilure, TABLE_LACET_VOILES
        v = Voilure(ProfilVoilier("x", "ardeur", k_gite_lacet=0.2, k_gite_lacet_par_deg=0.02))
        _, p10, _ = v.pas(0.01, 40.0, 7.0, 6.0, 60.0, -10.0)
        _, p20, _ = v.pas(0.01, 40.0, 7.0, 6.0, 60.0, -20.0)
        self.assertAlmostEqual(p10, 0.4 * 10.0)                 # gîte bâbord : remonte vers tribord
        self.assertAlmostEqual(p20, 0.6 * 20.0)
        w = Voilure(ProfilVoilier("x", "couple", k_gite_lacet=0.0, table_lacet_voiles=TABLE_LACET_VOILES))
        _, pv, _ = w.pas(0.01, 45.0, 7.0, 6.0, 60.0, 0.0)
        self.assertAlmostEqual(pv, 1.2)

    def test_polaire(self):
        from voilure_sim import PROFILS, Voilure
        v = Voilure(PROFILS["polaire"])
        self.assertLess(v.vitesse_polaire(6.0, 40.0), v.vitesse_polaire(6.0, 90.0))
        self.assertLess(v.vitesse_polaire(3.0, 90.0), v.vitesse_polaire(9.0, 90.0))
        self.assertLessEqual(v.vitesse_polaire(30.0, 90.0), 3.0)

    def test_roulis_realiste_dans_les_vagues(self):
        """Avant le 2026-11-26, le roulis entrait en résonance (écart type 11°, pointes à ±29°)."""
        import statistics
        g = []
        banc.executer(replace(banc.SCENARIOS["vagues"], duree_s=120.0), {"type": "pid_position"},
                      rodage_s=5.0, observateur=lambda e: g.append(e["gite_vraie"]) if e["t"] > 20 else None)
        self.assertLess(statistics.pstdev(g), 6.0)
        self.assertLess(max(abs(x) for x in g), 15.0)

    def test_profil_inconnu_ou_sans_vent(self):
        with self.assertRaises(ValueError):
            banc.executer(banc.SCENARIOS["renfort_compas"], {"type": "pid_position"}, voilier="catamaran")
        with self.assertRaises(ValueError):
            banc.executer(banc.SCENARIOS["vagues"], {"type": "pid_position"}, voilier="reference")

    def test_piege_de_la_zone_d_integrale(self):
        """Trouvé par le banc honnête : sur un bateau très ardent, la zone de 5° gèle l'intégrale."""
        scn = replace(banc.SCENARIOS["renfort_compas"], duree_s=300.0)
        base = {"type": "pid_position", "kp": 1.2, "ki": 0.05, "kd": 2.0}
        avec = banc.executer(scn, {**base, "zone_integrale_deg": 5.0}, fusion="mahony", voilier="tout")
        sans = banc.executer(scn, base, fusion="mahony", voilier="tout")
        self.assertGreater(avec["erreur_p95_deg"], 2 * sans["erreur_p95_deg"])


if __name__ == "__main__":
    unittest.main()
