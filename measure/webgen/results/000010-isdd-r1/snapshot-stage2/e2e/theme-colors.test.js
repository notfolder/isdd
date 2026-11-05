import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { startServer } from './helpers.js';

const server = await startServer();
after(() => server.stop());

test('the stylesheet uses an ivory background and dark green components, with no gray or dark red left', async () => {
  const response = await fetch(`${server.baseUrl}/style.css`);
  assert.equal(response.status, 200);
  const css = await response.text();
  assert.match(css, /--bg:\s*#fffff0/i);
  assert.match(css, /--green:\s*#006400/i);
  assert.doesNotMatch(css, /#e6e6e6/i);
  assert.doesNotMatch(css, /#8b0000/i);
});
