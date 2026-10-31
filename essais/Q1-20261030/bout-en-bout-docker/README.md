# Essai de bout en bout sous Docker — poste de Mathieu (2026-10-31)

Exécuté par Mathieu sur son poste Windows (Docker Desktop), avec le correctif `../q1-adaptateur-pypilot-v5.patch` appliqué sur un clone de SailSim `ef1e293` (dossier `C:\Users\mat_g\Documents\sailsim-test`). Analyse et comparaison avec les essais sans Docker : `../README.md`, section « Image Docker construite et correctif v5 ».

## Contenu

| Fichier | Ce que c'est |
|---|---|
| `build-v4.txt` | trace de la première construction de l'image, Dockerfile v4 (pypilot non fixé ; version obtenue vérifiée ensuite : `fdff88f`) |
| `build-v5-et-docker-logs.txt` | reconstruction avec v5, démarrage du conteneur `pp` et `docker logs pp` (écoute UDP `0.0.0.0` 20230 et 20231) |
| `installation-et-essai-ideal.txt` | installation de SailSim sous Windows (Python 3.14.5) et essai 1, vérin idéal |
| `essai-servo.txt` | essai 2, couche servo de pypilot (copie fidèle de la sortie transmise par Mathieu dans la conversation) |
| `e2e_docker_ideal.csv` | télémétrie de l'essai 1 (1201 pas) |
| `e2e_docker_servo.csv` | télémétrie de l'essai 2 (1201 pas) |
| `pypilot_servo.toml` | configuration d'autopilote de l'essai 2 : `configs/autopilots/pypilot.toml` + `pypilot_servo_layer = true` ; à placer dans `configs/autopilots/` de SailSim |

## Contrôles faits à la copie

- Fichiers de `sailsim-test` identiques à ceux de v5 (SHA-256 égales) : `docker/pypilot/sim_imu_patch.py`, `docker/pypilot/sim_servo_patch.py`, `docker/pypilot/Dockerfile`, `src/sailsim/autopilot/pypilot.py`.
- Erreur de cap recalculée sur les CSV par la méthode de l'évaluateur (après 10 s) : idéal moyenne 0,24°, max 1,18° ; couche servo moyenne 1,35°, max 2,76°. Identique à l'affichage de SailSim.

## Rejouer

```powershell
docker build -t sailsim-pypilot:test docker\pypilot
docker run -d --name pp -p 23322:23322 -p 20220:20220 -p 20230:20230/udp -p 20231:20231/udp sailsim-pypilot:test
docker restart pp; Start-Sleep 5
.venv\Scripts\python -m sailsim --scenario pypilot_heading_hold --yacht default --autopilot pypilot --output e2e_docker_ideal.csv
docker restart pp; Start-Sleep 5
.venv\Scripts\python -m sailsim --scenario pypilot_heading_hold --yacht default --autopilot pypilot_servo --output e2e_docker_servo.csv
```

Redémarrer le conteneur avant chaque essai : sinon pypilot garde l'état engagé et la consigne de l'essai précédent.
