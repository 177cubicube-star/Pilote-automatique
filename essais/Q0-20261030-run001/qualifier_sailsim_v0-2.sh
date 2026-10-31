#!/usr/bin/env bash
# Qualification Q0, SIL physique SailSim, version 0.2. Lancer dans un clone herostrat/sailsim.
# Ne teste NI l'intégration PyPilot, NI Fenix, NI le véritable Capri 22.
set -uo pipefail
if [[ ! -f pyproject.toml || ! -f configs/scenarios/calm_heading_hold.toml ]]; then
  echo 'ERREUR: exécuter à la racine du clone herostrat/sailsim' >&2
  exit 2
fi
HERE="$(pwd)"
BASE="$HERE/resultats/qualification_q0_v02"
mkdir -p "$BASE"
REPORT="$BASE/status.tsv"
printf 'test\tcode_retour\tobservation\n' > "$REPORT"
{ echo "date_utc=$(date -u +%FT%TZ)"; echo "git_sha=$(git rev-parse HEAD 2>/dev/null || echo inconnu)"; git status --short; python3 --version; } > "$BASE/environnement.txt" 2>&1
python3 -m venv .venv || { echo 'Impossible de créer venv'; exit 2; }
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install -e '.[dev]' > "$BASE/installation.log" 2>&1 || { echo -e 'installation\t2\tvoir installation.log' >> "$REPORT"; exit 2; }
run_case() {
  local name="$1"; shift
  "$@" > "$BASE/${name}.log" 2>&1
  local rc=$?
  local note='execution_et_qualite_a_examiner'
  if [[ "$name" == 'pytest_sans_docker' || "$name" == 'physique_statique' ]]; then note='tests_a_examiner'; fi
  printf '%s\t%s\t%s\n' "$name" "$rc" "$note" >> "$REPORT"
  echo "$name : code=$rc"
}
run_case pytest_sans_docker python -m pytest -q tests/unit tests/integration
run_case physique_statique python -m pytest -q tests/integration/test_simulator_physics.py
run_case j24_a sailsim --scenario calm_heading_hold --yacht j24 --autopilot nomoto --output "$BASE/j24_a.csv"
run_case j24_b sailsim --scenario calm_heading_hold --yacht j24 --autopilot nomoto --output "$BASE/j24_b.csv"
if [[ -f "$BASE/j24_a.csv" && -f "$BASE/j24_b.csv" ]]; then
  if cmp -s "$BASE/j24_a.csv" "$BASE/j24_b.csv"; then
    printf 'comparaison_csv\t0\tidentiques_octet_pour_octet\n' >> "$REPORT"
  else
    printf 'comparaison_csv\t1\tdifferents_analyser_tolerance_et_graines\n' >> "$REPORT"
  fi
else
  printf 'comparaison_csv\t2\tindisponible_sorties_absentes\n' >> "$REPORT"
fi
cat > "$BASE/AVERTISSEMENT.txt" <<'TXT'
Ce script lance Q0, mais ne certifie pas les performances d'un autopilote.
Un code retour 1 du CLI SailSim peut signifier une porte qualité échouée,
non un plantage. Consulter tous les logs. Les tests Q0-05 (convergence
dt) et Q0-06/Q0-07 (scénarios physiques additionnels) restent à réaliser.
TXT
printf '\nRésultats : %s\n' "$BASE"
