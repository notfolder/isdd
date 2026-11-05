import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, spin, winnings } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('the name field is required and sits in the same form as the Spin button', async () => {
  const html = await (await fetch(`${server.baseUrl}/`)).text();
  const form = html.match(/<form id="spin-form"[\s\S]*?<\/form>/);
  assert.ok(form, 'the spin form exists');
  assert.match(form[0], /<input id="spin-name"[^>]*\srequired[\s>]/);
  assert.match(form[0], /<button type="submit" id="spin-button"/);
  assert.match(html, /<label for="spin-name">Your name \(required\)<\/label>/);
});

test('an empty or too long name is refused: same message, nothing recorded', async () => {
  const before = await winnings(server.baseUrl, 'Sample Player');
  const empty = await spin(server.baseUrl, '   ');
  const tooLong = await spin(server.baseUrl, 'x'.repeat(31));
  for (const result of [empty, tooLong]) {
    assert.equal(result.status, 400);
    assert.equal(result.body.error, 'Please enter your name (1-30 characters).');
  }
  const after_ = await winnings(server.baseUrl, 'Sample Player');
  assert.equal(after_.body.winnings.length, before.body.winnings.length);
});
