import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, spin, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('spinning with a name returns a prize and records it for that name', async () => {
  const result = await spin(server.baseUrl, 'Alice');
  assert.equal(result.status, 201);
  assert.equal(result.body.record.playerName, 'Alice');
  assert.equal(typeof result.body.prize.name, 'string');
  assert.ok(result.body.prizeIndex >= 0 && result.body.prizeIndex < 8);

  const list = await winnings(server.baseUrl, 'Alice');
  assert.equal(list.status, 200);
  const match = list.body.winnings.find((w) => w.id === result.body.record.id);
  assert.ok(match, 'the spin must appear in the winnings');
  assert.equal(match.prizeName, result.body.prize.name);
  assert.equal(match.wonAt, result.body.record.wonAt);
});
