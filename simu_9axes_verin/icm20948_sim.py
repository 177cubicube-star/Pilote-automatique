"""icm20948_sim.py : centrale inertielle ICM-20948 SIMULÉE, vue à travers un faux bus I2C.

À quoi ça sert
--------------
Écrire dès maintenant le code Python qui LIT la centrale (le « lecteur »), sans
avoir la carte. Le lecteur parle à ce faux bus exactement comme il parlera au
vrai bus I2C du Raspberry Pi via `smbus2` : mêmes noms de méthodes
(`read_byte_data`, `write_byte_data`, `read_i2c_block_data`), mêmes adresses,
mêmes registres, mêmes octets. Le jour de la carte, on remplace

    bus = FauxBusI2C(puce)          par          bus = smbus2.SMBus(1)

et le lecteur ne change pas.

Ce que la puce simulée fait
---------------------------
- Registres principaux de l'ICM-20948 (banques 0 et 2) et du magnétomètre
  AK09916 intégré (accessible en mode « bypass », adresse 0x0C).
- Réinitialisation, mise en sommeil (données à zéro tant que la puce dort),
  choix des pleines échelles, sélection de banque.
- Conversion des grandeurs physiques en entiers 16 bits : bruit, biais, dérive
  lente du biais du gyroscope, quantification, saturation.
- Magnétomètre à 100 Hz avec drapeaux DRDY (donnée prête), DOR (donnée
  écrasée non lue) et HOFL (débordement).
- Injection d'erreurs de bus (OSError 121, comme smbus2 sur un câble douteux).

Ce qu'elle ne fait PAS
----------------------
FIFO, DMP (fusion interne d'InvenSense), interruptions, filtres numériques
internes (DLPF), maître I2C interne. Le temps de démarrage réel n'est pas imposé.

Valeurs reprises de la fiche technique — À VÉRIFIER
---------------------------------------------------
Adresses et registres ci-dessous écrits d'après la fiche InvenSense DS-000189
et celle de l'AK09916 (AKM), SANS relecture du document pendant cette session.
Bruits et biais : ordres de grandeur supposés. Orientation des axes du
magnétomètre par rapport à l'accéléromètre : hypothèse (voir AK_VERS_PUCE),
à confirmer à la main sur la vraie carte (tourner la carte, regarder les signes).

Repères
-------
Repère « corps » du bateau : x vers l'avant, y vers tribord, z vers le bas.
Repère « puce » : celui de l'accéléromètre et du gyroscope de l'ICM-20948.
La monture par défaut suppose la carte à plat, composants en haut, flèche x
vers l'avant : puce = (x, -y, -z) du corps. Au repos, l'accéléromètre lit +1 g
sur z puce.

Bibliothèque standard seulement.
"""
from __future__ import annotations

import math
import random
import struct
from dataclasses import dataclass

# --------------------------------------------------------------- adresses I2C
ADRESSE_ICM_DEFAUT = 0x69   # broche AD0 haute (réglage par défaut supposé de la carte Adafruit 4554)
ADRESSE_ICM_AD0_BAS = 0x68
ADRESSE_AK09916 = 0x0C

# ------------------------------------------------------ registres ICM, banque 0
REG_WHO_AM_I = 0x00
VAL_WHO_AM_I = 0xEA
REG_USER_CTRL = 0x03
BIT_I2C_MST_EN = 0x20
REG_PWR_MGMT_1 = 0x06
BIT_DEVICE_RESET = 0x80
BIT_SLEEP = 0x40
VAL_PWR_MGMT_1_RESET = 0x41          # en sommeil + horloge auto après réinitialisation
REG_INT_PIN_CFG = 0x0F
BIT_BYPASS_EN = 0x02
REG_ACCEL_XOUT_H = 0x2D              # 0x2D..0x32 accéléro, 0x33..0x38 gyro, 0x39..0x3A temp.
REG_TEMP_OUT_H = 0x39
REG_BANK_SEL = 0x7F                  # présent dans toutes les banques, banque = bits 5:4

# ------------------------------------------------------ registres ICM, banque 2
REG_GYRO_CONFIG_1 = 0x01             # bits 2:1 = GYRO_FS_SEL
REG_ACCEL_CONFIG = 0x14              # bits 2:1 = ACCEL_FS_SEL

# ------------------------------------------------------------- registres AK09916
AK_WIA1 = 0x00
VAL_WIA1 = 0x48
AK_WIA2 = 0x01
VAL_WIA2 = 0x09
AK_ST1 = 0x10                        # bit 0 DRDY, bit 1 DOR
AK_HXL = 0x11                        # 0x11..0x16 : X, Y, Z en petit-boutiste
AK_ST2 = 0x18                        # bit 3 HOFL ; LIRE ST2 libère la mesure suivante
AK_CNTL2 = 0x31
AK_CNTL3 = 0x32
AK_MODE_ARRET = 0x00
AK_MODE_CONTINU_100HZ = 0x08

# --------------------------------------------------------------- conversions
GYRO_LSB_PAR_DPS = {0: 131.0, 1: 65.5, 2: 32.8, 3: 16.4}        # ±250, 500, 1000, 2000 °/s
ACCEL_LSB_PAR_G = {0: 16384.0, 1: 8192.0, 2: 4096.0, 3: 2048.0}  # ±2, 4, 8, 16 g
AK_UT_PAR_LSB = 0.15
AK_MAX_LSB = 32752
TEMP_LSB_PAR_C = 333.87
TEMP_DECALAGE_C = 21.0
G = 9.80665

# ------------------------------------------------------------------- repères
# Matrices 3x3 en tuples de lignes. Toutes celles-ci sont orthonormées.
MONTURE_CORPS_VERS_PUCE = ((1, 0, 0), (0, -1, 0), (0, 0, -1))
AK_VERS_PUCE = ((1, 0, 0), (0, -1, 0), (0, 0, -1))   # HYPOTHÈSE : y et z du magnétomètre inversés


def mat_vec(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def mat_t_vec(m, v):
    """Transposée fois vecteur (= inverse pour une matrice orthonormée)."""
    return (m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2],
            m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2],
            m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2])


def _int16(valeur: float, limite: int | None = None) -> int:
    """Arrondit et sature comme un registre 16 bits signé (ou à ±limite)."""
    lo, hi = (-32768, 32767) if limite is None else (-limite, limite)
    return max(lo, min(hi, int(round(valeur))))


@dataclass(frozen=True)
class ConfigBruit:
    """Défauts de la puce. Ordres de grandeur SUPPOSÉS (pas mesurés).

    Biais : si `gyro_biais_dps` ou `accel_biais_g` vaut None, chaque axe est tiré
    au hasard (loi normale, écart type donné) à partir de la graine de la puce.
    Ainsi chaque graine est une « autre carte ». Des biais fixes identiques pour
    toutes les graines pouvaient se compenser par hasard et fausser les
    comparaisons (constaté le 2026-11-26)."""
    gyro_bruit_dps: float = 0.10                       # écart type par échantillon
    gyro_biais_dps: tuple | None = None                # biais de départ (repère puce)
    ecart_type_biais_gyro_dps: float = 0.3
    gyro_derive_dps_par_rac_s: float = 0.002           # marche aléatoire du biais
    accel_bruit_g: float = 0.002
    accel_biais_g: tuple | None = None
    ecart_type_biais_accel_g: float = 0.010            # HYPOTHÈSE : accéléromètre NON calibré
    mag_bruit_ut: float = 0.6
    periode_mag_s: float = 0.01                        # 100 Hz (mode continu 4)


class PuceICM20948:
    """La puce : registres + conversion physique -> octets."""

    def __init__(self, bruit: ConfigBruit = ConfigBruit(), graine: int = 0,
                 monture=MONTURE_CORPS_VERS_PUCE, ak_vers_puce=AK_VERS_PUCE):
        self.bruit = bruit
        self.monture = monture
        self.ak_vers_puce = ak_vers_puce
        self.rng = random.Random(graine)
        self.biais_gyro = (list(bruit.gyro_biais_dps) if bruit.gyro_biais_dps is not None
                           else [self.rng.gauss(0, bruit.ecart_type_biais_gyro_dps) for _ in range(3)])
        self.biais_accel = (list(bruit.accel_biais_g) if bruit.accel_biais_g is not None
                            else [self.rng.gauss(0, bruit.ecart_type_biais_accel_g) for _ in range(3)])
        self._reinitialiser_icm()
        self.ak = bytearray(0x40)
        self.ak[AK_WIA1] = VAL_WIA1
        self.ak[AK_WIA2] = VAL_WIA2
        self._chrono_mag = 0.0

    # ---------------------------------------------------------------- état
    def _reinitialiser_icm(self):
        self.banque = 0
        self.regs = [bytearray(0x80) for _ in range(4)]
        self.regs[0][REG_WHO_AM_I] = VAL_WHO_AM_I
        self.regs[0][REG_PWR_MGMT_1] = VAL_PWR_MGMT_1_RESET

    @property
    def dort(self) -> bool:
        return bool(self.regs[0][REG_PWR_MGMT_1] & BIT_SLEEP)

    @property
    def magnetometre_accessible(self) -> bool:
        return bool(self.regs[0][REG_INT_PIN_CFG] & BIT_BYPASS_EN) and not (
            self.regs[0][REG_USER_CTRL] & BIT_I2C_MST_EN)

    @property
    def fs_gyro(self) -> int:
        return (self.regs[2][REG_GYRO_CONFIG_1] >> 1) & 0x03

    @property
    def fs_accel(self) -> int:
        return (self.regs[2][REG_ACCEL_CONFIG] >> 1) & 0x03

    # ------------------------------------------------------ accès registres
    def lire_icm(self, reg: int) -> int:
        if reg == REG_BANK_SEL:
            return self.banque << 4
        return self.regs[self.banque][reg]

    def ecrire_icm(self, reg: int, val: int) -> None:
        if reg == REG_BANK_SEL:
            self.banque = (val >> 4) & 0x03
            return
        if self.banque == 0 and reg == REG_PWR_MGMT_1 and val & BIT_DEVICE_RESET:
            self._reinitialiser_icm()
            return
        if self.banque == 0 and reg == REG_WHO_AM_I:
            return                                   # lecture seule
        self.regs[self.banque][reg] = val

    def lire_ak(self, reg: int) -> int:
        val = self.ak[reg]
        if reg == AK_ST2:                            # fin de lecture : libère la mesure
            self.ak[AK_ST1] &= ~0x03 & 0xFF
        return val

    def ecrire_ak(self, reg: int, val: int) -> None:
        if reg == AK_CNTL3 and val & 0x01:           # réinitialisation logicielle
            self.ak = bytearray(0x40)
            self.ak[AK_WIA1] = VAL_WIA1
            self.ak[AK_WIA2] = VAL_WIA2
            return
        if reg in (AK_CNTL2, AK_CNTL3):
            self.ak[reg] = val

    # ------------------------------------------------- monde physique -> octets
    def mettre_a_jour(self, accel_ms2_corps, gyro_dps_corps, champ_ut_corps,
                      temp_c: float, dt_s: float) -> None:
        """Échantillonne le monde physique (repère corps) et remplit les registres."""
        b = self.bruit
        rac = math.sqrt(max(dt_s, 0.0))
        for k in range(3):
            self.biais_gyro[k] += b.gyro_derive_dps_par_rac_s * rac * self.rng.gauss(0, 1)

        if not self.dort:
            acc_p = mat_vec(self.monture, accel_ms2_corps)
            gyr_p = mat_vec(self.monture, gyro_dps_corps)
            lsb_a = ACCEL_LSB_PAR_G[self.fs_accel]
            lsb_g = GYRO_LSB_PAR_DPS[self.fs_gyro]
            brut = []
            for k in range(3):
                g_val = acc_p[k] / G + self.biais_accel[k] + self.rng.gauss(0, b.accel_bruit_g)
                brut.append(_int16(g_val * lsb_a))
            for k in range(3):
                d_val = gyr_p[k] + self.biais_gyro[k] + self.rng.gauss(0, b.gyro_bruit_dps)
                brut.append(_int16(d_val * lsb_g))
            brut.append(_int16((temp_c - TEMP_DECALAGE_C) * TEMP_LSB_PAR_C))
            self.regs[0][REG_ACCEL_XOUT_H:REG_ACCEL_XOUT_H + 14] = struct.pack(">7h", *brut)

        if self.ak[AK_CNTL2] == AK_MODE_CONTINU_100HZ:
            self._chrono_mag += dt_s
            if self._chrono_mag + 1e-9 >= b.periode_mag_s:
                self._chrono_mag -= b.periode_mag_s
                self._echantillon_mag(champ_ut_corps)

    def _echantillon_mag(self, champ_ut_corps):
        mag_p = mat_vec(self.monture, champ_ut_corps)
        mag_ak = mat_t_vec(self.ak_vers_puce, mag_p)
        brut, deborde = [], False
        for k in range(3):
            lsb = (mag_ak[k] + self.rng.gauss(0, self.bruit.mag_bruit_ut)) / AK_UT_PAR_LSB
            if abs(lsb) > AK_MAX_LSB:
                deborde = True
            brut.append(_int16(lsb, AK_MAX_LSB))
        self.ak[AK_HXL:AK_HXL + 6] = struct.pack("<3h", *brut)
        st1 = self.ak[AK_ST1]
        dor = 0x02 if st1 & 0x01 else 0x00            # la précédente n'a pas été lue
        self.ak[AK_ST1] = 0x01 | dor
        self.ak[AK_ST2] = 0x08 if deborde else 0x00


class FauxBusI2C:
    """Imite l'objet `smbus2.SMBus` pour les méthodes dont le lecteur a besoin.

    taux_erreur : probabilité qu'une transaction lève OSError(121), comme un
    câble I2C trop long ou parasité. Aucune transaction n'est faite à moitié."""

    def __init__(self, puce: PuceICM20948, adresse_icm: int = ADRESSE_ICM_DEFAUT,
                 taux_erreur: float = 0.0, graine: int = 0):
        self.puce = puce
        self.adresse_icm = adresse_icm
        self.taux_erreur = taux_erreur
        self.rng = random.Random(graine)
        self.transactions = 0
        self.erreurs = 0

    def _cible(self, adresse: int) -> str:
        self.transactions += 1
        if self.taux_erreur and self.rng.random() < self.taux_erreur:
            self.erreurs += 1
            raise OSError(121, "Remote I/O error (simulée)")
        if adresse == self.adresse_icm:
            return "icm"
        if adresse == ADRESSE_AK09916 and self.puce.magnetometre_accessible:
            return "ak"
        self.erreurs += 1
        raise OSError(121, f"Remote I/O error : rien ne répond à 0x{adresse:02X}")

    @staticmethod
    def _octet(valeur: int) -> int:
        if not 0 <= valeur <= 0xFF:
            raise ValueError(f"octet hors limites : {valeur}")
        return valeur

    def read_byte_data(self, i2c_addr: int, register: int) -> int:
        if self._cible(i2c_addr) == "icm":
            return self.puce.lire_icm(register)
        return self.puce.lire_ak(register)

    def write_byte_data(self, i2c_addr: int, register: int, value: int) -> None:
        value = self._octet(value)
        if self._cible(i2c_addr) == "icm":
            self.puce.ecrire_icm(register, value)
        else:
            self.puce.ecrire_ak(register, value)

    def read_i2c_block_data(self, i2c_addr: int, register: int, length: int) -> list:
        lire = self.puce.lire_icm if self._cible(i2c_addr) == "icm" else self.puce.lire_ak
        return [lire(register + k) for k in range(length)]

    def write_i2c_block_data(self, i2c_addr: int, register: int, data) -> None:
        ecrire = self.puce.ecrire_icm if self._cible(i2c_addr) == "icm" else self.puce.ecrire_ak
        for k, v in enumerate(data):
            ecrire(register + k, self._octet(v))

    def close(self) -> None:
        pass
