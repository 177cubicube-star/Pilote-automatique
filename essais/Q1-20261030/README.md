# Q1 — Adaptateur pypilot de SailSim : modèle de vérin et coupure sûre (2026-10-30)

**Statut :** correctif **exécuté en tests unitaires** (interfaces simulées), **pas encore exécuté avec le vrai pypilot** (conteneur Docker). Lot Q1 de `Plan_execution_pilote_Capri22_V0-5` (vault).

**Base :** `herostrat/sailsim`, commit `ef1e2930c85423b4f276ff6dabc5ec4ae3ca67c0`. Correctif : `q1-adaptateur-pypilot.patch` (4 fichiers, +117 / −41 lignes). Rien n'a été proposé au dépôt d'origine.

## Ce que le correctif change

| Défaut (EXP-002, qualification V0.2) | Correction |
|---|---|
| QX-1 / Q1-A : `servo.command` était converti directement en angle de safran (`-cmd × rudder_max`) | `servo.command` est traité comme une **demande de vitesse** du vérin, comme dans pypilot (`servo.py` : `do_command(speed)`). La barre avance à `-cmd × rudder_rate_max`, intégrée sur le pas de temps, et s'arrête en butée à `rudder_max` |
| Q1-B : une commande constante imposait un angle constant | Une commande nulle maintient la barre où elle est ; une commande constante la fait avancer progressivement |
| QX-4 / Q1-E : en cas de perte de communication, la dernière commande était gardée sans limite | Après `comm_timeout` secondes de temps simulé sans pypilot, le vérin est arrêté et un **défaut verrouillé** (`fault`) est levé. Il ne se lève qu'avec `reset_fault()` (réarmement explicite) |
| `rudder_rate_max` accepté mais jamais utilisé | Utilisé comme vitesse du vérin ; exposé dans la configuration (`pypilot_rudder_rate_max_deg_s`, défaut 10 °/s) avec `pypilot_comm_timeout_s` (défaut 1 s) |

Les trois tests unitaires qui validaient l'ancien comportement sont remplacés par cinq tests (avance progressive, maintien à commande nulle, butée, coupure au-delà du délai, défaut verrouillé après reconnexion).

## Validation exécutée (2026-10-30)

- `pytest tests/unit tests/integration tests/scenarios` : **312 réussis, 0 échec**.
- Contrôles du CI du dépôt : `ruff check` réussi, `ruff format --check` réussi, `mypy` sans erreur.
- Environnement : Python 3.13.18, conteneur Linux de la session Claude.

## Ce qui reste à faire dans Q1

- **Q1-C / Q1-D, cap IMU** : le conteneur pypilot utilise toujours la route GPS (COG) à la place du cap IMU (`docker/pypilot/apply_patch.py`). Non corrigé ici.
- **Q1-F, horloge** : la synchronisation entre le temps simulé et le temps réel de pypilot n'est pas mesurée.
- **Q1-H, couche servo de pypilot** : impulsions « période / windup » et étalonnage non reproduits. C'est un banc **au niveau contrôleur**, avec un vérin idéal en vitesse.
- **Version de pypilot** : le Dockerfile clone toujours la tête de branche, sans commit figé (QX-5).
- **Essai de bout en bout** : construire l'image Docker et rejouer `pypilot_heading_hold` avec le profil `default`. Docker est disponible dans l'environnement de la session ; l'image n'a pas encore été construite.

## Appliquer le correctif

Dans un clone de `herostrat/sailsim` au commit ci-dessus : `git apply q1-adaptateur-pypilot.patch`.
