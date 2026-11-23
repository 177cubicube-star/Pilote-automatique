"""preparer_essai.py : mettre le Lagoon de Skiff dans le MÊME état avant chaque essai.

Choix retenu par Mathieu (2026-11-23) : départ TRIBORD amures au près, vent du
000°, awa_deg ≈ +40° ; le virement passe par tribord ; cap_final = (cap + 80) % 360.

Étapes de preparer() :
  1. POST /v1/sim/reset avec le cap de départ (le reset efface tout le reste) ;
  2. position en eau libre (facultative, mais Prickly Bay est près de la côte) ;
  3. même vent, même courant, mêmes vagues, avec manual=true ;
  4. mêmes réglages de voile ; le MAINTIEN DE CAP de Skiff tient le cap de départ
     pendant l'établissement (quelqu'un doit barrer) ;
  5. attente : awa, rotation et vitesse sur l'eau stables pendant duree_stable_s ;
  6. retourne l'état au déclenchement (cap, safran, awa, stw, rotation, cap_final).

preparer() ne libère PAS la barre : Pont.demarrer() le fait en envoyant {}.

Angle du vent apparent : toujours via pont_skiff.awa_vient_de(state), car le
awa_deg brut de Skiff est décalé de 180° (mesuré le 2026-11-23).

DetecteurPassageVent : détecte le passage de l'étrave dans le vent, seulement
après avoir été ARMÉ sur l'amure de départ (le zéro d'initialisation de awa_deg
au reset ne peut donc pas le déclencher).

Stdlib seulement. Testé contre un faux serveur ; à essayer sur ton Skiff.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

from pont_skiff import SkiffClient, awa_vient_de

TRIBORD, BABORD = +1, -1   # côté d'où vient le vent au départ (signe de awa_deg)


def norm180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def _fini(nom: str, v: float) -> None:
    if not math.isfinite(v):
        raise ValueError(f"{nom} doit être fini (reçu {v!r})")


@dataclass(frozen=True)
class EssaiConfig:
    """Valeurs par défaut = HYPOTHÈSES à remplacer par tes réglages d'essai.
    Vent et courant suivent la convention « vient de » ici ; la conversion vers
    le « va vers » de Skiff est faite dans preparer()."""
    cap_depart_deg: float = 293.7
    sens_depart: int = TRIBORD
    angle_virement_deg: float = 80.0
    vent_vient_de_deg: float = 0.0
    vent_mps: float = 7.2               # vitesse du reset Skiff
    courant_va_vers_deg: float = 85.0   # courant du reset Skiff (0,55 m/s vers 85°)
    courant_mps: float = 0.55
    vague_m: float = 0.0
    vague_periode_s: float = 7.0
    vague_va_vers_deg: float = 290.0
    sail_trim: float = 0.76
    reef: float = 0.0
    traveler: float = 0.0
    lat_deg: float | None = None        # position en eau libre (facultative)
    lon_deg: float | None = None
    # Critères d'établissement
    awa_cible_deg: float = 40.0
    awa_tol_deg: float = 3.0
    rotation_max_dps: float = 0.5
    stw_min_mps: float = 1.0
    stw_variation_max_mps: float = 0.1  # écart max/min de stw dans la fenêtre
    duree_stable_s: float = 3.0         # temps Skiff (elapsed_s)
    delai_max_s: float = 120.0          # temps réel du Pi
    periode_s: float = 0.1

    def __post_init__(self):
        for nom in ("cap_depart_deg", "angle_virement_deg", "vent_vient_de_deg", "vent_mps",
                    "courant_va_vers_deg", "courant_mps", "vague_m", "vague_periode_s",
                    "vague_va_vers_deg", "sail_trim", "reef", "traveler", "awa_cible_deg",
                    "awa_tol_deg", "rotation_max_dps", "stw_min_mps", "stw_variation_max_mps",
                    "duree_stable_s", "delai_max_s", "periode_s"):
            _fini(nom, getattr(self, nom))
        if self.sens_depart not in (TRIBORD, BABORD):
            raise ValueError("sens_depart doit valoir TRIBORD (+1) ou BABORD (-1)")
        if (self.lat_deg is None) != (self.lon_deg is None):
            raise ValueError("donner lat_deg ET lon_deg, ou aucun des deux")
        if self.lat_deg is not None:
            _fini("lat_deg", self.lat_deg)
            _fini("lon_deg", self.lon_deg)
        if not 0 < self.angle_virement_deg < 180:
            raise ValueError("angle_virement_deg doit être entre 0 et 180")
        for nom in ("awa_tol_deg", "rotation_max_dps", "duree_stable_s", "delai_max_s", "periode_s"):
            if getattr(self, nom) <= 0:
                raise ValueError(f"{nom} doit être > 0")

    @property
    def cap_final_signe(self) -> float:
        """Tribord amures : virement vers tribord (+). Bâbord amures : vers bâbord (−)."""
        return self.sens_depart * self.angle_virement_deg


def angle_symetrique(cap_deg: float, c: "EssaiConfig") -> float:
    """Angle de virement qui mène au près SYMÉTRIQUE de l'autre amure (miroir autour
    de la direction du vent vrai) : Hfinal = 2 x vent - cap. Toujours entre 0 et 180."""
    hf = (2.0 * c.vent_vient_de_deg - cap_deg) % 360.0
    angle = c.sens_depart * norm180(hf - cap_deg)
    if not 0 < angle < 180:
        raise ValueError(f"cap {cap_deg:g}° incompatible avec le côté de départ choisi")
    return angle


class EssaiImpossible(RuntimeError):
    pass


@dataclass(frozen=True)
class Declenchement:
    skiff_elapsed_s: float
    cap_depart_deg: float       # cap MESURÉ au déclenchement
    cap_final_deg: float
    rudder_deg: float
    awa_deg: float              # convention « vient de » (0 = face au vent, + = tribord)
    stw_mps: float
    rotation_dps: float


class SuiviRotation:
    """Vitesse de rotation (°/s, + = vers tribord) à partir de deux caps successifs,
    datés par elapsed_s de Skiff. Gère le passage 359° -> 0°."""
    def __init__(self):
        self._h = self._t = None
        self.valeur: float | None = None

    def maj(self, heading_deg: float, elapsed_s: float) -> float | None:
        if self._t is not None and elapsed_s > self._t:
            self.valeur = norm180(heading_deg - self._h) / (elapsed_s - self._t)
        if self._t is None or elapsed_s > self._t:
            self._h, self._t = heading_deg, elapsed_s
        return self.valeur


def _requete_environnement(c: EssaiConfig) -> dict:
    return {"wind_speed_mps": c.vent_mps,
            "wind_to_deg": (c.vent_vient_de_deg + 180.0) % 360.0,   # Skiff : « va vers »
            "current_speed_mps": c.courant_mps, "current_to_deg": c.courant_va_vers_deg,
            "wave_height_m": c.vague_m, "wave_period_s": c.vague_periode_s,
            "wave_to_deg": c.vague_va_vers_deg, "manual": True}


def preparer(client: SkiffClient, c: EssaiConfig,
             clock: Callable[[], float] = time.monotonic,
             sleep: Callable[[float], None] = time.sleep) -> Declenchement:
    state = client._req("POST", "/v1/sim/reset", {"heading_true_deg": c.cap_depart_deg})
    if c.lat_deg is not None:
        state = client._req("POST", "/v1/sim/position", {"lat_deg": c.lat_deg, "lon_deg": c.lon_deg})
    client._req("POST", "/v1/sim/environment", _requete_environnement(c))
    client._req("POST", "/v1/sim/course", {"heading_true_deg": c.cap_depart_deg, "track_hold": False})
    control = dict(state["control"])
    control.update({"helm": 0.0, "sail_trim": c.sail_trim, "reef": c.reef,
                    "traveler": c.traveler, "thrust_port": 0.0, "thrust_stbd": 0.0})
    client.post_control(control)

    rot = SuiviRotation()
    fenetre: list[tuple[float, float]] = []   # (elapsed_s, stw) depuis que tout est dans la tolérance
    t0 = clock()
    dernier = None
    while clock() - t0 < c.delai_max_s:
        st = client.get_state()
        dernier = st
        if st.get("aground"):
            raise EssaiImpossible("le Lagoon s'est échoué pendant l'établissement : "
                                  "donner lat_deg/lon_deg en eau libre")
        if st.get("route_guidance") is not None:
            raise EssaiImpossible("route OpenCPN active : elle a priorité sur le maintien de cap")
        r = rot.maj(st["heading_true_deg"], st["elapsed_s"])
        awa, stw, t_sk = awa_vient_de(st), st["stw_mps"], st["elapsed_s"]
        ok = (r is not None
              and abs(c.sens_depart * awa - c.awa_cible_deg) <= c.awa_tol_deg
              and abs(r) <= c.rotation_max_dps
              and stw >= c.stw_min_mps)
        if not ok:
            fenetre.clear()
        elif not fenetre or t_sk > fenetre[-1][0]:
            fenetre.append((t_sk, stw))
            stws = [v for _, v in fenetre]
            if max(stws) - min(stws) > c.stw_variation_max_mps:
                fenetre[:] = [(t_sk, stw)]       # vitesse encore en train de changer
            elif t_sk - fenetre[0][0] >= c.duree_stable_s:
                h = st["heading_true_deg"]
                return Declenchement(t_sk, h, (h + c.cap_final_signe) % 360.0,
                                     st["rudder_deg"], awa, stw, r)
        sleep(c.periode_s)

    detail = "aucun état reçu" if dernier is None else (
        f"dernier état : awa {awa_vient_de(dernier):.1f}°, stw {dernier['stw_mps']:.2f} m/s, "
        f"rotation {rot.valeur if rot.valeur is not None else float('nan'):.2f} °/s")
    raise EssaiImpossible(
        f"établissement non atteint en {c.delai_max_s:g} s ({detail}). "
        f"Ajuster cap_depart_deg pour viser awa {c.sens_depart * c.awa_cible_deg:+g}°")


@dataclass
class DetecteurPassageVent:
    """Passage de l'étrave dans le vent = changement de signe de l'angle du vent
    apparent par 0°. À alimenter avec pont_skiff.awa_vient_de(state), JAMAIS avec
    state["awa_deg"] brut (son zéro est le vent arrière).
    1. ARMEMENT : n_armement lectures consécutives de awa du côté de départ, à
       awa_tol_deg de awa_armement_deg. Le zéro du reset n'arme donc pas.
    2. PASSAGE : une fois armé, awa change de signe avec |awa| < awa_max_passage_deg.
       Un changement de signe près de ±180° (empannage) est ignoré."""
    sens_depart: int = TRIBORD
    awa_armement_deg: float = 40.0
    awa_tol_deg: float = 5.0
    n_armement: int = 5
    awa_max_passage_deg: float = 90.0
    arme: bool = field(default=False, init=False)
    passe: bool = field(default=False, init=False)
    t_passage_s: float | None = field(default=None, init=False)
    _compte: int = field(default=0, init=False)

    def __post_init__(self):
        if self.sens_depart not in (TRIBORD, BABORD):
            raise ValueError("sens_depart doit valoir TRIBORD (+1) ou BABORD (-1)")
        if self.n_armement < 1 or self.awa_tol_deg <= 0 or not 0 < self.awa_max_passage_deg < 180:
            raise ValueError("paramètres d'armement ou de passage invalides")

    def maj(self, t_s: float, awa_deg: float) -> bool:
        """Retourne True UNE fois, à la lecture où le passage est détecté."""
        if self.passe or not math.isfinite(awa_deg):
            return False
        cote = self.sens_depart * awa_deg      # > 0 : encore sur l'amure de départ
        if not self.arme:
            if abs(cote - self.awa_armement_deg) <= self.awa_tol_deg:
                self._compte += 1
                self.arme = self._compte >= self.n_armement
            else:
                self._compte = 0
            return False
        if cote < 0 and abs(awa_deg) < self.awa_max_passage_deg:
            self.passe, self.t_passage_s = True, t_s
            return True
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Préparer le Lagoon au près tribord amures")
    ap.add_argument("--url", default="http://127.0.0.1:18081")
    ap.add_argument("--cap", type=float, default=293.7)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    a = ap.parse_args()
    cfg = EssaiConfig(cap_depart_deg=a.cap, lat_deg=a.lat, lon_deg=a.lon)
    d = preparer(SkiffClient(a.url), cfg)
    print(f"déclenché à t_skiff = {d.skiff_elapsed_s:.2f} s : cap {d.cap_depart_deg:.1f}°, "
          f"awa {d.awa_deg:+.1f}°, stw {d.stw_mps:.2f} m/s, rotation {d.rotation_dps:+.2f} °/s, "
          f"safran {d.rudder_deg:+.1f}° -> cap_final {d.cap_final_deg:.1f}°")
    print("Le maintien de cap Skiff est ENCORE engagé : lancer le pont tout de suite "
          "(Pont.demarrer() le libère).")
