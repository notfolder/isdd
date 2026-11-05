import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('every screen is in the same page with a menu to the three screens', async () => {
  const html = await (await fetch(`${server.baseUrl}/`)).text();
  assert.match(html, /<a href="#\/" data-route="spin">Spin the Wheel<\/a>/);
  assert.match(html, /<a href="#\/prizes" data-route="prizes">Prize List<\/a>/);
  assert.match(html, /<a href="#\/winnings" data-route="winnings">My Winnings<\/a>/);
  assert.match(html, /<html lang="en">/);
});

test('the stylesheet is served as CSS', async () => {
  const response = await fetch(`${server.baseUrl}/style.css`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /text\/css/);
});

test('the script is served and unknown paths are 404', async () => {
  const script = await fetch(`${server.baseUrl}/app.js`);
  assert.equal(script.status, 200);
  const missing = await fetch(`${server.baseUrl}/secret.txt`);
  assert.equal(missing.status, 404);
});
