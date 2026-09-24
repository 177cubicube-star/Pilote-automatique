---
name: session-prep-pa
version: 1.0.0
description: Ouverture de session du projet Pilote automatique — lecture seule, reconstruit l'état RÉEL sur la référence distante (recaps, ADR, TODO, sync git) et signale ce qui est déjà fait (« ne pas refaire »). À lancer AVANT tout travail sur « où en est-on », « reprendre », « début de session ».
---

# session-prep-pa — ouverture de session (Pilote automatique)

> Instancié depuis le gabarit `rituel-session` v1.1.1 — maison
> `claude-skills` @ `2627422`. Les blocs 🔒 FOND ne s'éditent pas ici.

<!-- 🔒 FOND:role -->
**Rôle** : répondre à « où en est-on **maintenant** ? », et non à « où en
était-on à la dernière session ? ». Chaque session part de son propre contexte
et ne voit pas ce que les autres ont poussé. Sans cette vérification, on refait
un ADR, une PR ou une fonctionnalité déjà mergés. Le **DELTA** sert à attraper
ce cas **avant** que le travail commence.

**Lecture seule, sans exception.** Ce skill n'écrit aucun fichier, ne committe
rien et ne touche ni au working tree ni au stash. Seul `git fetch` est permis :
il met à jour les refs, pas les fichiers. La sortie unique est un briefing à
l'écran.
<!-- /FOND:role -->

<!-- ✏️ FORME:config -->
## Forme du projet

| Paramètre | Valeur pour Pilote automatique |
|---|---|
| Référence distante | `origin/main` |
| Fuseau du poste | `America/Toronto` |
| Dossier des recaps | `sessions/` |
| Fichiers de clôture (exclus du comptage de continuité) | `sessions/` (TODO et fils sont `aucun`, rien d'autre à exclure) |
| Branches de travail | `aucun` — mesuré : une seule branche (`main`), aucune convention de préfixe en usage à ce jour |
| ADR | dossier `aucun` · ligne de statut `aucun` |
| TODO | `aucun` · marqueurs `aucun` |
| Règles actives du projet | `README.md` |
| Sections de règles à lire | voir le bloc « Lecture des règles » ci-dessous — **jamais dans ce tableau** : dans une cellule, `\|` y remplace `|`, et la commande copiée n'extrairait rien |
| Pages de fil | `aucun` |
| Scripts testés du projet | gap recap `aucun` · axes de sync `aucun` · ADR sur la réf `aucun` · fils actifs `aucun` · vues dérivées `aucun` |

Lecture des règles (copié tel quel dans la commande de l'étape 5) :

```text
MOTIF   : ^## (La méthode de collecte|Avertissement)
PLAFOND : 60
```

`MOTIF` : expression régulière des titres à lire (ex. `^## (Règle|Langue)`) ou
`aucun`. `PLAFOND` : lignes lues si `MOTIF` vaut `aucun` (ex. `80`).
<!-- /FORME:config -->

<!-- 🔒 FOND:regles-transverses -->
## Règles transverses

- **Toute lecture git se fait en `git --no-optional-locks …`**, pour ne laisser
  aucun verrou orphelin depuis le pont Cowork.
- **Le script d'abord** : un script déclaré s'invoque tel quel, et son verdict
  est inséré verbatim. Les procédures en ligne ci-dessous sont des gardes **par
  vigilance, non calibrées**.
- **La date se mesure, et la mesure se contrôle.** Prendre le premier
  instrument **valide**, dans cet ordre :
  1. `TZ=<fuseau> date '+%Y-%m-%d %H:%M %z'` (Linux, macOS, conteneurs) ;
  2. `powershell.exe -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm zzz'"`
     (Windows, y compris depuis Git Bash ; rend le fuseau du système).
  **Contrôle de validité** : si le fuseau déclaré n'est pas UTC et que le
  décalage rendu vaut `+0000` / `+00:00`, l'instrument est **invalide**. Il a
  ignoré un fuseau qu'il ne connaît pas et il est retombé en UTC **sans erreur
  ni code de sortie** (mesuré sous Git Bash, Windows, le 2026-09-23 : `18:12 +0000`
  pour `14:12 −04:00`). Passer alors à l'instrument suivant. Si aucun n'est
  valide, écrire `date NON MESURÉE`, **jamais** une date supposée. Jamais `date`
  nu ni l'en-tête de session (les conteneurs sont en UTC, donc au lendemain dès 20 h).
  Borne de cohérence : le `%ad` du dernier commit
  (`git log -1 --format=%ad --date=format:'%Y-%m-%d %H:%M %z'`) ne peut pas être
  postérieur à la date mesurée. Ce n'est pas l'heure actuelle.
- **Un verdict INDÉTERMINÉ nomme la précondition qui a manqué.** Un
  « indéterminé » opaque est un détecteur qui se tait sur sa propre panne.
- On collecte tout (étapes 1 à 5) avant d'afficher quoi que ce soit.
<!-- /FOND:regles-transverses -->

<!-- 🔒 FOND:etape-1-2 -->
## Étape 1 — État git réel

```bash
git fetch origin                       # refs seulement ; retenter à 2, 4, 8 s ; sinon DÉCLARER « réf possiblement périmée »
git --no-optional-locks branch --show-current
git --no-optional-locks log --oneline -15 <ref>
git --no-optional-locks branch -a --list "<branches de travail>"
git --no-optional-locks status --porcelain     # SIGNALER seulement : c'est le travail de l'utilisateur
git --no-optional-locks stash list
```

**Trois axes de synchronisation** (sauf si un script est déclaré) :

| Axe | Mesure | Lecture |
|---|---|---|
| 1 · branche ↔ réf | `rev-list --left-right --count <ref>...HEAD` | contexte : +N à merger, −M de retard |
| 2 · main local ↔ réf | `rev-list --left-right --count <ref>...main` | **ALERTE** si main local porte des commits non poussés ; ⚠️ s'il est en retard |
| 3 · branche ↔ son upstream | `rev-list --count @{u}..HEAD` | **ALERTE** si des commits locaux ne sont pas poussés (session coupée en vol ?) |

Si un opérande manque, on écrit `[axe N non vérifiable — <lequel manque>]`.

## Étape 2 — Recaps, lus sur la référence

Les deux côtés d'une comparaison se lisent **dans le même référentiel**. Lire
les recaps sur le disque et compter les commits sur la réf produirait un faux
`OK` pour un recap jamais poussé.

1. La liste des recaps sur la réf :
   `git ls-tree --name-only <ref> -- <sessions> | sort -V`. Le plus récent, et
   **tous ceux de la même date** (sessions parallèles), se lisent par
   `git show <ref>:<chemin>`.
2. **Verdict de continuité** (sauf si un script est déclaré). On prend le champ
   `HEAD : \`sha\`` du dernier recap sur la réf, puis on compte les commits
   postérieurs **en excluant les fichiers de clôture** (recaps, TODO, fils
   déclarés dans la forme) :
   `git rev-list --count <sha>..<ref> -- . ':(exclude)<sessions>' ':(exclude)<todo>' ':(exclude)<fils>'`.
   Sans cette exclusion, le commit qui dépose le recap, forcément postérieur au
   `HEAD` qu'il grave, rendrait GAP après chaque clôture propre (mesuré sur un
   dépôt jetable). Limite assumée : une session qui n'a touché **que** des
   fichiers de clôture n'est pas détectée.
   - `0` → **OK** ;
   - `> 0` → **GAP** : des commits ont avancé la réf sans recap ;
   - le dernier recap du **disque** est absent de la réf → **RECAP_LOCAL** :
     un recap n'a pas été poussé, le trou est local ;
   - recap sans champ `HEAD` → **INDÉTERMINÉ — recap sans HEAD** (le
     producteur n'a pas écrit la clé) ;
   - sha inconnu de la réf → **INDÉTERMINÉ — sha hors historique** ;
   - aucun recap sur la réf → **INDÉTERMINÉ — aucun recap sur <ref>**.
3. Dans ces recaps, extraire les **candidats du DELTA**, repérés **par le sens**
   et non par numéro de section : ce qui n'est pas fait, seulement proposé, un
   ADR en attente, un point ouvert, une prochaine action.
<!-- /FOND:etape-1-2 -->

<!-- 🔒 FOND:etape-3-5 -->
## Étape 3 — ADR sur la référence (si déclarés)

On utilise le script déclaré, sinon on liste avec
`git ls-tree --name-only <ref> -- <dossier ADR>` et on lit la ligne de statut
de chacun avec `git show <ref>:<fichier>`. On en tire les ADR **Proposés** non
actés et le **prochain numéro libre** (max + 1, sans jamais réutiliser ni
sauter un numéro). Si le dossier n'est pas vide mais qu'aucun statut n'est lu :
`[convention de statut à vérifier]`.

## Étape 4 — TODO (si déclaré)

Un fichier long se tronque **sans le dire**, et une lecture partielle passe
alors pour une lecture complète. On procède donc en trois temps :

```bash
grep -nE '<marqueurs>' "$TODO" | head -3    # 1. mesurer le motif réel du fichier
grep -cE '<toutes classes>' "$TODO"         # 2. CONTRÔLE POSITIF : doit être > 0
grep -nE '<classes ouvertes>' "$TODO"       # 3. à faire + en cours + bloquant, TOUTES
```

Un compte à 0 met en cause l'instrument, pas le fichier. Le tri par priorité
se fait dans le briefing, pas dans le grep.

## Étape 5 — Règles actives, lecture bornée

Le fichier de règles grossit avec le projet ; le lire en entier à chaque
ouverture ferait grossir chaque ouverture avec lui.

1. Mesurer d'abord : `wc -l <fichier de règles>`.
2. **Sections déclarées** → extraire seulement celles-là. Le motif se prend
   **tel quel dans le bloc « Lecture des règles »** de la FORME, jamais dans une
   cellule de tableau. Chaque section va de
   son titre au titre suivant de même niveau :
   ```bash
   awk -v m='<motif>' '/^#+ /{lvl=index($0," ")-1; if(on&&lvl<=L)on=0; if($0~m){on=1;L=lvl}} on' <fichier>
   ```
   **Contrôle positif** : si 0 ligne est extraite alors que le motif est
   déclaré, c'est le motif qui est en cause, pas le fichier. On le dit.
3. **Aucune section déclarée** → lire les `<plafond>` premières lignes, et
   déclarer la lecture partielle.
4. Résumer ce qui change ce qu'on a le droit de faire maintenant : **une ligne
   par interdiction ou obligation active** (« jamais… », « toujours… »), puis
   une ligne au plus pour le reste. On résume, on ne recopie pas. Une seule
   ligne pour neuf sections laisse tomber des interdits en silence (mesuré sur
   la 1re instance, 2026-09-23).
5. La ligne 📖 du briefing porte toujours la mesure :
   `règles : <N> l., lues : <sections … | L premières lignes> (<intégral | partiel>)`.

<!-- /FOND:etape-3-5 -->

<!-- 🔒 FOND:etape-6 -->
## Étape 6 — DELTA recap ↔ réf (la fonction clé, obligatoire)

| Le recap dit… | …et la réf montre | Verdict |
|---|---|---|
| « ADR-X proposé / à acter » | ADR-X **Accepté** | 🛑 NE PAS REFAIRE |
| « créer le fichier F » | F existe | 🛑 NE PAS REFAIRE |
| « prochaine action : Y » | un commit réalise Y | 🛑 NE PAS REFAIRE |
| « tâche Z ouverte » | Z cochée dans le TODO | ⚠️ Probablement fait — vérifier |
| « ADR-X proposé » | absent ou encore Proposé | ✅ Encore à faire |

Règles de jugement :

- **Mieux vaut un faux positif qu'un faux négatif** : un doublon raté coûte
  une PR en conflit, une alerte de trop coûte dix secondes.
- **Un 🛑 cite sa preuve** (sha, fichier, ligne de statut). Sans preuve, le
  verdict descend à ⚠️.
- Les candidats en double entre recaps frères se **dédupliquent** : une ligne,
  avec les recaps sources cités.
- **Aucun delta → on le dit** (« recap ↔ réf cohérents ») : une absence de
  doublon est une information.
- **Vues dérivées** : seulement si des scripts sont déclarés, avec leur rapport
  tel quel. Sinon, on écrit `ⓘ aucune vérif dérivée déclarée`.
<!-- /FOND:etape-6 -->

<!-- 🔒 FOND:etape-7 -->
## Étape 7 — Aiguillage : quelle ancre de reprise ?

Si des pages de fil sont déclarées, on liste les fils non archivés, triés par
dernière activité (`git log -1 --format=%cs -- <fichier>`), et on demande
**« Quel fil reprends-tu ? »**. Options :

- **un fil** : on démarre par sa prochaine action n° 1 ;
- **récent** : on démarre par la première action du dernier recap absente
  du 🛑 ;
- **aucun** : on affiche la vue d'ensemble ;
- **interrompue** (seulement si GAP) : on reconstruit depuis le `HEAD` du
  dernier recap, puis on demande confirmation ;
- **clore l'interrompu** (seulement si l'axe 3 est en ALERTE) : on relit les
  commits non poussés, puis on pose la question de merge, **jamais de merge
  sans GO**.

Sans fils, on propose seulement « récent », « aucun » et les options
conditionnelles. On attend la réponse. Le DELTA, lui, n'est pas ré-ancré : il
porte toujours sur les recaps du jour le plus récent.
<!-- /FOND:etape-7 -->

<!-- 🔒 FOND:briefing -->
## Étape 8 — Briefing (sortie unique, lisible en ~15 s)

```
═══ SESSION-PREP · <projet> · <ref> @<sha> · ancre : <…> ═══
🛑 NE PAS REFAIRE : <item ← preuve> | « rien — recap ↔ réf cohérents »
   ⓘ DELTA basé sur le(s) recap(s) du <date> : <liste>
   🛑 CONTINUITÉ : <OK | GAP | RECAP_LOCAL | INDÉTERMINÉ — précondition manquante>
➡️  DÉMARRER PAR : <selon l'ancre>
❓ Ouvert : [!] … · [~] … · [ ] …
🌿 Branche <x> · vs <ref> +N/−M · main local +K non poussé(s) (si K>0) · branches de travail : …
🧰 Working tree : <propre | N modifs — ne pas toucher> · stash : <vide | N>
📖 Périmètre de lecture : <intégral | partiel — source, ce qui n'a PAS été lu, motif>
🕐 Fetch : <OK | ÉCHEC — réf possiblement périmée> · date mesurée : <AAAA-MM-JJ HH:MM ±zone (instrument) | NON MESURÉE>
📐 Prochain ADR libre : … · Proposés non actés : …
📏 Règles ce cycle : <une ligne par interdiction ou obligation active>
📋 Reprise : <pointeur vers la section de reprise de l'ancre>
════════════════════════════════
```

- **📖 et 🕐 sont obligatoires, même quand tout est vert.** Une ligne absente
  se lit comme « tout va bien ».
- **📋 est un pointeur**, jamais les prompts de reprise recopiés.
- Les lignes sans objet dans ce projet (ADR `aucun`, fils `aucun`) s'omettent,
  sauf 📖 et 🕐.
<!-- /FOND:briefing -->

<!-- 🔒 FOND:checklist -->
## Checklist (avant d'afficher)

- [ ] Fetch tenté ; un échec est déclaré
- [ ] Recaps lus **sur la réf**, y compris les frères du même jour ; verdict de
      continuité rendu, avec la précondition nommée s'il est INDÉTERMINÉ
- [ ] Chaque 🛑 appuyé par une preuve ; le cas « ADR déjà Accepté » vérifié
- [ ] Motif du TODO mesuré, contrôle positif > 0
- [ ] Fichier de règles mesuré, lu par sections ou sous plafond, portée déclarée en 📖
- [ ] Aiguillage présenté, réponse attendue
- [ ] Lignes 📖 et 🕐 présentes
- [ ] Toutes les lectures git en `--no-optional-locks` ; **aucun fichier écrit**
<!-- /FOND:checklist -->
