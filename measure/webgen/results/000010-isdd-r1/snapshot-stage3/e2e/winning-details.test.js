import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, spin, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('every winning record carries the player name, the prize name and the time', async () => {
  await spin(server.baseUrl, 'Alice');
  const result = await winnings(server.baseUrl, 'Alice');
  assert.equal(result.status, 200);
  assert.ok(result.body.winnings.length >= 1);
  for (const record of result.body.winnings) {
    assert.equal(record.playerName, 'Alice');
    assert.equal(typeof record.prizeName, 'string');
    assert.ok(record.prizeName.length > 0);
    assert.ok(!Number.isNaN(Date.parse(record.wonAt)), 'wonAt is a date');
  }
});

test('the My Winnings table has Player, Reward and Won at columns', async () => {
  const html = await (await fetch(`${server.baseUrl}/`)).text();
  const table = html.match(/<table class="data-table" id="winnings-table">[\s\S]*?<\/thead>/);
  assert.ok(table, 'the winnings table exists');
  assert.match(table[0], /<th scope="col">Player<\/th><th scope="col">Reward<\/th><th scope="col">Won at<\/th>/);
});
