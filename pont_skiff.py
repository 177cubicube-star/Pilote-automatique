"""pont_skiff.py : pont Pi -> Skiff pour le banc du vérin.

À chaque tour (environ 50 ms) :
  1. mesure le temps RÉELLEMENT écoulé (time.monotonic) ;
  2. fait avancer le vérin simulé (verin_sequence.step_verin) avec la consigne
     qui était active PENDANT cet intervalle ;
  3. relit l'état Skiff, garde toute la structure `control` et ne change que
     `helm` = position ATTEINTE par le vérin / 35 (pas la consigne) ;
  4. demande la nouvelle consigne au programme de manœuvre (consigne_fn) ;
  5. journalise sur la même horloge : consigne du Pi, position du vérin, helm,
     safran Skiff, angle au vent apparent, cap.

Ce que le pont NE décide pas : quand virer, quand débraquer. C'est le rôle de
consigne_fn, fournie par le programme de manœuvre.

Stdlib seulement. Testé contre un faux serveur ; la liaison avec le vrai Skiff
reste à essayer.
"""
from __future__ import annotations

import csv
import json
import math
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable

from verin_sequence import VerinConfig, step_verin

SKIFF_RUDDER_MAX_DEG = 35.0   # rudder_max du Lagoon 450S dans Skiff

# Convention de signe, à UN seul endroit.
# +1 : pos_deg utilise déjà le signe de Skiff (+ = l'étrave vient sur bâbord,
#      essai de Mathieu du 2026-11-23 : +20° -> 21,5° sur bâbord en 3 s).
# -1 : à utiliser si le capteur physique du vérin a le signe inverse.
SIGNE_VERS_SKIFF = +1

COLONNES = ["t_pi_s", "dt_s", "cmd_deg", "pos_deg", "helm", "rudder_deg_skiff",
            "awa_deg", "heading_true_deg", "skiff_elapsed_s", "barre_ecrasee"]


class PilotageRefuse(RuntimeError):
    """Le pont ne peut pas (ou plus) commander la barre : l'essai serait faux."""


def deg_to_helm(pos_deg: float, signe: int = SIGNE_VERS_SKIFF) -> float:
    """Angle du vérin -> helm Skiff (-1..+1). Seul endroit où le signe change."""
    if signe not in (1, -1):
        raise ValueError("signe doit valoir +1 ou -1")
    if not math.isfinite(pos_deg):
        raise ValueError(f"pos_deg doit être fini (reçu {pos_deg!r})")
    return max(-1.0, min(1.0, signe * pos_deg / SKIFF_RUDDER_MAX_DEG))


def helm_to_deg(rudder_deg: float, signe: int = SIGNE_VERS_SKIFF) -> float:
    """Angle de safran Skiff -> convention du vérin (inverse de deg_to_helm)."""
    return signe * rudder_deg


class SkiffClient:
    def __init__(self, base_url: str = "http://127.0.0.1:18081", timeout_s: float = 1.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _req(self, method: str, path: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base_url + path, data=data, method=method,
                                     headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            return json.loads(r.read().decode())

    def get_state(self) -> dict:
        return self._req("GET", "/v1/sim/state")

    def release_course(self) -> dict:
        # Corps {} exactement : libère le cap interne (et le forçage moteur).
        # {"track_hold": false} seul NE libère PAS le cap.
        return self._req("POST", "/v1/sim/course", {})

    def post_control(self, control: dict) -> dict:
        return self._req("POST", "/v1/sim/control", control)


def _verifier_barre_libre(state: dict) -> None:
    if state.get("ap_heading_deg") is not None:
        raise PilotageRefuse(
            f"maintien de cap Skiff engagé ({state['ap_heading_deg']}°) : il a priorité sur helm")
    if state.get("route_guidance") is not None:
        raise PilotageRefuse(
            "route OpenCPN/Signal K active : prioritaire sur helm. La désactiver dans "
            "OpenCPN (Skiff la lâche 15 s après la dernière mise à jour)")


def prendre_la_barre(client: SkiffClient) -> dict:
    """Libère le cap interne et vérifie que rien n'a priorité sur helm."""
    state = client.release_course()
    _verifier_barre_libre(state)
    return state


ConsigneFn = Callable[[float, dict, float], float]   # (t_pi_s, état Skiff, pos_deg) -> cmd_deg


@dataclass
class Pont:
    client: SkiffClient
    cfg: VerinConfig
    consigne_fn: ConsigneFn
    signe: int = SIGNE_VERS_SKIFF
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    tol_helm: float = 1e-6

    def __post_init__(self):
        self.rows: list[dict] = []
        self._t0 = self._last = None
        self._pos = self._cmd = None
        self._helm_envoye = None

    def demarrer(self) -> None:
        state = prendre_la_barre(self.client)
        self._t0 = self._last = self.clock()
        # Le vérin part de l'angle actuel du safran Skiff : pas de saut au départ.
        self._pos = max(self.cfg.angle_min_deg,
                        min(self.cfg.angle_max_deg, helm_to_deg(state["rudder_deg"], self.signe)))
        self._cmd = self.consigne_fn(0.0, state, self._pos)

    def tick(self) -> dict:
        if self._t0 is None:
            raise RuntimeError("appeler demarrer() d'abord")
        now = self.clock()
        dt = now - self._last
        self._last = now
        # L'intervalle écoulé appartient encore à l'ANCIENNE consigne.
        # dt peut valoir 0 si l'horloge a une résolution grossière : le vérin
        # n'a alors pas eu le temps de bouger.
        if dt > 0:
            self._pos, _ = step_verin(self._pos, self._cmd, self.cfg, dt_s=dt)

        state = self.client.get_state()
        _verifier_barre_libre(state)
        ecrasee = (self._helm_envoye is not None
                   and abs(state["control"]["helm"] - self._helm_envoye) > self.tol_helm)

        control = dict(state["control"])            # garde voile, moteurs, masse...
        helm = deg_to_helm(self._pos, self.signe)
        control["helm"] = helm
        state = self.client.post_control(control)
        self._helm_envoye = helm

        t = now - self._t0
        row = {"t_pi_s": t, "dt_s": dt, "cmd_deg": self._cmd, "pos_deg": self._pos,
               "helm": helm, "rudder_deg_skiff": state.get("rudder_deg"),
               "awa_deg": state.get("awa_deg"), "heading_true_deg": state.get("heading_true_deg"),
               "skiff_elapsed_s": state.get("elapsed_s"), "barre_ecrasee": int(ecrasee)}
        self.rows.append(row)
        # Nouvelle consigne, pour l'intervalle SUIVANT.
        self._cmd = self.consigne_fn(t, state, self._pos)
        return row

    def run(self, duree_s: float, periode_s: float = 0.05) -> list[dict]:
        if not (math.isfinite(duree_s) and duree_s > 0 and math.isfinite(periode_s) and periode_s > 0):
            raise ValueError("duree_s et periode_s doivent être finis et > 0")
        self.demarrer()
        prochain = self._t0
        while self.clock() - self._t0 < duree_s:
            prochain += periode_s
            self.sleep(max(0.0, prochain - self.clock()))
            self.tick()
        return self.rows

    def ecrire_csv(self, chemin: str) -> None:
        with open(chemin, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLONNES)
            w.writeheader()
            w.writerows(self.rows)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Banc Pi -> vérin simulé -> Skiff (démo)")
    ap.add_argument("--url", default="http://127.0.0.1:18081")
    ap.add_argument("--cible", type=float, default=20.0, help="angle de barre (°), signe Skiff")
    ap.add_argument("--tenue", type=float, default=4.0, help="temps à la cible avant retour à 0 (s)")
    ap.add_argument("--duree", type=float, default=8.0, help="durée totale (s)")
    ap.add_argument("--csv", default="essai_pont.csv")
    a = ap.parse_args()

    # DÉMO seulement : consigne fixe puis retour à 0. La vraie décision (débraquer
    # quand l'étrave a passé le vent) appartient au programme de manœuvre.
    def consigne_demo(t, state, pos):
        return a.cible if t < a.tenue else 0.0

    pont = Pont(SkiffClient(a.url), VerinConfig(), consigne_demo)
    rows = pont.run(a.duree)
    pont.ecrire_csv(a.csv)
    n_ecr = sum(r["barre_ecrasee"] for r in rows)
    print(f"{len(rows)} lignes -> {a.csv}")
    if n_ecr:
        print(f"ATTENTION : barre réécrite par un tiers {n_ecr} fois (cockpit ouvert ?)")
