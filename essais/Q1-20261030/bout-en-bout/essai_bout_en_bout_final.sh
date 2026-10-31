#!/usr/bin/env bash
# Essai de bout en bout Q1 : vrai pypilot (fdff88f) + SailSim, scénario pypilot_heading_hold, profil default.
# $1 = étiquette (origine|corrige), $2 = racine du clone SailSim à utiliser.
set -u
label="$1"; clone="$2"
out=/tmp/e2e_final; mkdir -p "$out"
# arrêter un pypilot précédent par son pid (pas de pkill -f, qui viserait ce script)
if [ -f /tmp/pypilot.pid ]; then kill "$(cat /tmp/pypilot.pid)" 2>/dev/null; sleep 3; fi
rm -f ~/.pypilot/pypilot.conf.bak
cp /tmp/sailsim_audit/herostrat_sailsim/docker/pypilot/pypilot_sim.conf ~/.pypilot/pypilot.conf
bash /tmp/q0_scripts/demarrer_pypilot.sh || exit 1
sleep 2
cd "$clone"
PYTHONPATH="$clone/src" timeout 240 /tmp/sailsim_audit/herostrat_sailsim/.venv/bin/python -m sailsim \
  --scenario pypilot_heading_hold --yacht default --autopilot pypilot \
  --output "$out/$label.csv" > "$out/$label.log" 2>&1
echo "[$label] code retour : $?"
grep -E "Result|FAIL|OK\]|Error|error" "$out/$label.log" | head -12
