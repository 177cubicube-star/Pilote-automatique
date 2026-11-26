// Tests de alarme_ecart_cap.js. Lancer depuis ce dossier : node --test test_alarme_ecart_cap.js
// (Node.js 18 ou plus ; celui installé avec Signal K convient.)
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { creerAlarmeEcartCap } = require('./alarme_ecart_cap.js');

const rad = (d) => d * Math.PI / 180;

// Fait avancer le temps par pas de 0,2 s (5 Hz, comme le banc) en publiant cap et consigne.
function rouler(a, debut, fin, cap, consigne) {
  const sorties = [];
  for (let t = debut; t < fin - 1e-9; t += 0.2) {
    const capT = typeof cap === 'function' ? cap(t) : cap;
    if (capT !== null) sorties.push(...a.cap(rad(capT), t));
    sorties.push(...a.consigne(rad(consigne), t));
  }
  return sorties;
}
const ecarts = (s) => s.filter((n) => n.path === 'notifications.steering.autopilot.heading');

test('pas d’alarme sous le seuil', () => {
  const a = creerAlarmeEcartCap();
  assert.deepStrictEqual(rouler(a, 0, 120, 10, 0), []);
});

test('alarme après la temporisation, pas avant', () => {
  const a = creerAlarmeEcartCap();
  assert.deepStrictEqual(rouler(a, 0, 19.8, 30, 0), []);
  const s = rouler(a, 19.8, 21, 30, 0);
  assert.strictEqual(s.length, 1);
  assert.strictEqual(s[0].state, 'alarm');
  assert.deepStrictEqual(s[0].method, ['visual', 'sound']);
  assert.match(s[0].message, /30°/);
});

test('une seule notification par changement d’état', () => {
  const a = creerAlarmeEcartCap();
  assert.strictEqual(ecarts(rouler(a, 0, 100, 30, 0)).length, 1);
});

test('passage par 0° / 360°', () => {
  const a = creerAlarmeEcartCap();
  assert.deepStrictEqual(rouler(a, 0, 60, 355, 5), []);          // 10° d’écart seulement
  assert.strictEqual(ecarts(rouler(a, 60, 100, 330, 5)).length, 1); // 35°
});

test('hystérésis et délai de retour', () => {
  const a = creerAlarmeEcartCap();
  rouler(a, 0, 25, 30, 0);                                        // alarme
  assert.deepStrictEqual(rouler(a, 25, 40, 17, 0), []);           // 17° : entre 15 et 20, reste
  assert.deepStrictEqual(rouler(a, 40, 44.8, 10, 0), []);         // sous 15°, moins de 5 s
  const s = rouler(a, 44.8, 46, 10, 0);
  assert.strictEqual(s.length, 1);
  assert.strictEqual(s[0].state, 'normal');
});

test('une rafale brève ne déclenche pas', () => {
  const a = creerAlarmeEcartCap();
  const cap = (t) => (t % 30 < 10 ? 30 : 0);                     // 10 s hors seuil sur 30
  assert.deepStrictEqual(rouler(a, 0, 300, cap, 0), []);
});

test('manœuvre volontaire : pas d’alarme pendant un grand changement de cap', () => {
  const a = creerAlarmeEcartCap();
  rouler(a, 0, 10, 0, 0);
  const cap = (t) => Math.min(90, (t - 10) * 1.0);                // vire à 1 °/s vers 90°
  assert.deepStrictEqual(rouler(a, 10, 110, cap, 90), []);
});

test('manœuvre : l’inhibition a une durée maximale', () => {
  const a = creerAlarmeEcartCap({ manoeuvre_max_s: 60 });
  rouler(a, 0, 10, 0, 0);
  const s = rouler(a, 10, 100, 0, 90);                            // ne vire jamais
  assert.strictEqual(ecarts(s).length, 1);
  assert.ok(s[0].message.includes('90°'));
});

test('cap absent : alarme distincte, puis retour', () => {
  const a = creerAlarmeEcartCap();
  rouler(a, 0, 10, 0, 0);
  const s = rouler(a, 10, 20, null, 0);                           // la consigne continue
  assert.strictEqual(s.length, 1);
  assert.strictEqual(s[0].path, 'notifications.navigation.headingMagnetic');
  assert.strictEqual(s[0].state, 'alarm');
  const r = rouler(a, 20, 21, 0, 0);
  assert.strictEqual(r[0].state, 'normal');
});

test('tout se tait ensemble : pas d’alarme « cap absent »', () => {
  const a = creerAlarmeEcartCap();
  rouler(a, 0, 10, 0, 0);
  const s = [];
  for (let t = 10; t < 20; t += 0.5) s.push(...a.tic(t));
  assert.deepStrictEqual(s.filter((n) => n.path === 'notifications.navigation.headingMagnetic'), []);
});

test('cap jamais reçu alors que la consigne arrive : alarme « cap absent »', () => {
  const a = creerAlarmeEcartCap();
  const s = rouler(a, 0, 5, null, 0);
  assert.strictEqual(s.length, 1);
  assert.strictEqual(s[0].path, 'notifications.navigation.headingMagnetic');
});

test('sans consigne récente, rien ne sonne et l’alarme se lève', () => {
  const a = creerAlarmeEcartCap();
  rouler(a, 0, 25, 30, 0);
  const s = a.tic(31);                                            // consigne vieille de 6 s
  assert.strictEqual(ecarts(s).length, 1);
  assert.strictEqual(s[0].state, 'normal');
  assert.deepStrictEqual(a.tic(40), []);
});

test('pilote déclaré désengagé', () => {
  const a = creerAlarmeEcartCap();
  a.engage(false, 0);
  assert.deepStrictEqual(rouler(a, 0, 60, 40, 0), []);
});

test('réglages invalides refusés', () => {
  assert.throws(() => creerAlarmeEcartCap({ seuil_deg: -1 }));
  assert.throws(() => creerAlarmeEcartCap({ seuil_deg: 5, hysteresis_deg: 5 }));
  assert.throws(() => creerAlarmeEcartCap({ temporisation_s: NaN }));
});
