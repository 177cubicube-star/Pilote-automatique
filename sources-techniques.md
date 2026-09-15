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
| 57 | Raymarine ST4000+ — Owner's Handbook (doc. 81131-6) | PDF (manuel constructeur) | https://busse-yachtshop.de/pdf/rayST4000plus_mk2.pdf | 2026-09-13 | Analysée |
| 58 | Simrad TP10/TP22/TP32 — User Guide (2012) | PDF (manuel constructeur) | https://www.troppo.co.uk/odds/Simrad%20TP10-22-32%20User%20Manual%202012.pdf | 2026-09-13 | Analysée |
| 59 | Raymarine ST1000+/ST2000+ — page produit | Page web (constructeur) | https://www.raymarine.com/en-us/our-products/boat-autopilots/autopilot-packs/st1000-st2000 | 2026-09-13 | Analysée |
| 60 | Raymarine EV-100 Tiller Pilot — page produit | Page web (constructeur) | https://www.raymarine.com/en-us/our-products/boat-autopilots/autopilot-packs/ev-100-tiller-pilot | 2026-09-13 | Analysée |
| 61 | Simrad Tillerpilot TP22 — page produit | Page web (constructeur) | https://www.simrad-yachting.com/en-gb/simrad/type/autopilots/tiller-pilots/tillerpilot-22---simnetnmea/ | 2026-09-13 | Analysée |
| 62 | Vérin Raymarine Q047 (S1/ST4000/SPX-5/EV-100) — fiche technique | Page web (revendeur SVB) | https://www.svb24.com/en/raymarine-s1-tiller-drive-unit.html | 2026-09-13 | Analysée |
| 63 | PCNautic — Raymarine Q047 Replacement (capteur de barre interne, fins de course, cotes mi-course) | Page web (produit) | https://pcnautic.com/en/product/Raymarine-Q047-Replacement | 2026-09-13 | Analysée |
| 64 | Raymarine ST2000+ — fiche technique (course 236 mm) | Page web (revendeur) | https://rowlandsmarine.co.uk/raymarine-st2000-tiller/ | 2026-09-13 | Analysée |
| 65 | Practical Sailor — Tillerpilot Test: Simrad TP10 vs Raymarine ST1000 Plus | Article (banc d'essai + essai en mer) | https://www.practical-sailor.com/systems-propulsion/practical-sailor-reviews-boat-tillerpilots-the-simrad-tp10-and-the-raymarine-st1000-plus/ | 2026-09-13 | Analysée |
| 66 | Ventspleen — Raymarine EV100 Tiller pilot review (journal sur 2 ans) | Blog technique | https://www.ventspleen.com/raymarine-ev100-tiller-pilot-review/ | 2026-09-13 | Analysée |
| 67 | Tiller Pilot problems / Recommendations / Experiences | Forum (YBW) | https://forums.ybw.com/threads/tiller-pilot-problems-recommendations-experiences.402558/ | 2026-09-13 | Analysée |
| 68 | Rant — Raymarine ST1000 Tiller Pilot (goupille, microrupteurs, vernissage) | Forum (YBW) | https://forums.ybw.com/threads/rant-raymarine-st1000-tiller-pilot.510265/ | 2026-09-13 | Analysée |
| 69 | ST2000+ tiller pilot erratic steering (débris bloquant les cardans du compas) | Forum (YBW) | https://forums.ybw.com/threads/st2000-tiller-pilot-erratic-steering.501624/ | 2026-09-13 | Analysée |
| 70 | ST2000 bearing housing failure | Forum (YBW) | https://forums.ybw.com/threads/st2000-bearing-housing-failure.349847/ | 2026-09-13 | Analysée |
| 71 | ST4000+ Tiller Drive (démontage, satellites, roulement de vis) | Forum (YBW) | https://forums.ybw.com/threads/st4000-tiller-drive.285045/ | 2026-09-13 | Analysée |
| 72 | Autopilots for tiller steering (absence d'embrayage, limite ~5 t) | Forum (YBW) | https://forums.ybw.com/threads/autopilots-for-tiller-steering.598614/ | 2026-09-13 | Analysée |
| 73 | Tiller Pilot: Raytheon ST2000 — Repair or replacement unit | Forum (Sailboat Owners) | https://forums.sailboatowners.com/threads/tiller-pilot-raytheon-st2000-repair-or-replacement-unit.1249926008/ | 2026-09-13 | Analysée |
| 74 | Rudder position sensor and Raymarine Evolution EV-100 | Forum (Sailboat Owners) | https://forums.sailboatowners.com/threads/rudder-position-sensor-and-raymarine-evolution-ev-100-autopilot-question.1249932955/ | 2026-09-13 | Analysée |
| 75 | Raymarine EV-100 tiller pilot (EV-100 + vérin Pelagic) | Forum (Sailing Anarchy) | https://forums.sailinganarchy.com/threads/raymarine-ev-100-tiller-pilot.212970/ | 2026-09-13 | Analysée |
| 76 | Tiller pilot options (Jefa, Octopus, embrayage) | Forum (Sailing Anarchy) | https://forums.sailinganarchy.com/threads/tiller-pilot-options.247202/ | 2026-09-13 | Analysée |
| 77 | Repair Raymarine Tiller Pilot Drive (Q047) | Forum (Sailing Anarchy) | https://forums.sailinganarchy.com/threads/repair-raymarine-tiller-pilot-drive-q047.242170/ | 2026-09-13 | Analysée |
| 78 | Open heart surgery: operating on a broken Raymarine ST2000+ (photos internes) | Blog technique | http://taketothesea.us/2013/10/17/open-heart-surgery-repairing-a-broken-raymarine-st2000/ | 2026-09-13 | Analysée |
| 79 | Repairing the Raymarine ST1000+ Tiller Pilot (joint de boîtier, nettoyage de carte) | Blog technique | http://tiki21littlecat.blogspot.com/2020/05/repairing-raymarine-st1000.html | 2026-09-13 | Analysée |
| 80 | EV-100 Auto Pilot Install (course insuffisante sur barre longue) | Forum (MacGregor Sailors) | https://www.macgregorsailors.com/forum/viewtopic.php?p=303169 | 2026-09-13 | Analysée |
| 81 | Windvane Integrated with Tiller Pilot (décalage de 90° du compas interne) | Blog technique | https://boatprojects.blogspot.com/2011/06/windvane-integrated-with-tiller-pilot.html | 2026-09-13 | Analysée |
| 82 | Windpilot — article de Tom Cunliffe (pilote sur servo-pendulaire) | Blog constructeur | https://windpilot.com/blog/en/tec-news/autopilot/tom-cunliffe/ | 2026-09-13 | Analysée |
| 83 | Wind vane / autopilot combination | Forum (YBW) | https://forums.ybw.com/threads/wind-vane-autopilot-combination.16410/ | 2026-09-13 | Analysée |
| 84 | Using a tiller pilot with Hydrovane or other Windvane Steering | Forum (YBW) | https://forums.ybw.com/threads/using-a-tiller-pilot-with-hydrovane-or-other-windvane-steering.68382/ | 2026-09-13 | Analysée |
| 85 | Which Tiller Pilot for a Monitor Windvane? | Forum (SailNet) | https://www.sailnet.com/threads/which-tiller-pilot-for-a-monitor-windvane.63988/ | 2026-09-13 | Analysée |
| 86 | Pilote automatique bateau : comparatif et installation 2026 (NKE, B&G, Pelagic, prix) | Article (marché) | https://cap-nautique.fr/equipement/pilote-automatique-bateau-comparatif-et-installation-2026/ | 2026-09-13 | Analysée |

| 87 | Raymarine ST1000+/ST2000+ — manuel utilisateur | Référence mobilisée (déclarée) | https://www.olaje.com/documentos/ST1000Plus&2000PlusTillerPilot.pdf | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 88 | Raymarine — guide de sélection d’organe de commande | Référence mobilisée (déclarée) | https://www.raymarine.com/en-us/learning/online-guides/selecting-your-raymarine-drive-unit | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 89 | Hy-Pro ML+40 — actionneur électro-hydraulique linéaire | Référence mobilisée (déclarée) | https://www.hypro.co.uk/products/hydraulic-pumps-and-steering/linear-actuators/ml40-marine-autopilot-electro-hydraulic-linear-actuator/ | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 90 | Hy-Pro ML+40-S — version compacte 200 mm | Référence mobilisée (déclarée) | https://www.hypro.co.uk/products/hydraulic-pumps-and-steering/linear-actuators/ml40-compact-marine-autopilot-electro-hydraulic-linear-actuator/ | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 91 | Firgelli — vérin à retour de position | Référence mobilisée (déclarée) | https://www.firgelliauto.com/products/feedback-rod-actuator | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 92 | Soupape de dérivation de vérin de pilote | Référence mobilisée (déclarée) | https://www.sailrace.com/marine-autopilot-secondary-steering-cylinder-unloader-valve/ | 2026-09-13 | Mobilisée dans l’analyse actionneur — périmètre à vérifier |
| 93 | Hy-Pro — gamme des actionneurs linéaires hydrauliques | Piste de recherche | https://www.hypro.co.uk/products/hydraulic-pumps-and-steering/linear-actuators/ | 2026-09-13 | Repérée, non exploitée |
| 94 | Hy-Pro — annonce ML40 compact 200 mm | Piste de recherche | https://www.hypro.co.uk/blog/hypro-news/new-200-mm-ml40-linear-actuator-hy-prodrive/ | 2026-09-13 | Repérée, non exploitée |
| 95 | Raymarine — vérins hydrauliques Type 3 | Piste de recherche | https://www.raymarine.com/en-us/our-products/boat-autopilots/autopilot-drive-units/type-3-hydraulic-linear-drives | 2026-09-13 | Repérée, non exploitée |
| 96 | Attainable Adventure Cruising — choix organe de commande | Piste de recherche | https://www.morganscloud.com/2007/05/19/which-marine-autopilot-drive/ | 2026-09-13 | Repérée, non exploitée |
| 97 | Yachting Monthly — guide d’achat pilote automatique | Piste de recherche | https://www.yachtingmonthly.com/gear/autopilot-buyers-guide-for-sailing-yachts-80927 | 2026-09-13 | Repérée, non exploitée |
| 98 | West Marine — Selecting an Autopilot | Piste de recherche | https://www.westmarine.com/west-advisor/Selecting-an-Autopilot.html | 2026-09-13 | Repérée, non exploitée |
| 99 | Firgelli — collection vérins à retour de position | Piste de recherche | https://www.firgelliauto.com/collections/feedback-actuators | 2026-09-13 | Repérée, non exploitée |
| 100 | Firgelli — collection vérins IP66 | Piste de recherche | https://www.firgelliauto.com/collections/ip66-linear-actuators | 2026-09-13 | Repérée, non exploitée |
| 101 | Actuonix — vérins à retour de position | Piste de recherche | https://www.actuonix.com/feedback-actuators | 2026-09-13 | Repérée, non exploitée |
| 102 | Phoenix’s Flight — pyPilot sur direction hydraulique | Piste de recherche | http://phoenixketch.blogspot.com/2019/01/pypilot-open-source-marine-autopilot.html | 2026-09-13 | Repérée, non exploitée |
| 103 | Klaka — "Why Sailing Yacht Rudders Break" (IJSCT) | Paper technique (calcul analytique) | https://klakamarine.org/wp-content/uploads/2022/04/Klaka-IJSCT-rudder-strength-submitted.pdf | 2026-09-14 | Mobilisée dans la synthèse effort de barre — périmètre à vérifier |
| 104 | Stadler et al. — "A Customised Finn Dinghy Rudder for Optimal Olympic Performance" (Chalmers/ISEA 2020) | CFD (RANS) | https://research.chalmers.se/publication/519544/file/519544_Fulltext.pdf | 2026-09-14 | Mobilisée — donnée qualitative seulement (échelle non comparable) |
| 105 | Miller — "Dynamic Lift Coefficients for Spade Rudders on Yachts" (US Naval Academy 2007) | Essai bassin instrumenté (Carderock) | http://www.cembercikutuphanesi.biz.tr/propeller/appendage/sailing/a542380.pdf | 2026-09-14 | Mobilisée — coefficient dynamique/statique utilisé comme hypothèse |
| 106 | Langan Design Partners — Revue d'ingénierie de l'appareil à gouverner du Bluenose II (2016) | Essai instrumenté réel | https://novascotia.ca/news/docs/2016/03/03/Bluenose-II-Steering-Engineering-Review.pdf | 2026-09-14 | Mobilisée — bateau non comparable en taille, ordre de grandeur seulement |
| 107 | Lin Shijie et al. — 基于力学分析的470级帆船转舵应用研究 (China Sport Science 2017) | CFD (RANS) | https://tykx.xml-journal.net/cn/article/pdf/preview/10.16469/j.css.201712004.pdf | 2026-09-14 | Mobilisée — donnée qualitative seulement (échelle non comparable) |
| 108 | TU Delft — MSc thesis, Keel-Rudder Interaction on a Sailing Yacht (2019) | Mémoire universitaire (bassin + CFD) | https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034 | 2026-09-14 | Mobilisée — donnée qualitative seulement (effet quille/safran) |
| 109 | Smithwick — PhD thesis, Univ. of Southampton (2000) | Thèse (dynamomètre 5 composantes) | https://eprints.soton.ac.uk/467038/1/733097.pdf | 2026-09-14 | Repérée pour la synthèse effort de barre — aucune valeur chiffrée extraite, bateau (Reflex 28) très comparable en taille, à revoir en priorité |
| 110 | Zamora-Rodríguez, Izquierdo-Yerón, Botia Vera — Measurements (CEHINAV, UPM Madrid) | Bassin, dynamomètre 6 composantes | https://oa.upm.es/3687/1/INVE_MEM_2008_56494.pdf | 2026-09-14 | Mobilisée — donnée qualitative seulement (effet quille/safran) |
| 111 | Delefortrie, Van Hoydonck, Eloot — Forces and Torque acting on a Rudder while Manoeuvring (Flanders Hydraulics) | Modèle calibré (bassin, KCS) | https://www.vliz.be/imisdocs/publications/72/372072.pdf | 2026-09-14 | Repérée — modèle général, bateau (porte-conteneurs) non comparable |
| 112 | Practical Sailor — "The Tricked-Out Tillerpilot" | Article (retour d'usage terrain) | https://www.practical-sailor.com/marine-electronics/the-tricked-out-tillerpilot/ | 2026-09-14 | Mobilisée dans la synthèse effort de barre — périmètre à vérifier |
| 113 | Jefa — unité direct drive DD3 (données constructeur) | Fiche constructeur | https://www.jefa.com/steering/products/drives/direct-DD3.htm | 2026-09-14 | Mobilisée — capacité d'offre produit, pas un besoin mesuré |
| 114 | PhysicsForums — "Steering Effort on Sailboat w/ Hydraulic Rudder Control" | Forum (calcul + retour d'expérience) | https://www.physicsforums.com/threads/steering-effort-on-sailboat-w-hydraulic-rudder-control.1000007/ | 2026-09-14 | Mobilisée — couple à l'arbre de roue seulement, non convertible au safran |
| 115 | Foerthmann — "Self-Steering Under Sail" (extrait technique) | Document pratique/technique | https://www.bluemoment.com/downloads/selfsteering.pdf | 2026-09-14 | Mobilisée — capacité d'offre produit, pas un besoin mesuré |
| 116 | Klaka — "Rudder balance" | Article (vulgarisation) | https://klakamarine.org/wp-content/uploads/2022/04/CH-rudders.pdf | 2026-09-14 | Repérée — ordre de grandeur qualitatif seulement |
| 117 | Cruising World — "Rudder Loads on the Modern Cruiser" | Article (ratios de démultiplication) | https://www.cruisingworld.com/how/rudder-loads-modern-cruiser/ | 2026-09-14 | Repérée — principe non applicable à une barre franche directe |
| 118 | Peachment — "Torque Calculation" | Formule constructeur | https://www.peachment.co.uk/torque-calculation/ | 2026-09-14 | Repérée — formule non exploitable en l'état, unités à confirmer |
| 119 | Mahne Kalin, Žagar, Vidmar — Estimation of Forces Acting on a Sailboat Using a Kinematic Sensor (Transactions on Maritime Science 2018) | Étude (modèle NACA 0012 + capteur cinématique) | https://www.toms.com.hr/index.php/toms/article/download/221/233 | 2026-09-14 | Repérée — méthode validée, aucune valeur numérique extraite |
| 120 | Bibliothèque AHRS (Python) — documentation, compensation d'inclinaison | Documentation officielle (projet ouvert) | https://ahrs.readthedocs.io/en/latest/filters/tilt.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 121 | ArduPilot Rover — documentation Sailboat | Documentation officielle (projet ouvert) | https://ardupilot.org/rover/docs/sailboat-home.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 122 | Espressif ESP32-S3 — documentation TWAI/CAN | Documentation constructeur | https://docs.espressif.com/projects/esp-idf/en/v5.5.1/esp32s3/api-reference/peripherals/twai.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 123 | Holybro Pixhawk 6X — spécifications techniques | Documentation constructeur | https://docs.holybro.com/autopilot/pixhawk-6x/technical-specification | 2026-09-14 | Repérée (veille électronique), non analysée |
| 124 | Holybro Pixhawk 6X — page produit | Page produit (constructeur) | https://holybro.com/collections/flight-controllers/products/pixhawk-6x | 2026-09-14 | Repérée (veille électronique), non analysée |
| 125 | Jefa LD100 — dossier éclaté et pièces | Documentation constructeur | https://jefa.com/ftp/steering/products/autopilot_drives/linear_drive_LD100/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 126 | ams OSRAM AS5048A — fiche technique | Fiche technique (PDF) | https://look.ams-osram.com/m/287d7ad97d1ca22e/original/AS5048-DS000298.pdf | 2026-09-14 | Repérée (veille électronique), non analysée |
| 127 | nke — gamme pilote automatique (GyroPilot) | Page produit (constructeur) | https://nke-marine-electronics.fr/instruments-nke/pilote-automatique/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 128 | nke GyroPilot 3 — manuel utilisateur | Manuel constructeur (PDF) | https://nke-marine-electronics.fr/wp-content/uploads/user_manuals/FR/40_Gyropilot_3_um_FR.pdf | 2026-09-14 | Repérée (veille électronique), non analysée |
| 129 | Octopus Drives — FAQ (LAM/LAR) | Page constructeur | https://octopusdrives.com/octopus-faqs/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 130 | Octopus Drives — gamme vérins hydrauliques | Page produit (constructeur) | https://octopusdrives.com/products/hydraulic-linear-drives/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 131 | Octopus Drives — catalogue OCTBRO21 | Catalogue constructeur (PDF) | https://octopusdrives.com/wp-content/uploads/sites/8/2021/07/OCTBRO21_web.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 132 | Pcnautic Bare Tiller Drive — page produit | Page produit (constructeur) | https://pcnautic.com/product/pcnautic-bare-tillerdrive | 2026-09-14 | Repérée (veille transmission), non analysée |
| 133 | pypilot — calculateur (Autopilot Computer) | Documentation officielle (projet ouvert) | https://pypilot.org/autopilot_computer/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 134 | pypilot — contrôleurs moteur | Documentation officielle (projet ouvert) | https://pypilot.org/motor_controllers/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 135 | SBG Systems Ellipse — manuel d'exploitation marine | Manuel constructeur (PDF) | https://support.sbg-systems.com/sc/el/files/latest/29002027/29002034/1/1646663810102/Ellipse+Operating+Handbook+-+Use+In+Marine+Applications.pdf | 2026-09-14 | Repérée (veille électronique), non analysée |
| 136 | Analog Devices ADIS16470 — fiche produit | Page produit (constructeur) | https://www.analog.com/en/products/adis16470.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 137 | B&G NAC-3 — calculateur de pilote automatique | Page produit (constructeur) | https://www.bandg.com/en-sg/bg/type/autopilots/autopilot-computers/nac-3-autopilot-computer/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 138 | B&G NAC-2 — calculateur de pilote automatique | Page produit (constructeur) | https://www.bandg.com/fr-fr/bg/type/pilotes-automatiques/calculateurs-de-pilote-automatique/nac-2-autopilot-computer/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 139 | Espressif ESP32-S3 — présentation | Page produit (constructeur) | https://www.espressif.com/en/node/4978 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 140 | Hy-Pro ML+40 M — actionneur électro-hydraulique | Page produit (constructeur) | https://www.hypro.co.uk/products/hydraulic-pumps-and-steering/linear-actuators/ml40-m-marine-autopilot-electro-hydraulic-linear-actuator/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 141 | igus — vis à billes/lead screws, gamme | Page constructeur | https://www.igus.com/lead-screws | 2026-09-14 | Repérée (veille transmission), non analysée |
| 142 | igus dryspin — réduction de jeu | Page constructeur | https://www.igus.com/lead-screws/news/n22-dryspin-zero-backlash-lead-screw-nut | 2026-09-14 | Repérée (veille transmission), non analysée |
| 143 | igus — écrou E7SRM | Page produit (constructeur) | https://www.igus.com/product/drylin_SD_DST_E7SRM_C | 2026-09-14 | Repérée (veille transmission), non analysée |
| 144 | Jefa LD100 — guide d'installation | Manuel constructeur (PDF) | https://www.jefa.com/ftp/steering/installation-guides/Install-LD100-linear_drive-v1.2.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 145 | Jefa — page produit vérin linéaire LD100 | Page produit (constructeur) | https://www.jefa.com/steering/products/drives/linear.htm | 2026-09-14 | Repérée (veille transmission), non analysée |
| 146 | Lecomble & Schmitt — site fabricant | Site fabricant | https://www.ls-france.com/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 147 | Lecomble & Schmitt — notices et catalogues | Catalogue constructeur | https://www.ls-france.com/notices-catalogues/ | 2026-09-14 | Repérée (veille transmission), non analysée |
| 148 | Madintec — logiciels (MADBrain Élite) | Page constructeur | https://www.madintec.com/logiciels | 2026-09-14 | Repérée (veille électronique), non analysée |
| 149 | Madintec — pilote MADBrain, page produit | Page produit (constructeur) | https://www.madintec.com/produits/pilote-madbrain | 2026-09-14 | Repérée (veille électronique), non analysée |
| 150 | maxon GP 32 C — fiche technique (réducteur planétaire) | Fiche technique (PDF) | https://www.maxongroup.co.uk/medias/sys_master/root/9406824710174/GP-32-C.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 151 | maxon GP 32 S — fiche technique (vis à billes) | Fiche technique (PDF) | https://www.maxongroup.com/medias/sys_master/root/8882791514142/EN-21-426-427-428.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 152 | NMEA — norme NMEA 2000 | Organisme de norme | https://www.nmea.org/nmea-2000.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 153 | NXP S32K344 — carte de référence FRDM | Page produit (constructeur) | https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-A-S32K344 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 154 | NXP i.MX RT1170 — page produit | Page produit (constructeur) | https://www.nxp.com/products/i.MX-RT1170 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 155 | Parker/Oildyne Compact EHA — catalogue | Catalogue constructeur (PDF) | https://www.parker.com/content/dam/Parker-com/Literature/Accumulator---Cooler-Division---Europe/catalogues/actuator/eha/H07-1310UK_Compact_EHA_Linear_Actuators.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 156 | Pololu G2 High-Power Motor Driver 24v21 — page produit | Page produit (constructeur) | https://www.pololu.com/product/2995 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 157 | Raspberry Pi Compute Module 5 — fiche produit | Page produit (constructeur) | https://www.raspberrypi.com/products/compute-module-5/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 158 | Raymarine Type 1 Linear Drive — page produit (de-de) | Page produit (constructeur) | https://www.raymarine.com/de-de/unsere-produkte/autopiloten/autopilot-antriebseinheiten/typ-1-linearantriebseinheit | 2026-09-14 | Repérée (veille transmission), non analysée |
| 159 | Raymarine ST1000/ST2000 — gamme | Page produit (constructeur) | https://www.raymarine.com/en-gb/our-products/boat-autopilots/autopilot-packs/st1000-st2000 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 160 | Raymarine Type 2 Hydraulic Linear Drive — page produit | Page produit (constructeur) | https://www.raymarine.com/en-us/our-products/boat-autopilots/autopilot-drive-units/type-2-hydraulic-linear-drives | 2026-09-14 | Repérée (veille transmission), non analysée |
| 161 | Raymarine — capteur de pilote automatique (fr-fr) | Page produit (constructeur) | https://www.raymarine.com/fr-fr/nos-produits/pilotes-automatiques/capteur-de-pilote-automatique | 2026-09-14 | Repérée (veille électronique), non analysée |
| 162 | SBG Systems Ellipse — gamme | Page produit (constructeur) | https://www.sbg-systems.com/ellipse-series/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 163 | SBG Systems — actualité capteur inertiel | Page constructeur (actualité) | https://www.sbg-systems.com/fr/actualites/capteur-inertiel-de-position-et-mouvement/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 164 | SBG Systems — glossaire, choix de méthode de cap | Page constructeur (glossaire) | https://www.sbg-systems.com/fr/glossary/how-to-choose-best-heading-method/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 165 | SBG Systems Ellipse — whitepaper performance AHRS | Fiche technique (PDF) | https://www.sbg-systems.com/wp-content/uploads/SBG-Ellipse-AHRS-performance-whitepaper.pdf | 2026-09-14 | Repérée (veille électronique), non analysée |
| 166 | Simrad TP32 — page produit | Page produit (constructeur) | https://www.simrad-yachting.com/en-sg/simrad/type/autopilots/tiller-pilots/tp32-tiller-pilot/ | 2026-09-14 | Repérée (veille électronique), non analysée |
| 167 | ST IIS2MDC — magnétomètre, fiche produit | Page produit (constructeur) | https://www.st.com/en/mems-and-sensors/iis2mdc.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 168 | ST ISM330DHCX — IMU, fiche produit | Page produit (constructeur) | https://www.st.com/en/mems-and-sensors/ism330dhcx.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 169 | ST STM32F405RG — fiche produit | Page produit (constructeur) | https://www.st.com/en/microcontrollers-microprocessors/stm32f405rg.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 170 | ST STM32G474RE — fiche produit | Page produit (constructeur) | https://www.st.com/en/microcontrollers-microprocessors/stm32g474re.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 171 | ST STM32H743VI — fiche produit | Page produit (constructeur) | https://www.st.com/en/microcontrollers-microprocessors/stm32h743vi.html | 2026-09-14 | Repérée (veille électronique), non analysée |
| 172 | Thomson — catalogue actionneurs linéaires (Max Jac) | Catalogue constructeur (PDF) | https://www.thomsonlinear.com/downloads/actuators/Linear_Actuators_G_CTEN.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 173 | Thomson Max Jac — brochure | Catalogue constructeur (PDF) | https://www.thomsonlinear.com/downloads/actuators/Max_Jac_bren.pdf | 2026-09-14 | Repérée (veille transmission), non analysée |
| 174 | Thomson Electrak HD — page produit | Page produit (constructeur) | https://www.thomsonlinear.com/en/products/linear-actuators/electrak-hd | 2026-09-14 | Repérée (veille transmission), non analysée |
| 175 | Thomson — vis à glissement vs vis à billes, support technique | Page constructeur (support) | https://www.thomsonlinear.com/en/support/20150127-na | 2026-09-14 | Repérée (veille transmission), non analysée |
| 176 | TI DRV8353 — documentation | Documentation constructeur | https://www.ti.com/lit/gpn/DRV8353 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 177 | TI DRV8701 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/DRV8701 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 178 | TI INA240 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/INA240 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 179 | TI ISO1042 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/ISO1042 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 180 | TI ISO1410 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/ISO1410 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 181 | TI LM5164 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/LM5164 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 182 | TI LM7480 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/LM7480 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 183 | TI TMS320F280049C — fiche produit | Page produit (constructeur) | https://www.ti.com/product/TMS320F280049C | 2026-09-14 | Repérée (veille électronique), non analysée |
| 184 | TI TPS3431 — fiche produit | Page produit (constructeur) | https://www.ti.com/product/TPS3431 | 2026-09-14 | Repérée (veille électronique), non analysée |
| 185 | u-blox ZED-F9H — page produit | Page produit (constructeur) | https://www.u-blox.com/en/product/zed-f9h-module | 2026-09-14 | Repérée (veille électronique), non analysée |
| 186 | u-blox ZED-X20D — page produit | Page produit (constructeur) | https://www.u-blox.com/en/product/zed-x20d-module | 2026-09-14 | Repérée (veille électronique), non analysée |
| 187 | u-blox ZED-X20D — annonce produit | Page constructeur (annonce) | https://www.u-blox.com/en/zed-x20d-all-band-gnss-heading-module | 2026-09-14 | Repérée (veille électronique), non analysée |
| 188 | VectorNav — solutions AHRS | Page produit (constructeur) | https://www.vectornav.com/solutions/ahrs | 2026-09-14 | Repérée (veille électronique), non analysée |
| 189 | Pelagic — FAQ compatibilité (piste vis) | Page constructeur (FAQ) | https://pelagicautopilot.com/pages/faq | 2026-09-14 | Repérée (veille transmission), non analysée |
| 190 | ManualsLib — copie du manuel Simrad AP16 (répertoire tiers) | Répertoire de manuels (tiers) | https://www.manualslib.fr/manual/642458/Simrad-Ap16.html | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 191 | SciSpace — article académique, AHRS sous-marin MEMS | Article académique (PDF) | https://scispace.com/pdf/mems-sensor-based-underwater-ahrs-attitude-and-heading-3gs9ar9cch.pdf | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 192 | MEMS Mag — principes AHRS | Presse spécialisée | https://www.memsmag.com/principles-algorithms-and-implementation-of-attitude-reference-system-ahrs | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 193 | NauticExpo — fiche produit Lars Thrane | Catalogue B2B (agrégateur) | https://www.nauticexpo.com/prod/lars-thrane-s/product-66318-488507.html | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 194 | Comptoir Nautique — fiche Raymarine EV-200 | Revendeur | https://www.comptoirnautique.com/pilote-auto-pour-voilier/2838-raymarine-pilote-automatique-evolution-ev-200-voilier-0723193774298.html | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 195 | Scribd — notice SmartPilot (dépôt tiers) | Document tiers déposé (origine non confirmée) | https://fr.scribd.com/document/856220983/SmartPilot-NOTICE-TradgoogleFR | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 196 | Scribd — Affaires Maritimes, division 222-22 (dépôt tiers) | Document tiers déposé (origine non confirmée) | https://fr.scribd.com/document/632986646/Affaires-Maritimes-division-222-22-2017-0-pdf | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 197 | Wikipédia (fr) — Boussole fluxgate | Encyclopédie générale | https://fr.wikipedia.org/wiki/Boussole_fluxgate | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 198 | Académie de Toulouse — support pédagogique, suivre un cap à la boussole | Institutionnel (pédagogique, PDF) | https://pedagogie.ac-toulouse.fr/sii/system/files/2020-07/Act4-SuivreCAP-Boussole.pdf | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 199 | Voiles et Voiliers (Ouest-France) — capteurs de mouvement pour pilote | Presse spécialisée | https://voilesetvoiliers.ouest-france.fr/equipement-entretien/electronique-embarquee/equipement-des-capteurs-de-mouvement-pour-le-pilote-a-quoi-ca-sert-comment-ca-marche-afafdd18-110e-11ee-be68-0182cf49ad63 | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 200 | Bestech Australia — fiche AHRS-II (distributeur) | Distributeur (fabricant d'origine non confirmé) | https://www.bestech.com.au/wp-content/uploads/AHRS-II-Datasheet.rev1_.5._March2016.pdf | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 201 | Idea Publishers — revue académique NASIJ | Revue académique | https://ideapublishers.org/index.php/nasij/article/download/492/253 | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 202 | Qsense Motion — page fournisseur/article IMU | Site fournisseur (article) | https://qsense-motion.com/fr/capteur-imu/ | 2026-09-14 | Repérée (veille électronique, palier B), non analysée |
| 203 | Forum Arduino — boussole à inclinaison compensée | Forum | https://forum.arduino.cc/t/boussole-a-inclinaison-compensee-et-calibration-memorisee/1147564 | 2026-09-14 | Repérée (veille électronique, palier C), non analysée |
| 204 | GuideNav — blog, guide IMU | Blog | https://guidenav.com/fr/bloguer/le-guide-ultime-des-unites-de-mesure-inertielle-imu-/ | 2026-09-14 | Repérée (veille électronique, palier C), non analysée |
| 205 | GuideNav — blog, centrale inertielle et mesure d'angle | Blog | https://guidenav.com/fr/bloguer/pourquoi-une-centrale-inertielle-ne-peut-pas-mesurer-directement-les-angles/ | 2026-09-14 | Repérée (veille électronique, palier C), non analysée |
| 206 | GT Robotique — article/blog, IMU et applications | Blog | https://gtrobotique.fr/imu-systeme-mesure-inertielle-transports-applications-scientifiques/ | 2026-09-14 | Repérée (veille électronique, palier C), non analysée |
| 207 | Sam's Blues — page personnelle, instruments de navigation | Page personnelle | http://samsblues.free.fr/Navigation/instruments.html | 2026-09-14 | Repérée (veille électronique, palier C), non analysée |

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

**Lot « pilotes de barre franche externes » du 2026-09-13 (n° 57 à 86)** — contrairement
aux lots précédents, ces sources n'ont pas été déposées telles quelles par Mathieu : elles
ont été identifiées lors d'une recherche documentaire sur les pilotes externes du commerce
(Raymarine ST1000+/ST2000+, ST4000+, EV-100 Tiller T70153, Simrad TP10/TP22/TP32) et ont
été exploitées immédiatement dans une fiche de synthèse — d'où le statut `Analysée` dès
l'enregistrement. La provenance est notée ici pour que le registre reste honnête sur
l'origine des entrées.

Le lot comprend deux manuels constructeurs complets (ST4000+ et Simrad TP), qui constituent
la source d'autorité pour les spécifications, la géométrie d'installation et les schémas de
câblage ; un banc d'essai indépendant (Practical Sailor) pour les valeurs de poussée, de
courant et de temps butée à butée ; et une majorité de fils de forum et de blogs, qui sont
la seule source documentant les modes de défaillance réels et les modifications apportées
par les utilisateurs.

La source n° 63 (PCNautic — Raymarine Q047 Replacement) est une page produit du site déjà
indexé en n° 56 ; elle est indexée séparément parce qu'elle porte l'information technique
la plus dense du site (cotes mi-course de toutes les marques, capteur de position de barre
interne, contacts de fin de course).

Fiche de synthèse issue de ce lot : `pilotes-barre-franche-externes-etat-de-l-art.md`.


**Lot actionneur — références et pistes transmises par Mathieu** : n° 87 à 92, déclarées mobilisées dans l’analyse actionneur ; n° 93 à 102, uniquement repérées, sans donnée extraite pour cette analyse. L’enregistrement ne constitue ni une consultation ni une validation du contenu. Les titres et URLs sont conservés comme données de collecte. Les six premières figuraient déjà dans la file locale « Sources à enregistrer », mais pas dans ce registre.

**Lot forces sur barre franche et safran — cas documentés, transmis par Mathieu** : n° 103 à 119. Chiffres déjà extraits par Mathieu lors de la capture (14/09/2026) ; ce dépôt ne constitue pas une revérification indépendante ligne par ligne de chaque document. Synthèse comparative issue de ce lot, avec conversions d'unités et hypothèses de recoupement explicitement signalées : `Efforts et couples à la barre franche — synthèse des cas documentés.md` (vault Obsidian).

**Lot électronique — palier A (fabricant/officiel), transmis par Mathieu** : n° 120 à 189, 70 entrées. Issues de deux veilles (calculateur/capteurs/puissance électronique, et transmission d'actionneur vis/hydraulique) déposées le 14/09/2026. Vérification de doublons faite par URL contre ce registre avant ajout ; quatre références des mêmes veilles étaient déjà indexées (n° 32, 38, 60, 90) et ne sont pas dupliquées ici. Une référence (n° 189, FAQ Pelagic) avait été omise par erreur lors du premier ajout ; corrigée le jour même. Les paliers B (tiers documentés) et C (forums/blogs) des mêmes veilles restent non indexés, voir `Lot électronique — références et pistes.md` (vault Obsidian). Liens non ouverts lors de cette collecte ; aucun contenu validé par cet enregistrement.

**Lot électronique — paliers B et C (tiers documentés, forums/blogs), transmis par Mathieu** : n° 190 à 207, 18 entrées (13 palier B, 5 palier C). Issues de la synthèse Perplexity répondant à Q-009 (capteurs et cap), déposée le 14/09/2026. Nature des sources très inégale — presse spécialisée, académique, revendeur, répertoire de manuels tiers pour le palier B ; forums et blogs personnels pour le palier C. Voir `Lot électronique — références et pistes.md` (vault Obsidian) pour le détail du tri. Liens non ouverts lors de cette collecte ; aucun contenu validé par cet enregistrement.
