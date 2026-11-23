"""Mesures de l'essai de virement à phases (spécification de Mathieu, 2026-11-23).

Entrées : <tag>.csv (SailSim, temps simulé), <tag>_pypilot.csv et <tag>_journal.json (horloge du script).
Recalage : t_sim = a * t_client + b, trouvé en superposant le cap reçu par pypilot et le cap de SailSim.
Sorties : instant du lit du vent, fin de séquence, alignement sur Hfinal (±5° pendant 5 s) ; erreur de cap et
vitesse de rotation à la fin de la séquence ; part du virement accomplie ; vent apparent final ; u signé.
Usage : python analyse_spec.py spec_phases
"""
import csv, json, sys, pathlib
import analyse

tag = sys.argv[1] if len(sys.argv) > 1 else "spec_phases"
D = pathlib.Path(__file__).parent
sim = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(D / f"{tag}.csv"))]
pp = [r for r in csv.DictReader(open(D / f"{tag}_pypilot.csv")) if r["imu.heading"] not in ("", "False")]
pp = [(float(r["t_client"]), float(r["imu.heading"])) for r in pp]
journal = json.load(open(D / f"{tag}_journal.json", encoding="utf-8"))


def resolv(a):
    return (a + 180) % 360 - 180


dt = sim[1]["t"] - sim[0]["t"]


def cap_sim(t):
    i = int(round((t - sim[0]["t"]) / dt))
    return sim[i]["psi_deg"] if 0 <= i < len(sim) else None


def cout(a, b, pas):
    s, n = 0.0, 0
    for tc, h in pp[::pas]:
        c = cap_sim(a * tc + b)
        if c is not None:
            s += resolv(h - c) ** 2; n += 1
    return s / n if n > len(pp[::pas]) * 0.6 else 1e9


best = min(((cout(a / 1000, b / 10, 10), a / 1000, b / 10) for a in range(800, 1051, 10) for b in range(-150, 51, 5)))
_, a0, b0 = best
best = min(((cout(a0 + da / 1000, b0 + db / 100, 2), a0 + da / 1000, b0 + db / 100)
            for da in range(-10, 11) for db in range(-50, 51, 5)))
rms, A, B = best[0] ** 0.5, best[1], best[2]
T = lambda tc: A * tc + B
ligne = lambda t: min(sim, key=lambda r: abs(r["t"] - t))

ev = {e[1]: e for e in journal if e[1] != "ENVOI"}
res = {"recalage": {"a": A, "b": round(B, 2), "ecart_cap_rms_deg": round(rms, 2)}}
if "TACK" not in ev:
    res["verdict"] = "pas de TACK : " + str(ev.get("ARRÊT"))
    print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit()

tack = ev["TACK"]; t_tack = T(tack[0]); info = tack[2]
H0, Hf = info["H0"], info["Hfinal"]
fin = ev.get("FIN SÉQUENCE") or ev.get("ARRÊT"); t_fin = T(fin[0])
apres = [r for r in sim if r["t"] >= t_tack]
# lit du vent : le cap traverse la direction du vent vrai (000°)
t_lit = next((r["t"] for r, s in zip(apres, apres[1:]) if r["psi_deg"] < 0 <= s["psi_deg"]), None)
t_awa0 = next((r["t"] for r, s in zip(apres, apres[1:]) if r["aw_angle_deg"] * s["aw_angle_deg"] < 0), None)
t_al = None
for i, r in enumerate(apres):
    if abs(resolv(r["psi_deg"] - Hf)) <= 5:
        w = [x for x in apres[i:] if x["t"] <= r["t"] + 5]
        if w[-1]["t"] >= r["t"] + 4.9 and all(abs(resolv(x["psi_deg"] - Hf)) <= 5 for x in w):
            t_al = r["t"]; break
lf, lfin = ligne(t_fin), sim[-1]
cap_fin = lf["psi_deg"] % 360
part = resolv(cap_fin - H0) / 100.0
res.update({
    "TACK_t_sim": round(t_tack, 2), "H0": round(H0, 1), "Hfinal": round(Hf, 1), "safran0": info["safran0"],
    "lit_du_vent_s_apres_TACK": None if t_lit is None else round(t_lit - t_tack, 2),
    "vent_apparent_passe_0_s_apres_TACK": None if t_awa0 is None else round(t_awa0 - t_tack, 2),
    "fin_sequence_s_apres_TACK": round(t_fin - t_tack, 2), "fin_sequence_motif": fin[1],
    "alignement_Hfinal_s_apres_TACK": None if t_al is None else round(t_al - t_tack, 2),
    "a_la_fin_de_sequence": {"cap": round(cap_fin, 1), "erreur_cap_deg": round(resolv(Hf - cap_fin), 1),
                             "rotation_deg_s": round(lf["r"] * 57.2958, 2), "u_m_s": round(lf["u"], 2),
                             "vent_apparent": round(lf["aw_angle_deg"], 1),
                             "part_du_virement_accomplie_pct": round(100 * part)},
    "final": {"cap": round(lfin["psi_deg"] % 360, 1), "vent_apparent": round(lfin["aw_angle_deg"], 1),
              "u_m_s_signe": round(lfin["u"], 2), "u_min_apres_TACK": round(min(r["u"] for r in apres), 2)},
})
res["REUSSI"] = (t_al is not None and lfin["u"] >= 3.0 and lfin["aw_angle_deg"] * ligne(t_tack - 0.5)["aw_angle_deg"] < 0)
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open(D / f"{tag}_mesures.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# Graphique : même tracé que analyse.py, trait vertical au TACK, cible Hfinal (en ±180)
analyse.T_CMD, analyse.CIBLE = t_tack, resolv(Hf)
analyse.svg(sim, f"{tag} — {'RÉUSSI' if res['REUSSI'] else 'ÉCHEC'} (SIMULÉ)", D / f"{tag}.svg")
