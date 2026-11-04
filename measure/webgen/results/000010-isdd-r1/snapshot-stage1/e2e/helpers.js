import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/**
 * Finds a free TCP port on 127.0.0.1.
 * @returns {Promise<number>} the port number
 */
function freePort() {
  return new Promise((resolve, reject) => {
    const probe = createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
  });
}

/**
 * Starts the real server with a new empty DATA_DIR on a free port and waits until it answers.
 * @returns {Promise<{baseUrl: string, stop: () => Promise<void>}>} the base URL and a function that stops the server
 */
export async function startServer() {
  const port = await freePort();
  const dataDir = mkdtempSync(join(tmpdir(), 'wof-e2e-'));
  const child = spawn(process.execPath, [join(ROOT, 'src', 'server.js')], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(port), DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stderr = '';
  child.stderr.on('data', (chunk) => { stderr += chunk; });
  const baseUrl = `http://127.0.0.1:${port}`;

  const deadline = Date.now() + 15000;
  for (;;) {
    try {
      const response = await fetch(`${baseUrl}/api/prizes`);
      if (response.ok) break;
    } catch {
      // not listening yet
    }
    if (child.exitCode !== null) throw new Error(`server exited early: ${stderr}`);
    if (Date.now() > deadline) {
      child.kill();
      throw new Error(`server did not start: ${stderr}`);
    }
    await new Promise((r) => setTimeout(r, 100));
  }

  return {
    baseUrl,
    stop: () => new Promise((resolve) => {
      if (child.exitCode !== null) return resolve();
      child.once('exit', () => resolve());
      child.kill();
    }),
  };
}

/**
 * Sends a spin request for the given name.
 * @param {string} baseUrl server base URL
 * @param {unknown} name value for the name field
 * @returns {Promise<{status: number, body: object}>} HTTP status and parsed JSON body
 */
export async function spin(baseUrl, name) {
  const response = await fetch(`${baseUrl}/api/spin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  return { status: response.status, body: await response.json() };
}

/**
 * Lists the winnings of one player through the API.
 * @param {string} baseUrl server base URL
 * @param {string} name player name
 * @returns {Promise<{status: number, body: object}>} HTTP status and parsed JSON body
 */
export async function winnings(baseUrl, name) {
  const response = await fetch(`${baseUrl}/api/winnings?name=${encodeURIComponent(name)}`);
  return { status: response.status, body: await response.json() };
}
