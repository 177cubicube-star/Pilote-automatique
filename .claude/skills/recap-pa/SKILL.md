---
name: recap-pa
version: 1.0.0
description: Clôture de session du projet Pilote automatique — produit le document de continuité depuis les faits git (HEAD mesuré, rien d'inventé, VALIDÉ seulement sur accord), aperçu puis « oui » avant écriture, met à jour le TODO, affiche les gestes de clôture. À lancer sur « recap », « fin de session », « clôturer », ou quand un travail est interrompu.
---

# recap-pa — clôture de session (Pilote automatique)

> Instancié depuis le gabarit `rituel-session` v1.1.1 — maison
> `claude-skills` @ `2627422`. Les blocs 🔒 FOND ne s'éditent pas ici :
> une amélioration du fond se fait dans le gabarit, puis se reporte.

<!-- 🔒 FOND:role -->
**Rôle** : produire en fin de session un document de continuité **honnête**,
qui permet à la session suivante de reprendre sans relire la conversation.
Un recap faux est pire que pas de recap : il induit la session suivante en
erreur. D'où quatre règles qui ne se négocient pas :

- les faits viennent de git et du dépôt, pas de la mémoire de la conversation ;
- rien d'inventé, et **VALIDÉ** seulement si l'utilisateur l'a dit dans cette
  session ;
- rien n'est écrit sans aperçu **et** un « oui » explicite ;
- rien n'est commité.
<!-- /FOND:role -->

<!-- ✏️ FORME:config -->
## Forme du projet

| Paramètre | Valeur pour Pilote automatique |
|---|---|
| Référence distante | `origin/main` |
| Fuseau du poste | `America/Toronto` |
| Template de continuité | `sessions/CONTINUITE-SESSION-TEMPLATE.md` |
| Dossier des recaps | `sessions/` |
| Nommage | `recap-YYYYMMDD-NN.md` |
| TODO | `aucun` |
| ADR | dossier `aucun` · ligne de statut `aucun` |
| Pages de fil | `aucun` · gabarit `aucun` |
| Seuil de relecture | `aucun` |
| Archives | TODO → `aucun` · fils → `aucun` |
| Fichiers « code » (gate code/docs) | `aucun` — mesuré : le dépôt ne contient que `.md`/`.json`/`.gitignore`, aucune extension de code à ce jour |
| Compter les tests | `aucun` |
| Marqueurs de dette | `aucun` |
| Vue de la structure | `git --no-optional-locks ls-files \| sort` |
| Scripts testés du projet (remplacent la procédure en ligne) | NN libre : `aucun` · statuts ADR : `aucun` · audit des claims : `aucun` |
| Grille de triage des décisions | pointeur `aucun` |
| Rapport externe (Notion…) | pointeur vers la procédure `aucun` |
| Gestes de clôture | pointeur vers leur source d'autorité `~/.claude/CLAUDE.md` § R202 (git — niveaux d'approbation par risque) |

Règle de remplissage : un **pointeur**, jamais une copie, pour toute règle qui
vit ailleurs (procédure de merge, grille, rapport). Une règle recopiée perd sa
condition de levée.
<!-- /FORME:config -->

<!-- 🔒 FOND:regles-transverses -->
## Règles transverses (valent à chaque étape)

- **Lecture git sans verrou.** Toute commande git de lecture se lance en
  `git --no-optional-locks …`. Depuis le pont Cowork, un `git status` nu laisse
  un `.git/index.lock` que le pont ne sait pas retirer, et la commande git
  suivante du poste échoue.
- **Écriture git : jamais depuis ce skill.** Ni add, ni commit, ni push.
- **Le script d'abord.** Si la forme déclare un script testé pour une étape,
  on l'invoque tel quel et on insère sa sortie **verbatim**. On ne refait jamais
  sa logique de tête. Sinon, on applique la procédure en ligne ci-dessous, qui
  est une garde **par vigilance, non calibrée**.
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
- **Un module à `aucun` est sauté**, et on le dit en une ligne dans l'aperçu.
<!-- /FOND:regles-transverses -->

<!-- 🔒 FOND:etape-1 -->
## Étape 1 — Localiser et nommer

1. Lire le template en entier, sans le modifier. S'il est absent : **arrêter**
   et nommer le chemin.
2. Rafraîchir la référence : `git fetch origin`. En cas d'échec (le 403 du
   proxy en VM est connu), retenter à 2, 4, puis 8 s ; sinon, continuer et
   **déclarer** dans l'aperçu que tout ce qui suit est calculé contre une réf
   possiblement périmée.
3. **Ancre** : le champ `HEAD : \`sha\`` du dernier recap **présent sur la
   réf** (`git ls-tree --name-only <ref> -- <sessions>`). Sans recap, ou sans
   champ, prendre les 15 derniers commits et le dire.
4. **NN du jour, lu sur la réf** : NN = max(NN existants de la date mesurée) + 1,
   sans jamais combler un trou. Si un script NN est déclaré, recopier son NN
   verbatim. Refaire ce calcul juste avant d'écrire le fichier : une session
   parallèle a pu en créer un entre-temps.
<!-- /FOND:etape-1 -->

<!-- 🔒 FOND:etape-2 -->
## Étape 2 — Collecter

**2a. État git (toujours exécuté)**

```bash
git --no-optional-locks branch --show-current
git --no-optional-locks rev-parse --short <ref>        # → le HEAD à écrire dans le recap
git --no-optional-locks log --oneline <ancre>..HEAD
git --no-optional-locks diff --stat <ancre>..HEAD
git --no-optional-locks status --porcelain             # à signaler, jamais toucher
```

**Gate code/docs.** `git diff --stat <ancre>..HEAD -- <fichiers code>`. S'il ne
renvoie rien, c'est une session docs : on saute 2b et on écrit
`[session docs — code inchangé depuis <recap ancre>]`.

**2b. Instantané code.** On lance les commandes déclarées dans la forme.
**Contrôle positif** : un 0 sur un dépôt qui a manifestement des tests met en
cause la commande, pas le dépôt. On l'écrit alors `[0 — commande à vérifier]`,
jamais « 0 test ».

**2c. ADR (si déclarés).** On utilise le script déclaré, sinon on lit la ligne de
statut de chaque ADR du working tree et on donne le prochain numéro libre
(max + 1). Si le dossier n'est pas vide mais qu'aucun statut n'est lu, on écrit
`[convention de statut à vérifier]`, jamais « aucun ADR ».
<!-- /FOND:etape-2 -->

<!-- 🔒 FOND:etape-3 -->
## Étape 3 — Remplir le template

- **Le template fait autorité** sur les sections, les libellés et le vocabulaire.
- **Le bloc d'en-tête est obligatoire, champ `HEAD` compris**, avec le sha
  mesuré en 2a, **jamais recopié** d'un recap précédent. C'est la clé que lit
  `session-prep` à l'ouverture suivante. Sans elle, le détecteur de session non
  recappée devient aveugle, et il l'est en silence.
- Aucune section n'est supprimée. Sans données, on écrit
  `[Aucune donnée disponible cette session]`.
- Rien n'est inventé. En cas de doute, on écrit `[À CONFIRMER]` ou
  `[HYPOTHÈSE]`.

| Statut (si le template n'en impose pas) | Quand |
|---|---|
| **VALIDÉ** | L'utilisateur a dit oui / go / approuvé **dans cette session** |
| **FAIT** | Prouvé par un commit ou constaté dans le dépôt |
| **EN ATTENTE** | Discuté, pas exécuté |
| **À CONFIRMER** | Tout le reste, sans statut intermédiaire |

**Triage des décisions (si une grille est déclarée).** On applique la grille
pointée, sans la recopier. La décision humaine reste toujours à `PENDING` :
la grille propose, l'utilisateur tranche. Ce triage est consultatif et ne bloque
jamais.
<!-- /FOND:etape-3 -->

<!-- 🔒 FOND:etape-4 -->
## Étape 4 — Aperçu, avec contrôle anti-sur-claim

1. Écrire le brouillon dans un fichier temporaire, hors du dépôt.
2. Si un script d'audit est déclaré, on l'invoque et on insère sa shortlist
   verbatim. Sinon, on dresse la **shortlist** des lignes qui portent un verdict
   (FAIT, VALIDÉ, vert, passe, corrigé…) **sans preuve sur la même ligne**
   (sha, chemin, sortie de commande). Pour chacune : preuve présente ailleurs →
   RAS ; enjeu faible → RAS ; sinon → ré-étiqueter la ligne ou dégrader son
   statut **avant** l'aperçu.
3. Afficher le document, la shortlist, les modules sautés et les réserves
   (fetch, date), puis demander :
   `Je sauvegarde dans <sessions>/<nom> ? « oui » ou corrections.`

## Étape 5 — Sauvegarder

Seulement après un « oui » explicite. On écrit le fichier, on signale
`✅ <chemin>`, et **aucun commit**.
<!-- /FOND:etape-4 -->

<!-- 🔒 FOND:etape-6 -->
## Étape 6 — Fil et TODO (seulement s'ils sont déclarés)

**Page de fil.** Identifier le fil touché ; si c'est ambigu, **demander**. On
rafraîchit les sections vivantes définies par le gabarit de fil, on déplace ce
qui n'est plus courant vers l'archive datée et on ne supprime jamais rien.
Montrer avant → après, attendre le « oui », puis écrire.

**TODO.**

- Cocher ce qui est FAIT, avec sa preuve.
- Passer « en cours » ce qui l'est.
- **Ajouter** les prochaines actions et les dettes relevées qui ne sont pas
  encore listées.
- Ne jamais supprimer une ligne, inventer une tâche, ni changer un bloquant
  sans instruction. Un **déplacement vers l'archive**, proposé à l'étape 6b et
  accepté, n'est pas une suppression.
- Mettre à jour la date d'en-tête, mesurée.

Montrer seulement les lignes changées (`[ ] → [x]  <tâche> ← <preuve>`),
attendre le « oui », puis écrire.

**Étape 6b — Mesurer ce qui sera relu (si un seuil est déclaré).** Chaque
clôture écrit, chaque ouverture relit : sans borne, le rituel recrée le
problème qu'il sert à éviter (README du gabarit, § « Contrainte de
conception »).

1. Mesurer `wc -l` du TODO et de chaque page de fil touchée, **après** les
   écritures de l'étape 6. Afficher toujours la ligne
   `📏 Relu à l'ouverture : TODO <N> l. · fil <slug> <N> l. · seuil <S>`,
   même sous le seuil. Une mesure absente se lit « rien à signaler ».
2. Au-delà du seuil, **proposer** l'archivage, sans jamais l'imposer :
   - TODO : déplacer les items `fait`, avec leurs sous-lignes, vers l'archive
     déclarée, sous un en-tête daté ; laisser dans le TODO une ligne
     `Archivé le <date> : <n> items → <archive>` ;
   - fil : déplacer le contenu de sa section d'archive datée vers
     `<archive des fils>/<slug>.md`, et laisser un pointeur.
3. Montrer le mouvement (ce qui part, où il va, les comptes avant et après),
   attendre le « oui », puis écrire. **Contrôle de conservation** : les lignes
   avant = les lignes restantes + les lignes archivées − les lignes de pointeur.
   Un écart signifie qu'on arrête et qu'on le signale.
4. Archives `aucun` alors que le seuil est dépassé → le signaler dans
   l'aperçu, sans rien déplacer.

**Rapport externe (si déclaré).** Suivre la procédure pointée. Outil
indisponible → le dire en une ligne, sans bloquer.
<!-- /FOND:etape-6 -->

<!-- 🔒 FOND:etape-7 -->
## Étape 7 — Gestes de clôture (dernier écran, aucune écriture)

La branche se lit par `git --no-optional-locks branch --show-current`, jamais
écrite en dur. On affiche les gestes **lus dans leur source d'autorité**
(bloc FORME), résumés fidèlement, en citant la source. En cas de divergence,
la source prime.

```
═══ GESTES DE CLÔTURE ═══
Branche : <branche>
<gestes, source citée>
Rien n'a été commité par ce skill.
```
<!-- /FOND:etape-7 -->

<!-- 🔒 FOND:checklist -->
## Checklist (avant chaque écriture)

- [ ] Date mesurée par un instrument **valide** (décalage ≠ `+0000` si le fuseau
      n'est pas UTC), ou `date NON MESURÉE` déclarée ; cohérente avec le dernier commit
- [ ] Fetch réussi, ou son échec déclaré dans l'aperçu
- [ ] NN calculé sur la réf, juste avant l'écriture
- [ ] Champ `HEAD` présent, avec un sha **mesuré** sur la réf
- [ ] Aucun placeholder oublié ; aucun VALIDÉ sans accord dans la session
- [ ] Shortlist anti-sur-claim traitée et affichée
- [ ] Chaque écriture précédée d'un « oui » ; aucun commit
- [ ] Toutes les lectures git faites en `--no-optional-locks`
- [ ] Ligne 📏 affichée (si seuil déclaré) ; tout archivage proposé, montré, accepté, et son contrôle de conservation passé
<!-- /FOND:checklist -->
