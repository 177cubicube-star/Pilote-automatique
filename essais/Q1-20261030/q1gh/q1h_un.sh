#!/usr/bin/env bash
# Q1-G/H — une exécution : pypilot redémarré avec la conf de simulation, puis q1h_run.py.
# $1 = clone SailSim ; la suite = arguments de q1h_run.py
set -u
clone="$1"; shift
out=/tmp/q1h; mkdir -p "$out"
if [ -f /tmp/pypilot.pid ]; then kill "$(cat /tmp/pypilot.pid)" 2>/dev/null; sleep 3; fi
rm -f ~/.pypilot/pypilot.conf.bak ~/.pypilot/servocalibration
cp /tmp/sailsim_audit/herostrat_sailsim/docker/pypilot/pypilot_sim.conf ~/.pypilot/pypilot.conf
if [ -n "${Q1H_CAL:-}" ]; then echo "$Q1H_CAL" > ~/.pypilot/servocalibration; fi
bash /tmp/q0_scripts/demarrer_pypilot.sh > /dev/null || { echo "pypilot n'a pas démarré"; exit 1; }
sleep 2
cd "$clone" && PYTHONPATH="$clone/src" timeout 300 /tmp/sailsim_audit/herostrat_sailsim/.venv/bin/python /tmp/q0_scripts/q1h_run.py --out "$out" "$@" 2>"$out/derniere.err" | tail -1
