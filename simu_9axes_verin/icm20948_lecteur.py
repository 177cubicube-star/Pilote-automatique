"""icm20948_lecteur.py : le code Python qui PARLE à l'ICM-20948 par I2C.

C'est le morceau destiné à tourner un jour sur le Raspberry Pi. Il ne sait pas
s'il parle à la vraie carte ou à la puce simulée : il reçoit un objet « bus »
qui offre les méthodes de `smbus2.SMBus`.

    # au banc virtuel
    from icm20948_sim import PuceICM20948, FauxBusI2C
    bus = FauxBusI2C(PuceICM20948())

    # sur le Pi, plus tard (pip install smbus2)
    import smbus2
    bus = smbus2.SMBus(1)

    lecteur = LecteurICM20948(bus)
    lecteur.demarrer()
    mesure = lecteur.lire(t)

Rôle dans l'architecture DEC-014 : pypilot lit déjà sa centrale lui-même.
Ce lecteur sert (1) à préparer et tester la chaîne de mesure avant le matériel,
(2) d'outil de diagnostic au banc (vérifier câblage, adresses, signes des axes),
(3) de base si une lecture hors pypilot devient nécessaire (LIS3DH, journal).
Ce n'est PAS une décision de remplacer la lecture de pypilot.

Séquence de démarrage (registres : voir icm20948_sim.py, À VÉRIFIER sur la fiche) :
  1. banque 0, réinitialisation (PWR_MGMT_1 = 0x80), attente
  2. WHO_AM_I doit valoir 0xEA, sinon ErreurCapteur
  3. réveil (PWR_MGMT_1 = 0x01 : sommeil coupé, horloge auto)
  4. banque 2 : pleines échelles du gyroscope et de l'accéléromètre
  5. banque 0 : maître I2C interne coupé, mode « bypass » allumé
  6. AK09916 : WIA2 doit valoir 0x09, puis mode continu 100 Hz

Sortie : grandeurs physiques dans le repère CORPS du bateau
(x avant, y tribord, z bas), en m/s², °/s et µT, calibration du magnétomètre
appliquée. Stdlib seulement.
"""
from __future__ import annotations

import struct
import time
from dataclasses import dataclass

from icm20948_sim import (
    ACCEL_LSB_PAR_G, ADRESSE_AK09916, ADRESSE_ICM_DEFAUT, AK_CNTL2, AK_HXL,
    AK_MODE_CONTINU_100HZ, AK_ST1, AK_UT_PAR_LSB, AK_VERS_PUCE, AK_WIA2,
    BIT_BYPASS_EN, BIT_I2C_MST_EN, G, GYRO_LSB_PAR_DPS, MONTURE_CORPS_VERS_PUCE,
    REG_ACCEL_CONFIG, REG_ACCEL_XOUT_H, REG_BANK_SEL, REG_GYRO_CONFIG_1,
    REG_INT_PIN_CFG, REG_PWR_MGMT_1, REG_USER_CTRL, REG_WHO_AM_I, TEMP_DECALAGE_C,
    TEMP_LSB_PAR_C, VAL_WHO_AM_I, VAL_WIA2, mat_t_vec, mat_vec,
)


class ErreurCapteur(Exception):
    """La centrale ne répond pas, ou pas comme une ICM-20948."""


@dataclass(frozen=True)
class MesureIMU:
    t: float
    accel_ms2: tuple          # repère corps
    gyro_dps: tuple           # repère corps
    mag_ut: tuple | None      # repère corps, calibré ; None si pas de mesure neuve
    temp_c: float


class LecteurICM20948:
    def __init__(self, bus, adresse: int = ADRESSE_ICM_DEFAUT, fs_gyro: int = 0,
                 fs_accel: int = 0, monture=MONTURE_CORPS_VERS_PUCE,
                 ak_vers_puce=AK_VERS_PUCE, fer_dur_ut=(0.0, 0.0, 0.0),
                 echelle_mag=(1.0, 1.0, 1.0), attente=time.sleep, essais: int = 2):
        if fs_gyro not in GYRO_LSB_PAR_DPS or fs_accel not in ACCEL_LSB_PAR_G:
            raise ValueError("fs_gyro et fs_accel vont de 0 à 3")
        if essais < 1:
            raise ValueError("essais doit être >= 1")
        self.bus = bus
        self.adresse = adresse
        self.fs_gyro = fs_gyro
        self.fs_accel = fs_accel
        self.monture = monture
        self.ak_vers_puce = ak_vers_puce
        self.fer_dur_ut = tuple(fer_dur_ut)       # calibration « fer dur » (repère corps)
        self.echelle_mag = tuple(echelle_mag)     # calibration « fer doux » simplifiée
        self.attente = attente
        self.essais = essais
        self._banque = None
        self.erreurs_bus = 0                      # transactions ratées puis réessayées
        self.mag_debordements = 0
        self.demarre = False

    # ----------------------------------------------------------- outils bus
    def _essayer(self, fonction, *args):
        derniere = None
        for _ in range(self.essais):
            try:
                return fonction(*args)
            except OSError as erreur:
                self.erreurs_bus += 1
                derniere = erreur
        raise ErreurCapteur(f"bus I2C : {derniere}")

    def _banque_(self, banque: int) -> None:
        if self._banque != banque:
            self._essayer(self.bus.write_byte_data, self.adresse, REG_BANK_SEL, banque << 4)
            self._banque = banque

    def _ecrire(self, reg: int, val: int) -> None:
        self._essayer(self.bus.write_byte_data, self.adresse, reg, val)

    def _lire(self, reg: int) -> int:
        return self._essayer(self.bus.read_byte_data, self.adresse, reg)

    # -------------------------------------------------------------- démarrage
    def demarrer(self) -> None:
        self._banque = None
        self._banque_(0)
        self._ecrire(REG_PWR_MGMT_1, 0x80)          # réinitialisation
        self.attente(0.1)
        self._banque = None                         # la réinitialisation remet la banque 0
        self._banque_(0)
        qui = self._lire(REG_WHO_AM_I)
        if qui != VAL_WHO_AM_I:
            raise ErreurCapteur(f"WHO_AM_I = 0x{qui:02X}, 0x{VAL_WHO_AM_I:02X} attendu "
                                f"(mauvaise puce ou mauvaise adresse 0x{self.adresse:02X} ?)")
        self._ecrire(REG_PWR_MGMT_1, 0x01)          # réveil, horloge auto
        self.attente(0.05)

        self._banque_(2)
        self._ecrire(REG_GYRO_CONFIG_1, (self.fs_gyro << 1) | 0x01)
        self._ecrire(REG_ACCEL_CONFIG, (self.fs_accel << 1) | 0x01)
        self._banque_(0)

        user = self._lire(REG_USER_CTRL)
        self._ecrire(REG_USER_CTRL, user & ~BIT_I2C_MST_EN & 0xFF)
        pin = self._lire(REG_INT_PIN_CFG)
        self._ecrire(REG_INT_PIN_CFG, pin | BIT_BYPASS_EN)
        self.attente(0.01)

        wia2 = self._essayer(self.bus.read_byte_data, ADRESSE_AK09916, AK_WIA2)
        if wia2 != VAL_WIA2:
            raise ErreurCapteur(f"AK09916 : WIA2 = 0x{wia2:02X}, 0x{VAL_WIA2:02X} attendu")
        self._essayer(self.bus.write_byte_data, ADRESSE_AK09916, AK_CNTL2, AK_MODE_CONTINU_100HZ)
        self.attente(0.01)
        self.demarre = True

    # ------------------------------------------------------------------ lecture
    def lire(self, t: float) -> MesureIMU:
        """Une lecture complète. Lève ErreurCapteur si le bus échoue `essais` fois."""
        if not self.demarre:
            raise ErreurCapteur("demarrer() n'a pas été appelé")
        self._banque_(0)
        brut = self._essayer(self.bus.read_i2c_block_data, self.adresse, REG_ACCEL_XOUT_H, 14)
        ax, ay, az, gx, gy, gz, tmp = struct.unpack(">7h", bytes(brut))
        lsb_a = ACCEL_LSB_PAR_G[self.fs_accel]
        lsb_g = GYRO_LSB_PAR_DPS[self.fs_gyro]
        acc_p = (ax / lsb_a * G, ay / lsb_a * G, az / lsb_a * G)
        gyr_p = (gx / lsb_g, gy / lsb_g, gz / lsb_g)

        mag = None
        st1 = self._essayer(self.bus.read_byte_data, ADRESSE_AK09916, AK_ST1)
        if st1 & 0x01:
            # HXL..HZH, TMPS, ST2 : lire jusqu'à ST2 libère la mesure suivante
            d = self._essayer(self.bus.read_i2c_block_data, ADRESSE_AK09916, AK_HXL, 8)
            hx, hy, hz = struct.unpack("<3h", bytes(d[:6]))
            if d[7] & 0x08:
                self.mag_debordements += 1
            else:
                mag_ak = (hx * AK_UT_PAR_LSB, hy * AK_UT_PAR_LSB, hz * AK_UT_PAR_LSB)
                mag_c = mat_t_vec(self.monture, mat_vec(self.ak_vers_puce, mag_ak))
                mag = tuple((mag_c[k] - self.fer_dur_ut[k]) * self.echelle_mag[k]
                            for k in range(3))

        return MesureIMU(
            t=t,
            accel_ms2=mat_t_vec(self.monture, acc_p),
            gyro_dps=mat_t_vec(self.monture, gyr_p),
            mag_ut=mag,
            temp_c=tmp / TEMP_LSB_PAR_C + TEMP_DECALAGE_C,
        )
