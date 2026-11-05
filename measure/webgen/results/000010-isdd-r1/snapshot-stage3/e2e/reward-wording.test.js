import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('the page shows no prize wording: visible text and labels say reward', async () => {
  const html = await (await fetch(`${server.baseUrl}/`)).text();
  // Visible text is what sits between tags; labels are the aria-label and placeholder values.
  const visible = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]*>/g, ' ');
  assert.doesNotMatch(visible, /prize/i);
  const labels = [...html.matchAll(/(?:aria-label|placeholder)="([^"]*)"/g)].map((m) => m[1]);
  for (const label of labels) assert.doesNotMatch(label, /prize/i, `label "${label}"`);
  assert.match(html, /<a href="#\/rewards" data-route="prizes">Reward List<\/a>/);
});

test('the reward names shown on the wheel and in the list have no prize wording', async () => {
  const body = await (await fetch(`${server.baseUrl}/api/prizes`)).json();
  assert.ok(body.prizes.some((p) => p.name === 'Grand Reward Headphones'));
  for (const reward of body.prizes) {
    assert.doesNotMatch(reward.name, /prize/i, `reward "${reward.name}"`);
  }
});
