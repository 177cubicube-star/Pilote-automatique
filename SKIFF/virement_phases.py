"""virement_phases.py : virement à phases de Mathieu (virement_spec.py, SailSim) transposé à Skiff.

Spécification reprise de essais/CON010-virement-20261123/virement_spec.py (2026-11-23) :
  - phases (angle du côté du virage, vitesse °/s, maintien s) ; angle négatif = contre-barre ;
  - chaque phase part de la position réelle du vérin ;
  - le maintien démarre quand l'angle est atteint à ±tol_angle_deg, ou après t_atteinte_s
    (« NON ATTEINT », on maintient quand même, comme dans virement_spec.py) ;
  - séquence limitée à duree_max_s ; au-delà : secours = reprise du cap sur Hfinal ;
  - fin de séquence : reprise de la tenue de cap sur Hfinal.

Différences avec le banc SailSim (choix de transposition, à valider) :
  - La reprise n'est pas pypilot : c'est une tenue de cap proportionnelle qui passe
    PAR LE VÉRIN SIMULÉ (même loi que le maintien de cap de Skiff : 0,06 de helm par
    degré, soit 2,1° de barre par degré d'erreur). La vitesse du vérin compte donc
    aussi pendant la reprise.
  - La vitesse de chaque phase règle la rampe de la CONSIGNE ; le vérin reste limité
    par sa propre vitesse maximale (VerinConfig.max_speed_dps). C'est la variable A/B.
  - ProgrammeVirementPhases est une consigne_fn pour pont_skiff.Pont : il ne parle
    jamais à Skiff lui-même.

Signes : angle « du côté du virage » -> signe Skiff par vers_signe_skiff(), seul endroit.
Virage à tribord (départ tribord amures) : sens_virage = +1 -> barre Skiff négative.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from pont_skiff import awa_vient_de

KP_REPRISE_DEG_PAR_DEG = 0.06 * 35.0     # loi du maintien de cap de Skiff (HEADING_KP x rudder_max)


def norm180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def vers_signe_skiff(angle_cote_virage: float, sens_virage: int) -> float:
    """Angle « du côté du virage » -> angle de barre en signe Skiff.
    Skiff : barre négative = l'étrave vient sur tribord (essai du 2026-11-23)."""
    if sens_virage not in (1, -1):
        raise ValueError("sens_virage doit valoir +1 (tribord) ou -1 (bâbord)")
    return -sens_virage * angle_cote_virage


@dataclass(frozen=True)
class Phase:
    angle_deg: float      # côté du virage ; négatif = contre-barre
    vitesse_dps: float
    maintien_s: float

    def __post_init__(self):
        for nom in ("angle_deg", "vitesse_dps", "maintien_s"):
            if not math.isfinite(getattr(self, nom)):
                raise ValueError(f"{nom} doit être fini")
        if self.vitesse_dps <= 0 or self.maintien_s < 0:
            raise ValueError("vitesse_dps doit être > 0 et maintien_s >= 0")


# Phases de l'essai 4 (Mathieu, 2026-11-23) : contre-barre 15°, phase 2 tenue 8 s.
PHASES_ESSAI4 = (Phase(-15, 10, 0.0), Phase(20, 10, 3.0), Phase(25, 5, 8.0),
                 Phase(10, 5, 2.0), Phase(0, 5, 0.0))
# Phases de l'essai 3, pour comparaison.
PHASES_ESSAI3 = (Phase(20, 10, 3.0), Phase(25, 5, 4.0), Phase(10, 5, 2.0), Phase(0, 5, 0.0))


@dataclass
class ProgrammeVirementPhases:
    """consigne_fn(t, state, pos_deg) -> angle de barre demandé (signe Skiff)."""
    phases: tuple[Phase, ...]
    angle_virement_deg: float = 80.0
    sens_virage: int = 1
    tol_angle_deg: float = 1.0
    t_atteinte_s: float = 5.0
    duree_max_s: float = 30.0
    kp_reprise: float = KP_REPRISE_DEG_PAR_DEG
    journal: list = field(default_factory=list)

    def __post_init__(self):
        if not self.phases:
            raise ValueError("au moins une phase")
        vers_signe_skiff(0.0, self.sens_virage)          # valide le sens
        for nom in ("angle_virement_deg", "tol_angle_deg", "t_atteinte_s", "duree_max_s", "kp_reprise"):
            v = getattr(self, nom)
            if not math.isfinite(v) or v <= 0:
                raise ValueError(f"{nom} doit être fini et > 0")
        self.etat = "attente"          # attente -> phases -> reprise
        self.t0 = self.H0 = self.Hfinal = None
        self._i = 0
        self._sous = None              # "atteinte" | "maintien"
        self._cmd = self._t_prec = self._ta = self._tm = None

    def _log(self, t, evt, info=None):
        self.journal.append([round(t, 3), evt, info])

    def _debut_phase(self, t, pos):
        self._sous, self._ta, self._cmd = "atteinte", t, pos   # part de la position réelle

    def _reprise(self, t, motif):
        self.etat = "reprise"
        self._log(t, motif, {"Hfinal": self.Hfinal})

    def __call__(self, t: float, state: dict, pos_deg: float) -> float:
        if self.etat == "attente":                           # ordre TACK
            self.t0, self.H0 = t, state["heading_true_deg"]
            self.Hfinal = (self.H0 + self.sens_virage * self.angle_virement_deg) % 360.0
            self._log(t, "TACK", {"H0": self.H0, "Hfinal": self.Hfinal,
                                  "safran0": state.get("rudder_deg"), "awa": awa_vient_de(state)})
            self.etat, self._i, self._t_prec = "phases", 0, t
            self._debut_phase(t, pos_deg)

        if self.etat == "phases":
            dt = max(0.0, t - self._t_prec)
            self._t_prec = t
            if t - self.t0 > self.duree_max_s:
                self._reprise(t, "ARRÊT durée maximale de séquence")
            else:
                ph = self.phases[self._i]
                cible = vers_signe_skiff(ph.angle_deg, self.sens_virage)
                pas = ph.vitesse_dps * dt
                self._cmd = cible if abs(cible - self._cmd) <= pas else \
                    self._cmd + math.copysign(pas, cible - self._cmd)
                if self._sous == "atteinte":
                    if abs(pos_deg - cible) <= self.tol_angle_deg:
                        self._log(t, "ATTEINT", {"phase": self._i + 1, "pos": pos_deg,
                                                 "en_s": round(t - self._ta, 2)})
                        self._sous, self._tm = "maintien", t
                    elif t - self._ta > self.t_atteinte_s:
                        self._log(t, "NON ATTEINT", {"phase": self._i + 1, "pos": pos_deg})
                        self._sous, self._tm = "maintien", t
                if self._sous == "maintien" and t - self._tm >= ph.maintien_s - 1e-9:
                    self._log(t, "FIN PHASE", {"phase": self._i + 1})
                    self._i += 1
                    if self._i < len(self.phases):
                        self._debut_phase(t, pos_deg)
                    else:
                        self._log(t, "FIN SÉQUENCE", {"chrono_s": round(t - self.t0, 2),
                                                      "cap": state["heading_true_deg"], "pos": pos_deg})
                        self.etat = "reprise"
                if self.etat == "phases":
                    return self._cmd

        # reprise : tenue de cap sur Hfinal, à travers le vérin
        err = norm180(self.Hfinal - state["heading_true_deg"])
        return -self.kp_reprise * err


def mesurer(rows: list[dict], prog: ProgrammeVirementPhases, vent_vient_de_deg: float = 0.0,
            stw_min_reussi_mps: float = 3.0) -> dict:
    """Mêmes mesures que analyse_spec.py, sur le CSV du pont (temps = t_reponse_s)."""
    if prog.t0 is None:
        return {"verdict": "pas de TACK"}
    ev = {e[1].split(" ")[0]: e for e in prog.journal}
    t_tack, H0, Hf = prog.t0, prog.H0, prog.Hfinal
    apres = [r for r in rows if r["t_reponse_s"] >= t_tack]
    avant = [r for r in rows if r["t_reponse_s"] <= t_tack] or rows[:1]

    def croise(f):
        for a, b in zip(apres, apres[1:]):
            va, vb = f(a), f(b)
            if va * vb < 0 and abs(va) < 90 and abs(vb) < 90:
                return round(b["t_reponse_s"] - t_tack, 2)
        return None

    t_lit = croise(lambda r: norm180(r["heading_true_deg"] - vent_vient_de_deg))
    t_awa0 = croise(lambda r: r["awa_vient_de_deg"])
    t_al = None
    for i, r in enumerate(apres):
        if abs(norm180(r["heading_true_deg"] - Hf)) <= 5:
            w = [x for x in apres[i:] if x["t_reponse_s"] <= r["t_reponse_s"] + 5]
            if w[-1]["t_reponse_s"] >= r["t_reponse_s"] + 4.9 and \
                    all(abs(norm180(x["heading_true_deg"] - Hf)) <= 5 for x in w):
                t_al = round(r["t_reponse_s"] - t_tack, 2)
                break

    fin = ev.get("FIN") or ev.get("ARRÊT")
    t_fin = fin[0] if fin else apres[-1]["t_reponse_s"]
    i_f = min(range(len(apres)), key=lambda i: abs(apres[i]["t_reponse_s"] - t_fin))
    lf, lfin = apres[i_f], apres[-1]
    j = max(0, i_f - 10)
    rot = norm180(lf["heading_true_deg"] - apres[j]["heading_true_deg"]) / \
        max(1e-9, lf["t_reponse_s"] - apres[j]["t_reponse_s"])
    part = prog.sens_virage * norm180(lf["heading_true_deg"] - H0) / prog.angle_virement_deg
    awa0 = avant[-1]["awa_vient_de_deg"]
    res = {
        "H0": round(H0, 1), "Hfinal": round(Hf, 1),
        "lit_du_vent_s_apres_TACK": t_lit, "vent_apparent_passe_0_s_apres_TACK": t_awa0,
        "fin_sequence_s_apres_TACK": round(t_fin - t_tack, 2),
        "fin_sequence_motif": fin[1] if fin else "fin d'essai",
        "alignement_Hfinal_s_apres_TACK": t_al,
        "a_la_fin_de_sequence": {
            "cap": round(lf["heading_true_deg"] % 360, 1),
            "erreur_cap_deg": round(norm180(Hf - lf["heading_true_deg"]), 1),
            "rotation_deg_s": round(rot, 2), "stw_m_s": round(lf["stw_mps"], 2),
            "vent_apparent": round(lf["awa_vient_de_deg"], 1),
            "part_du_virement_accomplie_pct": round(100 * part)},
        "final": {"cap": round(lfin["heading_true_deg"] % 360, 1),
                  "vent_apparent": round(lfin["awa_vient_de_deg"], 1),
                  "stw_m_s": round(lfin["stw_mps"], 2),
                  "stw_min_apres_TACK": round(min(r["stw_mps"] for r in apres), 2)},
    }
    res["REUSSI"] = (t_al is not None and lfin["stw_mps"] >= stw_min_reussi_mps
                     and lfin["awa_vient_de_deg"] * awa0 < 0)
    return res
