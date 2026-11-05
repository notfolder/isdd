import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('an empty data directory starts with sample prizes and sample records', async () => {
  const prizes = await (await fetch(`${server.baseUrl}/api/prizes`)).json();
  assert.equal(prizes.prizes.length, 8);
  const sample = await winnings(server.baseUrl, 'Sample Player');
  assert.equal(sample.status, 200);
  assert.equal(sample.body.winnings.length, 3);
});
