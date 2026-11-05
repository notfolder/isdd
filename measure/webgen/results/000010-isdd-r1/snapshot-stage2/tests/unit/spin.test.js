import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openDatabase, seedInitialData, listWinningsByName } from '../../src/db.js';
import { validatePlayerName, pickWeightedPrize, performSpin } from '../../src/spin.js';

test('validatePlayerName accepts 1 to 30 characters after trimming', () => {
  assert.deepEqual(validatePlayerName('  Alice  '), { ok: true, name: 'Alice' });
  assert.equal(validatePlayerName('a').ok, true);
  assert.equal(validatePlayerName('x'.repeat(30)).ok, true);
});

test('validatePlayerName rejects empty, blank, too long and non-string names', () => {
  const message = 'Please enter your name (1-30 characters).';
  assert.deepEqual(validatePlayerName(''), { ok: false, error: message });
  assert.deepEqual(validatePlayerName('   '), { ok: false, error: message });
  assert.deepEqual(validatePlayerName('x'.repeat(31)), { ok: false, error: message });
  assert.deepEqual(validatePlayerName(undefined), { ok: false, error: message });
  assert.deepEqual(validatePlayerName(42), { ok: false, error: message });
});

test('pickWeightedPrize selects by cumulative weight', () => {
  const prizes = [{ name: 'A', weight: 1 }, { name: 'B', weight: 2 }, { name: 'C', weight: 3 }];
  const pickWith = (roll) => pickWeightedPrize(prizes, () => roll).name;
  assert.equal(pickWith(0), 'A');
  assert.equal(pickWith(1), 'B');
  assert.equal(pickWith(2), 'B');
  assert.equal(pickWith(3), 'C');
  assert.equal(pickWith(5), 'C');
});

test('pickWeightedPrize returns null when there are no prizes', () => {
  assert.equal(pickWeightedPrize([], () => 0), null);
});

test('pickWeightedPrize asks for an integer below the total weight', () => {
  const asked = [];
  pickWeightedPrize([{ weight: 4 }, { weight: 6 }], (n) => { asked.push(n); return 0; });
  assert.deepEqual(asked, [10]);
});

test('performSpin records nothing for an invalid name', () => {
  const db = openDatabase(mkdtempSync(join(tmpdir(), 'wof-unit-')));
  seedInitialData(db);
  const outcome = performSpin(db, '   ', () => 0);
  assert.equal(outcome.status, 'invalid-name');
  assert.equal(listWinningsByName(db, 'Alice', 10).length, 0);
  db.close();
});

test('performSpin records the winning prize for a valid name', () => {
  const db = openDatabase(mkdtempSync(join(tmpdir(), 'wof-unit-')));
  seedInitialData(db);
  const outcome = performSpin(db, ' Alice ', () => 0);
  assert.equal(outcome.status, 'ok');
  assert.equal(outcome.prizeIndex, 0);
  assert.equal(outcome.record.playerName, 'Alice');
  assert.equal(listWinningsByName(db, 'Alice', 10)[0].prizeName, outcome.prize.name);
  db.close();
});
