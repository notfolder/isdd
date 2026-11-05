import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('the prize list has all 8 prizes whose chances add up to 100 percent', async () => {
  const response = await fetch(`${server.baseUrl}/api/prizes`);
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.prizes.length, 8);
  assert.equal(body.totalWeight, 100);
  const chanceSum = body.prizes.reduce((sum, p) => sum + p.chance, 0);
  assert.ok(Math.abs(chanceSum - 100) < 0.5, `chance sum was ${chanceSum}`);
  for (const prize of body.prizes) {
    assert.equal(typeof prize.name, 'string');
    assert.ok(prize.name.length > 0);
  }
});

test('the Prize List screen is served with its English heading', async () => {
  const html = await (await fetch(`${server.baseUrl}/`)).text();
  assert.match(html, /<h2 id="prizes-title">Prize List<\/h2>/);
});
