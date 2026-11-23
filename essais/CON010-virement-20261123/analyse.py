"""Juge un virement SailSim (CSV) sur trois critères pris ensemble, et trace un graphique SVG.

Critères (tous requis) :
  1. le vent apparent passe sur l'autre bord et y reste (signe opposé, |awa| >= 20° à la fin) ;
  2. le cap entre à ±5° de la cible et y reste jusqu'à la fin ;
  3. la vitesse avant u (axe du bateau, PAS la vitesse sur l'eau) remonte : u final >= 3 m/s.
Usage : python analyse.py fichier.csv [...]  (cible +50°, commande à 30 s : scénario tack_port_to_starboard)
"""
import csv, sys, pathlib

CIBLE, T_CMD = 50.0, 30.0


def charge(f):
    return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(f))]


def juge(rows):
    fin = rows[-1]
    apres = [r for r in rows if r["t"] >= T_CMD]
    awa0 = min(rows, key=lambda r: abs(r["t"] - (T_CMD - 0.5)))["aw_angle_deg"]
    c1 = fin["aw_angle_deg"] * awa0 < 0 and abs(fin["aw_angle_deg"]) >= 20
    # première entrée à ±5° suivie d'un maintien jusqu'à la fin
    t_stable = None
    for i, r in enumerate(apres):
        if all(abs(x["psi_deg"] - CIBLE) <= 5 for x in apres[i:]):
            t_stable = r["t"]; break
    t_entree = next((r["t"] for r in apres if abs(r["psi_deg"] - CIBLE) <= 5), None)
    c2 = t_stable is not None
    c3 = fin["u"] >= 3.0
    return {
        "vent_autre_bord": c1, "cap_tenu": c2, "u_remonte": c3, "REUSSI": c1 and c2 and c3,
        "entree_5deg_s_apres_cmd": None if t_entree is None else round(t_entree - T_CMD, 2),
        "stable_5deg_s_apres_cmd": None if t_stable is None else round(t_stable - T_CMD, 2),
        "cap_final": round(fin["psi_deg"], 1), "u_min": round(min(r["u"] for r in apres), 2),
        "u_final": round(fin["u"], 2), "barre_max": round(max(abs(r["rudder_deg"]) for r in apres), 1),
        "course_barre_deg": round(sum(abs(b["rudder_deg"] - a["rudder_deg"]) for a, b in zip(apres, apres[1:])), 0),
    }


def svg(rows, titre, out):
    W, H, ml, mr = 900, 620, 60, 20
    pistes = [("cap (°)", "psi_deg", -80, 80, "#1971c2"), ("vent apparent (°)", "aw_angle_deg", -60, 60, "#9c36b5"),
              ("u — vitesse avant (m/s)", "u", -1, 7, "#2f9e44"), ("rotation (°/s)", "r", -8, 8, "#e8590c"),
              ("barre (°)", "rudder_deg", -32, 32, "#e03131")]
    ph = (H - 60) / len(pistes)
    tmax = rows[-1]["t"]
    X = lambda t: ml + (W - ml - mr) * t / tmax
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="white"/><text x="{ml}" y="18" font-size="14">{titre}</text>']
    for k, (nom, col, lo, hi, couleur) in enumerate(pistes):
        y0 = 30 + k * ph
        Y = lambda v: y0 + ph - 8 - (ph - 16) * (min(max(v, lo), hi) - lo) / (hi - lo)
        p.append(f'<rect x="{ml}" y="{y0}" width="{W-ml-mr}" height="{ph-4}" fill="none" stroke="#ced4da"/>')
        p.append(f'<line x1="{ml}" x2="{W-mr}" y1="{Y(0)}" y2="{Y(0)}" stroke="#dee2e6"/>')
        if col == "psi_deg":
            p.append(f'<line x1="{ml}" x2="{W-mr}" y1="{Y(CIBLE)}" y2="{Y(CIBLE)}" stroke="#1971c2" stroke-dasharray="4 3"/>')
        if col == "aw_angle_deg":
            for s in (-20, 20):
                p.append(f'<line x1="{ml}" x2="{W-mr}" y1="{Y(s)}" y2="{Y(s)}" stroke="#adb5bd" stroke-dasharray="2 3"/>')
        f = (lambda r: r[col] * 57.2958) if col == "r" else (lambda r: r[col])
        pts = " ".join(f"{X(r['t']):.1f},{Y(f(r)):.1f}" for r in rows[::4])
        p.append(f'<polyline points="{pts}" fill="none" stroke="{couleur}" stroke-width="1.6"/>')
        p.append(f'<text x="{ml+6}" y="{y0+14}" fill="{couleur}">{nom}</text>')
        p.append(f'<text x="{ml-6}" y="{Y(hi)+4}" text-anchor="end" fill="#868e96">{hi}</text>')
        p.append(f'<text x="{ml-6}" y="{Y(lo)+4}" text-anchor="end" fill="#868e96">{lo}</text>')
    p.append(f'<line x1="{X(T_CMD)}" x2="{X(T_CMD)}" y1="30" y2="{H-30}" stroke="black" stroke-dasharray="5 3"/>')
    p.append(f'<text x="{X(T_CMD)+4}" y="{H-16}">commande du virement (30 s)</text>')
    for t in range(0, int(tmax) + 1, 20):
        p.append(f'<text x="{X(t)}" y="{H-4}" text-anchor="middle" fill="#868e96">{t} s</text>')
    p.append("</svg>")
    pathlib.Path(out).write_text("\n".join(p), encoding="utf-8")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        rows = charge(f)
        res = juge(rows)
        svg(rows, f"{pathlib.Path(f).stem} — {'RÉUSSI' if res['REUSSI'] else 'ÉCHEC'} (SIMULÉ)", pathlib.Path(f).with_suffix(".svg"))
        print(pathlib.Path(f).name, res)
