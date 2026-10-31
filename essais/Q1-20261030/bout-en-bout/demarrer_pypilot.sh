#!/usr/bin/env bash
# Démarre le vrai pypilot (fdff88f, environnement /tmp/pp311) en arrière-plan et attend son port JSON.
cd /tmp
nohup /tmp/pp311/bin/pypilot > /tmp/pypilot_run.log 2>&1 &
echo $! > /tmp/pypilot.pid
for i in $(seq 1 30); do
  if python3 -c "import socket; socket.create_connection(('localhost',23322),1).close()" 2>/dev/null; then
    echo "pypilot écoute sur 23322 après ${i}s (pid $(cat /tmp/pypilot.pid))"
    exit 0
  fi
  sleep 1
done
echo "pypilot n'a pas ouvert son port"; tail -20 /tmp/pypilot_run.log; exit 1
