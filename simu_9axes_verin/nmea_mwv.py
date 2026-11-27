"""nmea_mwv.py : lecteur des phrases de vent NMEA 0183 (MWV). Le code qui ira sur le Pi.

Il ne sait pas d'où viennent les lignes : de `girouette_sim.py` au banc, ou d'un
port série (`pyserial`) branché sur la vraie girouette. Il refuse tout ce qui est
douteux plutôt que de deviner : somme de contrôle fausse, champ manquant, statut
`V` (invalide), unité inconnue, angle hors plage.

    recepteur = RecepteurVent(age_max_s=2.0)
    recepteur.ligne("$WIMWV,35.0,R,11.7,N,A*hh", t)
    v = recepteur.vent_valide(t)        # None si trop vieux ou jamais reçu

Unités de sortie : angle en degrés, positif tribord, négatif bâbord (comme
Signal K) ; vitesse en m/s. Stdlib seulement.
"""
from __future__ import annotations

from dataclasses import dataclass

NOEUD = 0.514444
UNITES = {"N": NOEUD, "M": 1.0, "K": 1000.0 / 3600.0}


class ErreurPhrase(ValueError):
    """Ligne refusée (le motif est dans le message)."""


@dataclass(frozen=True)
class MesureVent:
    t: float
    angle_deg: float        # [-180, 180), positif tribord
    vitesse_ms: float
    reference: str          # "R" relatif (apparent) ou "T" vrai


def analyser_mwv(ligne: str, t: float = 0.0) -> MesureVent:
    ligne = ligne.strip()
    if not ligne.startswith("$") or "*" not in ligne:
        raise ErreurPhrase("pas une phrase NMEA")
    corps, _, somme = ligne[1:].partition("*")
    calcul = 0
    for ch in corps:
        calcul ^= ord(ch)
    if len(somme) < 2 or somme[:2].upper() != f"{calcul:02X}":
        raise ErreurPhrase("somme de contrôle fausse")
    champs = corps.split(",")
    if len(champs[0]) != 5 or champs[0][2:] != "MWV":
        raise ErreurPhrase("pas une phrase MWV")
    if len(champs) < 6:
        raise ErreurPhrase("champs manquants")
    angle_txt, reference, vitesse_txt, unite, statut = champs[1:6]
    if statut.upper() != "A":
        raise ErreurPhrase("statut invalide (capteur en défaut)")
    if reference.upper() not in ("R", "T"):
        raise ErreurPhrase("référence inconnue")
    if unite.upper() not in UNITES:
        raise ErreurPhrase("unité de vitesse inconnue")
    try:
        angle = float(angle_txt)
        vitesse = float(vitesse_txt) * UNITES[unite.upper()]
    except ValueError:
        raise ErreurPhrase("nombre illisible") from None
    if not 0.0 <= angle < 360.0 or vitesse < 0:
        raise ErreurPhrase("valeur hors plage")
    signe = angle - 360.0 if angle > 180.0 else angle
    return MesureVent(t, signe, vitesse, reference.upper())


class RecepteurVent:
    """Garde le dernier vent APPARENT valide et sait dire s'il est encore frais."""

    def __init__(self, age_max_s: float = 2.0):
        if age_max_s <= 0:
            raise ValueError("age_max_s doit être > 0")
        self.age_max_s = age_max_s
        self.derniere: MesureVent | None = None
        self.refusees = 0
        self.lues = 0

    def ligne(self, texte: str, t: float) -> MesureVent | None:
        try:
            m = analyser_mwv(texte, t)
        except ErreurPhrase:
            self.refusees += 1
            return None
        if m.reference != "R":
            return None                       # le mode vent apparent n'utilise que R
        self.lues += 1
        self.derniere = m
        return m

    def vent_valide(self, t: float) -> MesureVent | None:
        m = self.derniere
        if m is None or t - m.t > self.age_max_s:
            return None
        return m
