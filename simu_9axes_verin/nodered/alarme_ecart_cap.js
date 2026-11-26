// alarme_ecart_cap.js : logique de l'alarme d'écart de cap (socle), pour Node-RED.
//
// SOURCE UNIQUE : ce fichier est testé seul (test_alarme_ecart_cap.js) et recopié
// tel quel dans le bloc « fonction » du flux par generer_flux_nodered.py.
// Ne pas modifier le code dans Node-RED : modifier ici, puis régénérer le flux.
//
// Ce que fait l'alarme (PROPOSITION de Claude, 2026-11-26, à valider ; la grille
// des capacités demande « seuil et temporisation réglables ; tenir compte d'une
// manœuvre volontaire ») :
//   - active seulement si le pilote a une consigne récente (et n'est pas déclaré
//     désengagé, si steering.autopilot.engaged est publié) ;
//   - déclenche quand |consigne − cap| dépasse SEUIL pendant TEMPORISATION
//     secondes (référence ST4000+ : plus de 20 s) ;
//   - s'éteint quand l'écart repasse sous SEUIL − HYSTERESIS pendant RETOUR s
//     (pas d'acquittement : DEC-017 ne couvre que les décrochages) ;
//   - manœuvre volontaire : après un changement de consigne d'au moins MANOEUVRE
//     degrés, aucune NOUVELLE alarme ne démarre tant que l'écart n'est pas revenu
//     sous le seuil, au plus MANOEUVRE_MAX s ; une alarme déjà active continue ;
//   - cap absent : la consigne continue d'arriver mais plus le cap, depuis plus de
//     DONNEES_MAX s ; alarme distincte (référence ST4000+ « NO DATA »). Si tout se
//     tait en même temps, c'est la règle « pilote non actif » qui s'applique.
// Il ne commande rien : il publie des notifications Signal K.
//
// Unités en entrée : radians (Signal K). Temps : secondes.

function creerAlarmeEcartCap(reglages) {
  const c = Object.assign({
    seuil_deg: 20,          // HYPOTHÈSE de départ, réglable
    temporisation_s: 20,    // référence ST4000+
    hysteresis_deg: 5,
    retour_s: 5,
    manoeuvre_deg: 5,
    manoeuvre_max_s: 120,
    donnees_max_s: 3,
    consigne_max_s: 5,
    chemin_ecart: 'notifications.steering.autopilot.heading',
    chemin_donnees: 'notifications.navigation.headingMagnetic',
  }, reglages || {});
  for (const k of ['seuil_deg', 'temporisation_s', 'hysteresis_deg', 'retour_s',
                   'manoeuvre_deg', 'manoeuvre_max_s', 'donnees_max_s', 'consigne_max_s']) {
    if (typeof c[k] !== 'number' || !isFinite(c[k]) || c[k] < 0) {
      throw new Error('réglage invalide : ' + k + ' = ' + c[k]);
    }
  }
  if (c.hysteresis_deg >= c.seuil_deg) {
    throw new Error('hysteresis_deg doit être plus petit que seuil_deg');
  }

  const e = {
    cap: null, t_cap: null, consigne: null, t_consigne: null, t_premiere_consigne: null,
    engage: null,
    alarme: false, absence: false, debut_depassement: null, debut_retour: null,
    inhibe_jusqua: null,
  };
  const deg = (r) => r * 180 / Math.PI;
  const ecart = () => ((deg(e.consigne) - deg(e.cap)) % 360 + 540) % 360 - 180;
  const actif = (t) => e.consigne !== null && t - e.t_consigne <= c.consigne_max_s
                       && e.engage !== false;

  function notification(chemin, alarme, message) {
    return { path: chemin, state: alarme ? 'alarm' : 'normal',
             method: alarme ? ['visual', 'sound'] : [], message: message };
  }

  function evaluer(t) {
    const sorties = [];
    if (!actif(t)) {
      e.debut_depassement = e.debut_retour = e.inhibe_jusqua = null;
      if (e.alarme) {
        e.alarme = false;
        sorties.push(notification(c.chemin_ecart, false, 'Pilote non actif : alarme levée'));
      }
      if (e.absence) {
        e.absence = false;
        sorties.push(notification(c.chemin_donnees, false, 'Pilote non actif'));
      }
      return sorties;
    }
    // « cap absent » seulement si la consigne, elle, continue d'arriver : quand tout se
    // tait ensemble (source arrêtée), c'est la règle « pilote non actif » qui s'applique
    const absent = e.cap === null
      ? e.t_consigne - e.t_premiere_consigne > c.donnees_max_s
      : e.t_consigne - e.t_cap > c.donnees_max_s;
    if (absent !== e.absence) {
      e.absence = absent;
      sorties.push(notification(c.chemin_donnees, absent, absent
        ? 'Cap absent depuis plus de ' + c.donnees_max_s + ' s'
        : 'Cap de nouveau reçu'));
    }
    if (absent) {
      return sorties;                    // pas de jugement d'écart sans cap frais
    }
    const err = Math.abs(ecart());
    if (e.inhibe_jusqua !== null && (err <= c.seuil_deg || t >= e.inhibe_jusqua)) {
      e.inhibe_jusqua = null;
    }
    if (!e.alarme) {
      if (err > c.seuil_deg && e.inhibe_jusqua === null) {
        if (e.debut_depassement === null) e.debut_depassement = t;
        if (t - e.debut_depassement >= c.temporisation_s) {
          e.alarme = true;
          e.debut_retour = null;
          sorties.push(notification(c.chemin_ecart, true, 'Écart de cap ' + err.toFixed(0)
            + '° depuis ' + (t - e.debut_depassement).toFixed(0) + ' s'));
        }
      } else {
        e.debut_depassement = null;
      }
    } else if (err < c.seuil_deg - c.hysteresis_deg) {
      if (e.debut_retour === null) e.debut_retour = t;
      if (t - e.debut_retour >= c.retour_s) {
        e.alarme = false;
        e.debut_depassement = null;
        sorties.push(notification(c.chemin_ecart, false, 'Cap retrouvé (écart ' + err.toFixed(0) + '°)'));
      }
    } else {
      e.debut_retour = null;
    }
    return sorties;
  }

  return {
    reglages: c,
    cap(valeur_rad, t) {
      if (typeof valeur_rad !== 'number' || !isFinite(valeur_rad)) return evaluer(t);
      e.cap = valeur_rad; e.t_cap = t;
      return evaluer(t);
    },
    consigne(valeur_rad, t) {
      if (typeof valeur_rad !== 'number' || !isFinite(valeur_rad)) return evaluer(t);
      if (e.consigne !== null) {
        const saut = Math.abs(((deg(valeur_rad) - deg(e.consigne)) % 360 + 540) % 360 - 180);
        if (saut >= c.manoeuvre_deg) {
          e.inhibe_jusqua = t + c.manoeuvre_max_s;
          e.debut_depassement = null;
        }
      }
      if (e.t_premiere_consigne === null) e.t_premiere_consigne = t;
      e.consigne = valeur_rad; e.t_consigne = t;
      return evaluer(t);
    },
    engage(valeur, t) {
      e.engage = valeur === true ? true : valeur === false ? false : null;
      return evaluer(t);
    },
    tic(t) { return evaluer(t); },
    etat() { return Object.assign({}, e); },
  };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { creerAlarmeEcartCap };
}
