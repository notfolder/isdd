import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { listPrizes, listWinningsByName } from './db.js';
import { performSpin, validatePlayerName } from './spin.js';

const PUBLIC_DIR = fileURLToPath(new URL('../public/', import.meta.url));
const MAX_WINNINGS = 100;
const MAX_BODY_BYTES = 4096;

// Only these files are served; anything else is a 404.
const STATIC_FILES = {
  '/': { file: 'index.html', type: 'text/html; charset=utf-8' },
  '/index.html': { file: 'index.html', type: 'text/html; charset=utf-8' },
  '/style.css': { file: 'style.css', type: 'text/css; charset=utf-8' },
  '/app.js': { file: 'app.js', type: 'text/javascript; charset=utf-8' },
};

/**
 * Sends a JSON response.
 * @param {import('node:http').ServerResponse} res response to write
 * @param {number} status HTTP status code
 * @param {object} body value to serialize as JSON
 * @returns {void}
 */
function _sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}

/**
 * Reads a small request body and parses it as JSON.
 * @param {import('node:http').IncomingMessage} req request whose body is read
 * @returns {Promise<unknown>} the parsed value; rejects when the body is too large or not JSON
 */
function _readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new SyntaxError('Request body must be JSON.'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch {
        reject(new SyntaxError('Request body must be JSON.'));
      }
    });
    req.on('error', reject);
  });
}

/**
 * Routes one HTTP request to the JSON API or the static files.
 * @param {import('node:http').IncomingMessage} req incoming request
 * @param {import('node:http').ServerResponse} res response to write
 * @param {{db: import('node:sqlite').DatabaseSync}} context shared resources
 * @returns {Promise<void>} resolves after the response is written
 */
export async function handleRequest(req, res, context) {
  const url = new URL(req.url, 'http://localhost');
  try {
    if (url.pathname === '/api/spin') {
      if (req.method !== 'POST') return _sendJson(res, 405, { error: 'Method not allowed.' });
      return await handleSpin(req, res, context);
    }
    if (url.pathname === '/api/prizes') {
      if (req.method !== 'GET') return _sendJson(res, 405, { error: 'Method not allowed.' });
      return handlePrizes(res, context);
    }
    if (url.pathname === '/api/winnings') {
      if (req.method !== 'GET') return _sendJson(res, 405, { error: 'Method not allowed.' });
      return handleWinnings(url, res, context);
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      return _sendJson(res, 405, { error: 'Method not allowed.' });
    }
    return await serveStaticFile(res, url.pathname);
  } catch (err) {
    if (err instanceof SyntaxError) {
      return _sendJson(res, 400, { error: err.message });
    }
    console.error(err);
    return _sendJson(res, 500, { error: 'Something went wrong.' });
  }
}

/**
 * Serves one of the allowed static files, or 404.
 * @param {import('node:http').ServerResponse} res response to write
 * @param {string} pathname request path
 * @returns {Promise<void>} resolves after the response is written
 */
export async function serveStaticFile(res, pathname) {
  const entry = STATIC_FILES[pathname];
  if (!entry) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not found');
    return;
  }
  const content = await readFile(join(PUBLIC_DIR, entry.file));
  res.writeHead(200, { 'Content-Type': entry.type, 'Cache-Control': 'no-cache' });
  res.end(content);
}

/**
 * POST /api/spin: draws a prize for the given name and records it.
 * @param {import('node:http').IncomingMessage} req request with JSON body {"name": "..."}
 * @param {import('node:http').ServerResponse} res response to write
 * @param {{db: import('node:sqlite').DatabaseSync}} context shared resources
 * @returns {Promise<void>} resolves after the response is written
 */
export async function handleSpin(req, res, context) {
  const body = await _readJsonBody(req);
  const name = body !== null && typeof body === 'object' ? body.name : undefined;
  const outcome = performSpin(context.db, name);
  if (outcome.status === 'invalid-name') {
    return _sendJson(res, 400, { error: outcome.error });
  }
  if (outcome.status === 'no-prizes') {
    return _sendJson(res, 409, { error: outcome.error });
  }
  const { record, prize, prizeIndex } = outcome;
  return _sendJson(res, 201, {
    record,
    prize: { id: prize.id, name: prize.name, weight: prize.weight, sortOrder: prize.sortOrder },
    prizeIndex,
  });
}

/**
 * GET /api/prizes: lists the prizes in display order with their chance in percent.
 * @param {import('node:http').ServerResponse} res response to write
 * @param {{db: import('node:sqlite').DatabaseSync}} context shared resources
 * @returns {void}
 */
export function handlePrizes(res, context) {
  const prizes = listPrizes(context.db);
  const totalWeight = prizes.reduce((sum, prize) => sum + prize.weight, 0);
  return _sendJson(res, 200, {
    prizes: prizes.map((prize) => ({
      id: prize.id,
      name: prize.name,
      weight: prize.weight,
      chance: totalWeight > 0 ? Math.round((prize.weight / totalWeight) * 1000) / 10 : 0,
      sortOrder: prize.sortOrder,
    })),
    totalWeight,
  });
}

/**
 * GET /api/winnings?name=...: lists one player's winning records, newest first.
 * @param {URL} url parsed request URL carrying the name query
 * @param {import('node:http').ServerResponse} res response to write
 * @param {{db: import('node:sqlite').DatabaseSync}} context shared resources
 * @returns {void}
 */
export function handleWinnings(url, res, context) {
  const checked = validatePlayerName(url.searchParams.get('name') ?? '');
  if (!checked.ok) {
    return _sendJson(res, 400, { error: checked.error });
  }
  return _sendJson(res, 200, {
    name: checked.name,
    winnings: listWinningsByName(context.db, checked.name, MAX_WINNINGS),
  });
}

