import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDatabase, seedInitialData } from './db.js';
import { handleRequest } from './routes.js';

const HOST = '127.0.0.1';

/**
 * Opens the database, adds sample data when empty, and starts listening on 127.0.0.1.
 * @param {{port: number, dataDir: string}} options port to listen on (0 picks a free port) and the data directory
 * @returns {Promise<import('node:http').Server>} the listening server
 */
export function startServer({ port, dataDir }) {
  const db = openDatabase(dataDir);
  seedInitialData(db);
  const server = createServer((req, res) => {
    handleRequest(req, res, { db });
  });
  return new Promise((resolvePromise, reject) => {
    server.once('error', reject);
    server.listen(port, HOST, () => resolvePromise(server));
  });
}

function _isMainModule() {
  return process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}

if (_isMainModule()) {
  const port = Number(process.env.PORT ?? 8000);
  const dataDir = process.env.DATA_DIR ?? './data';
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error(`Invalid PORT: ${process.env.PORT}`);
    process.exit(1);
  }
  startServer({ port, dataDir })
    .then(() => {
      console.log(`Wheel of Fortune is running at http://${HOST}:${port}/ (data: ${dataDir})`);
    })
    .catch((err) => {
      console.error(`Failed to start: ${err.message}`);
      process.exit(1);
    });
}
