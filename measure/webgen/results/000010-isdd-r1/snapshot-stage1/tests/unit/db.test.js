import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openDatabase, seedInitialData, listPrizes, listWinningsByName } from '../../src/db.js';

test('an empty data directory gets 8 prizes and 3 sample records', () => {
  const dir = join(mkdtempSync(join(tmpdir(), 'wof-db-')), 'nested');
  const db = openDatabase(dir);
  seedInitialData(db);
  assert.equal(listPrizes(db).length, 8);
  assert.equal(listWinningsByName(db, 'Sample Player', 100).length, 3);
  db.close();
});

test('seeding a second time adds nothing', () => {
  const db = openDatabase(mkdtempSync(join(tmpdir(), 'wof-db-')));
  seedInitialData(db);
  seedInitialData(db);
  assert.equal(listPrizes(db).length, 8);
  assert.equal(listWinningsByName(db, 'Sample Player', 100).length, 3);
  db.close();
});

test('initial prize weights sum to 100', () => {
  const db = openDatabase(mkdtempSync(join(tmpdir(), 'wof-db-')));
  seedInitialData(db);
  assert.equal(listPrizes(db).reduce((sum, p) => sum + p.weight, 0), 100);
  db.close();
});
