# Sources techniques — projet « pilote automatique »

Index des documents techniques déposés par Mathieu pour bâtir la base de
connaissance du projet. Ce fichier ne contient **aucune analyse** : il sert
uniquement de registre des sources, à enrichir au fur et à mesure des dépôts.

## Méthode

Mathieu ratisse volontairement large : les sources sont déposées ici telles
quelles, sans filtrage préalable ni jugement de pertinence. Le tri et
l'extraction des éléments spécifiques au projet se feront **au moment de
l'analyse**, pas au moment du dépôt. Les éléments retenus seront alors
consignés en notes dans son vault Obsidian, qui deviendra la source de
référence du projet.

Ce fichier reste donc volontairement un simple registre chronologique — pas
un tri, pas une évaluation de pertinence.

Quand un dépôt contient du contenu détaillé (specs, câblage, procédures) et
pas seulement un lien, ce contenu est conservé intégralement dans
`sources-brutes/` et référencé ici.

## Objectif du projet

Construire un pilote automatique de barre pour voilier (style Fenix : Arduino
Mega + vérin linéaire + IMU), en visant une conception comparable à un
produit commercial existant : **Pelagic Autopilot** (https://pelagicautopilot.com/),
cité par Mathieu comme référence de ce qu'il cherche à reproduire dans sa
propre conception. **pyPilot** est cité comme l'alternative open-source dont
l'architecture est jugée la plus proche de Pelagic.

## Registre

| # | Source | Type | Lien / emplacement | Date d'ajout | Statut |
|---|--------|------|--------------------|--------------|--------|
| 1 | Fenix — code | Dépôt GitHub | https://github.com/spascual90/Fenix.git | 2026-09-07 | Enregistrée, non analysée |
| 2 | Fenix Autopilot — documentation (racine) | Site GitBook | https://spascual90.gitbook.io/fenix-autopilot | 2026-09-07 | Enregistrée, non analysée |
| 3 | Arduino — site officiel | Site web (racine) | https://www.arduino.cc/ | 2026-09-07 | Enregistrée, non analysée |
| 4 | Fenix Autopilot — site officiel (accueil) | Site web | https://fenix-autopilot.com/ | 2026-09-08 | Enregistrée, non analysée |
| 5 | Fenix Autopilot — Bill of Materials | Page web | https://fenix-autopilot.com/build-of-materials/ | 2026-09-08 | Enregistrée, non analysée |
| 6 | Fenix Autopilot — Guide de construction | Page web | https://fenix-autopilot.com/start-to-build-from-here/ | 2026-09-08 | Enregistrée, non analysée |
| 7 | Fenix Autopilot — Installation app Virtuino | Page web | https://fenix-autopilot.com/install-virtuino-app/ | 2026-09-08 | Enregistrée, non analysée |
| 8 | Fenix Autopilot — Premiers essais en mer | Page web | https://fenix-autopilot.com/perform-first-sea-trials/ | 2026-09-08 | Enregistrée, non analysée |
| 9 | Fenix Autopilot — Mode AUTO | Page GitBook | https://spascual90.gitbook.io/fenix-autopilot/using-fenix-tiller-pilot/using-auto-mode | 2026-09-08 | Enregistrée, non analysée |
| 10 | Fenix Autopilot — Mode TRACK | Page GitBook | https://spascual90.gitbook.io/fenix-autopilot/using-fenix-tiller-pilot/using-track-mode | 2026-09-08 | Enregistrée, non analysée |
| 11 | Fenix Autopilot — Fonctions utilisateur | Page GitBook | https://spascual90.gitbook.io/fenix-autopilot/using-fenix-tiller-pilot/user-functions | 2026-09-08 | Enregistrée, non analysée |
| 12 | Fenix — releases (firmware) | GitHub | https://github.com/spascual90/Fenix/releases | 2026-09-08 | Enregistrée, non analysée |
| 13 | Virtuino for Fenix (app Android) | Dépôt GitHub | https://github.com/spascual90/virtuino-for-fenix | 2026-09-08 | Enregistrée, non analysée |
| 14 | Potentiometer Feedback from a Linear Actuator | Tutoriel (Firgelli) | https://www.firgelliauto.com/en-mx/blogs/tutorials/potentiometer-feedback-from-a-linear-actuator | 2026-09-08 | Enregistrée, non analysée |
| 15 | Arduino Actuator with Feedback | Tutoriel | https://arduinogetstarted.com/tutorials/arduino-actuator-with-feedback | 2026-09-08 | Enregistrée, non analysée |
| 16 | Linear Actuator with Feedback | Tutoriel (Circuits DIY) | https://www.circuits-diy.com/linear-actuator-with-feedback-arduino-tutorial/ | 2026-09-08 | Enregistrée, non analysée |
| 17 | Getting potentiometer feedback from Actuonix | Forum Arduino | https://forum.arduino.cc/t/getting-potentiometer-feedback-from-actuonix-linear-actuator/560509 | 2026-09-08 | Enregistrée, non analysée |
| 18 | Arduino BTS7960 DC Motor Driver | Tutoriel (DeepBlue Embedded) | https://deepbluembedded.com/arduino-bts7960-dc-motor-driver/ | 2026-09-08 | Enregistrée, non analysée |
| 19 | BTS7960 — Example Code | Wiki (DFRobot) | https://wiki.dfrobot.com/dri0018/docs/18926 | 2026-09-08 | Enregistrée, non analysée |
| 20 | How to Connect and Control a BTS7960 | Tutoriel (AIChipLink) | https://aichiplink.com/blog/How-to-Connect-and-Control-a-BTS7960-Motor-Driver-with-Arduino_351 | 2026-09-08 | Enregistrée, non analysée |
| 21 | BTS7960 Motor Driver — datasheet | PDF (HandsonTec) | https://www.handsontec.com/dataspecs/module/BTS7960%20Motor%20Driver.pdf | 2026-09-08 | Enregistrée, non analysée |
| 22 | BTS7960 — tutoriel complet | Tutoriel (RoboJax) | https://robojax.com/tutorial_view.php?id=169&lang=en | 2026-09-08 | Enregistrée, non analysée |
| 23 | YAAAP (Yet Another Arduino AutoPilot) | Dépôt GitHub | https://github.com/FilBip/yaaap | 2026-09-08 | Enregistrée, non analysée |
| 24 | ESP32 WiFi Autopilot | Dépôt GitHub | https://github.com/jeff-burright/Autopilot_ESP32_wifi | 2026-09-08 | Enregistrée, non analysée |
| 25 | Autopilot for Sailing Boats V2 (Marco Zonca) | Arduino Project Hub | https://projecthub.arduino.cc/marcozonca/autopilot-for-sailing-boats-new-version-2-987140 | 2026-09-08 | Enregistrée, non analysée |
| 26 | Autotiller (Daniel's Works) | Blog technique | https://www.danielsworks.com/blog/autotiller | 2026-09-08 | Enregistrée, non analysée |
| 27 | Boat Autopilot | Instructable | https://www.instructables.com/Boat-Autopilot/ | 2026-09-08 | Enregistrée, non analysée |
| 28 | Arduino Boat Autopilot in Progress | Instructable | https://www.instructables.com/Arduino-Boat-Autopilot-in-Progress/ | 2026-09-08 | Enregistrée, non analysée |
| 29 | Autopilot for Sailing Boats V2 (Hackster) | Article (Hackster.io) | https://www.hackster.io/marcozonca/autopilot-for-sailing-boats-new-version-2-251a60 | 2026-09-08 | Enregistrée, non analysée |
| 30 | Arduino Autopilot (fil 2010) | Forum Arduino | https://forum.arduino.cc/t/arduino-autopilot/48764 | 2026-09-08 | Enregistrée, non analysée |
| 31 | Autopilot Tiller Arduino DIY | Wiki OpenCPN | https://opencpn.org/wiki/dokuwiki/doku.php?id=opencpn:supplementary_hardware:autopilot-arduino | 2026-09-08 | Enregistrée, non analysée |
| 32 | Pelagic Autopilot — produit commercial de référence | Site web (produit) | https://pelagicautopilot.com/ | 2026-09-08 | Enregistrée, non analysée |
| 33 | Pelagic — manuel utilisateur (Hisse et Oh) | PDF | https://www.hisse-et-oh.com/store/medias/sailing/5ea/b6b/070/original/5eab6b07040dbf2adf435d26.pdf | 2026-09-08 | Enregistrée, non analysée |
| 34 | Pelagic — manuel d'installation/utilisateur | PDF | https://marine-electronics-manuals.com/maxabcpdf/pil_pel/pil_pel4.pdf | 2026-09-08 | Enregistrée, non analysée |
| 35 | Pelagic — manuels (site officiel) | Page web | https://pelagicautopilot.com/collections/manuals | 2026-09-08 | Enregistrée, non analysée |
| 36 | Pelagic — manuel Scanmar International | Page (ManualsLib) | https://www.manualslib.com/manual/2998315/Scanmar-International-Pelagic-Autopilot.html | 2026-09-08 | Enregistrée, non analysée |
| 37 | Pelagic Autopilot review | Article (Veloce Sailing) | https://velocesailing.se/2021/07/17/pelagic-autopilot/ | 2026-09-08 | Enregistrée, non analysée |
| 38 | pyPilot — manuel utilisateur (HTML) | Documentation officielle | https://pypilot.org/doc/pypilot_user_manual/ | 2026-09-08 | Enregistrée, non analysée |
| 39 | pyPilot — manuel utilisateur (PDF) | PDF | https://pypilot.org/doc/pypilot_user_manual/pdf/pypilot_user_manual.pdf | 2026-09-08 | Enregistrée, non analysée |
| 40 | pyPilot — documentation générale (incl. version FR) | Documentation officielle | https://pypilot.org/doc/ | 2026-09-08 | Enregistrée, non analysée |
| 41 | pyPilot — Workbook | Wiki GitHub | https://github.com/pypilot/workbook/wiki | 2026-09-08 | Enregistrée, non analysée |
| 42 | pyPilot — dépôt principal | Dépôt GitHub | https://github.com/pypilot/pypilot | 2026-09-08 | Enregistrée, non analysée |
| 43 | Open-Boat-Projects — pyPilot | Guide DIY | https://open-boat-projects.org/en/pypilot/ | 2026-09-08 | Enregistrée, non analysée |
| 44 | pyPilot — fil forum allemand (Segeln-Forum) | Forum | https://www.segeln-forum.de/thread/68916-pypilot/?pageNo=1 | 2026-09-08 | Enregistrée, non analysée |
| 45 | pyPilot/TinyPilot — guide complet (AndreasW29) | Wiki GitHub | https://github.com/AndreasW29/pypilot-tinypilot-mysolution-infos/tree/main/guide | 2026-09-08 | Enregistrée, non analysée |
| 46 | Sailing Anne-Mon — DIY autopilot | Blog | http://sailingannemon.com/diy-autopilot-for-sailboat-part-one/ | 2026-09-08 | Enregistrée, non analysée |
| 47 | Club Feeling 1090 — installation pyPilot | Récit d'installation | https://www.clubfeeling1090.fr/barre-safran/pilote-pypilot | 2026-09-08 | Enregistrée, non analysée |
| 48 | Nautinect — Build your own autopilot | Guide DIY (ESP32) | https://www.nautinect.com/buildyourownautopilot | 2026-09-08 | Enregistrée, non analysée |
| 49 | KastB — Boat Autopilot | Dépôt GitHub | https://github.com/KastB/boat_autopilot | 2026-09-08 | Enregistrée, non analysée |
| 50 | DC9 — Homemade Sailboat Autopilot | Page web | http://www.dc9.com/autopilot/autopilot.html | 2026-09-08 | Enregistrée, non analysée |
| 51 | OpenPlotter — pyPilot | Documentation | https://openplotter.readthedocs.io/latest/pypilot/pypilot_app.html | 2026-09-08 | Enregistrée, non analysée |
| 52 | Forum OpenMarine — fil installation pyPilot | Forum | https://forum.openmarine.net/showthread.php?tid=4204 | 2026-09-08 | Enregistrée, non analysée |
| 53 | pyPilot in action | Vidéo (YouTube) | https://youtu.be/IMqUmcTbQOE | 2026-09-08 | Enregistrée, non analysée |
| 54 | Forum OpenMarine (racine) | Forum | https://forum.openmarine.net/ | 2026-09-08 | Enregistrée, non analysée |
| 55 | pyPilot — Issues GitHub | GitHub Issues | https://github.com/pypilot/pypilot/issues | 2026-09-08 | Enregistrée, non analysée |
| 56 | PCNautic — système pyPilot assemblé | Site web (produit) | https://pcnautic.com/ | 2026-09-08 | Enregistrée, non analysée |

## Conventions

- Une ligne par source déposée, dans l'ordre d'arrivée.
- **Statut** : `Enregistrée, non analysée` → `Analysée` (une fiche de synthèse
  existe alors dans le projet, ou les éléments retenus sont passés dans le
  vault Obsidian) → `Écartée` (avec la raison en note).
- Les notes de contexte fournies par Mathieu lors du dépôt sont reprises
  telles quelles sous le tableau, sans reformulation.

## Notes de dépôt

**Fenix — code (n° 1)** — présenté par Mathieu comme « un des multiples documents
techniques » destinés à construire la connaissance du projet.

**Fenix Autopilot — documentation (n° 2)** — déposée comme source suivante, sans
commentaire particulier. Même auteur GitHub (`spascual90`) que la source n° 1.

**Arduino — site officiel (n° 3)** — déposée sans commentaire. Racine du site
plutôt qu'une page précise.

**Lot Fenix Autopilot du 2026-09-08 (n° 4 à 31)** — compilation de liens fournie
en un seul message : documentation officielle du site fenix-autopilot.com,
pages GitBook complémentaires, releases GitHub, app Android Virtuino,
tutoriels sur le vérin linéaire à potentiomètre et le driver moteur BTS7960,
projets similaires (YAAAP, ESP32, Marco Zonca, Autotiller, Instructables),
et fils de forum/wiki connexes. Le message contenait aussi du contenu
détaillé (BoM, câblage, formules, procédures de calibration, points clés) —
conservé intégralement dans
[`sources-brutes/fenix-liens-et-notes-2026-09-08.md`](sources-brutes/fenix-liens-et-notes-2026-09-08.md).
Deux éléments cités dans ce lot n'avaient pas d'URL exploitable (le dépôt
« PCB-for-Fenix » et la section vidéos du site officiel) — notés comme tels
dans ce même fichier plutôt qu'omis silencieusement.

**Pelagic Autopilot (n° 32)** — déposée par Mathieu comme « un produit qui se
vend » et auquel il tente de faire la même conception : il s'agit donc du
produit commercial de référence pour le projet, pas d'une source technique
au même titre que les autres (aucune documentation technique ouverte n'est
présumée disponible sur ce site — à vérifier lors de l'analyse).

**Lot Pelagic & pyPilot du 2026-09-08 (n° 33 à 56)** — compilation de liens
fournie dans la foulée de la source n° 32 : manuels et revue Pelagic,
documentation et dépôt pyPilot (alternative open-source à l'architecture
jugée similaire), guides DIY (Open-Boat-Projects, Sailing Anne-Mon, Club
Feeling 1090, Nautinect en ESP32), projets similaires (KastB, DC9,
OpenPlotter) et ressources complémentaires (vidéo, forums, issues GitHub).
Le message contenait aussi du contenu détaillé (specs Pelagic, dimensions
d'installation tiller, architecture matérielle pyPilot/TinyPilot, câblage
ESP32↔IBT-2 et IMU, calibration, modes de navigation, vitesses de vérin,
alimentation) — conservé intégralement dans
[`sources-brutes/pelagic-pypilot-notes-2026-09-08.md`](sources-brutes/pelagic-pypilot-notes-2026-09-08.md).
Deux points signalés comme incertains dans le texte source y sont notés tels
quels plutôt qu'omis : un lien pyPilot répété (documentation FR / générale,
indexé une seule fois en n° 40) et une référence à PCNautic accompagnée d'une
parenthèse tronquée dans le message d'origine.
