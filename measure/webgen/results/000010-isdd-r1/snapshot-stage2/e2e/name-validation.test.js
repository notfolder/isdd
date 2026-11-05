import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, spin, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());
const MESSAGE = 'Please enter your name (1-30 characters).';

test('an empty name is refused and nothing is recorded', async () => {
  const result = await spin(server.baseUrl, '');
  assert.equal(result.status, 400);
  assert.equal(result.body.error, MESSAGE);
  assert.equal((await winnings(server.baseUrl, 'Dana')).body.winnings.length, 0);
});

test('a 31-character name is refused and the winnings lookup refuses it too', async () => {
  const name = 'x'.repeat(31);
  const result = await spin(server.baseUrl, name);
  assert.equal(result.status, 400);
  assert.equal(result.body.error, MESSAGE);
  const lookup = await winnings(server.baseUrl, name);
  assert.equal(lookup.status, 400);
  assert.equal(lookup.body.error, MESSAGE);
});

test('a 30-character name is accepted', async () => {
  const name = 'y'.repeat(30);
  assert.equal((await spin(server.baseUrl, name)).status, 201);
});
