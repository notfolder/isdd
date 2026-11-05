import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, spin, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('a name with no records gets an empty list', async () => {
  const result = await winnings(server.baseUrl, 'Bob');
  assert.equal(result.status, 200);
  assert.deepEqual(result.body.winnings, []);
});

test('each name sees only its own records, newest first', async () => {
  const first = await spin(server.baseUrl, 'Alice');
  const second = await spin(server.baseUrl, 'Alice');
  await spin(server.baseUrl, 'Carol');

  const alice = await winnings(server.baseUrl, 'Alice');
  assert.equal(alice.body.winnings.length, 2);
  const ids = alice.body.winnings.map((w) => w.id);
  assert.deepEqual(ids, [second.body.record.id, first.body.record.id]);
  assert.equal(alice.body.winnings.some((w) => w.prizeName === undefined), false);

  const bob = await winnings(server.baseUrl, 'Bob');
  assert.equal(bob.body.winnings.length, 0);
});
