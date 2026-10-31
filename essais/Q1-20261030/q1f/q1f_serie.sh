#!/usr/bin/env bash
# Q1-F — série d'exécutions instrumentées. $1 = étiquette (origine|corrige), $2 = clone SailSim, $3 = nombre d'exécutions.
set -u
label="$1"; clone="$2"; n="$3"
out=/tmp/q1f; mkdir -p "$out"
for k in $(seq 1 "$n"); do
  if [ -f /tmp/pypilot.pid ]; then kill "$(cat /tmp/pypilot.pid)" 2>/dev/null; sleep 3; fi
  rm -f ~/.pypilot/pypilot.conf.bak
  cp /tmp/sailsim_audit/herostrat_sailsim/docker/pypilot/pypilot_sim.conf ~/.pypilot/pypilot.conf
  bash /tmp/q0_scripts/demarrer_pypilot.sh > /dev/null || { echo "pypilot n'a pas démarré"; exit 1; }
  sleep 2
  (cd "$clone" && PYTHONPATH="$clone/src" timeout 200 /tmp/sailsim_audit/herostrat_sailsim/.venv/bin/python /tmp/q0_scripts/q1f_run.py "${label}_${k}" "$out" 2>"$out/${label}_${k}.err" | tail -1)
done
if [ -f /tmp/pypilot.pid ]; then kill "$(cat /tmp/pypilot.pid)" 2>/dev/null; fi
