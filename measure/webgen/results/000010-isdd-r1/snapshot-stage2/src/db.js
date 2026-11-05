import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';

// Initial prizes. Weights are relative chances; they sum to 100 for easy reading.
const INITIAL_PRIZES = [
  { name: 'Gift Card $50', weight: 5 },
  { name: 'Coffee Voucher', weight: 15 },
  { name: 'Free Dessert', weight: 20 },
  { name: 'Sticker Pack', weight: 25 },
  { name: 'Keychain', weight: 15 },
  { name: 'Tote Bag', weight: 10 },
  { name: 'Mug', weight: 7 },
  { name: 'Grand Prize Headphones', weight: 3 },
];

// Sample winning records added once, when the record table is empty.
const SAMPLE_RECORDS = [
  { playerName: 'Sample Player', prizeName: 'Sticker Pack', daysAgo: 3 },
  { playerName: 'Sample Player', prizeName: 'Coffee Voucher', daysAgo: 2 },
  { playerName: 'Sample Player', prizeName: 'Free Dessert', daysAgo: 1 },
];

/**
 * Opens (and creates if needed) the SQLite database in dataDir and makes sure the tables exist.
 * @param {string} dataDir directory that holds wheel.sqlite; created when missing
 * @returns {DatabaseSync} open database handle
 */
export function openDatabase(dataDir) {
  mkdirSync(dataDir, { recursive: true });
  const db = new DatabaseSync(join(dataDir, 'wheel.sqlite'));
  db.exec(`
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS prize (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 40),
      weight INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 100),
      sort_order INTEGER NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS winning_record (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      player_name TEXT NOT NULL CHECK (length(player_name) BETWEEN 1 AND 30),
      prize_id INTEGER NOT NULL REFERENCES prize (id),
      prize_name TEXT NOT NULL,
      won_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS winning_record_player_won
      ON winning_record (player_name, won_at);
  `);
  return db;
}

/**
 * Fills empty tables with sample content so every feature can be tried at once.
 * Prizes are added only when the prize table is empty; sample records only when the record table is empty.
 * @param {DatabaseSync} db open database
 * @returns {void}
 */
export function seedInitialData(db) {
  db.exec('BEGIN');
  try {
    const prizeCount = db.prepare('SELECT COUNT(*) AS n FROM prize').get().n;
    if (prizeCount === 0) {
      const insert = db.prepare('INSERT INTO prize (name, weight, sort_order) VALUES (?, ?, ?)');
      INITIAL_PRIZES.forEach((prize, index) => insert.run(prize.name, prize.weight, index + 1));
    }

    const recordCount = db.prepare('SELECT COUNT(*) AS n FROM winning_record').get().n;
    if (recordCount === 0) {
      const prizes = listPrizes(db);
      for (const sample of SAMPLE_RECORDS) {
        const prize = prizes.find((p) => p.name === sample.prizeName);
        if (!prize) continue;
        const wonAt = new Date(Date.now() - sample.daysAgo * 24 * 60 * 60 * 1000).toISOString();
        insertWinningRecord(db, { playerName: sample.playerName, prize, wonAt });
      }
    }
    db.exec('COMMIT');
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
}

/**
 * Lists all prizes in display order.
 * @param {DatabaseSync} db open database
 * @returns {{id: number, name: string, weight: number, sortOrder: number}[]} prizes sorted by sort order
 */
export function listPrizes(db) {
  return db
    .prepare('SELECT id, name, weight, sort_order FROM prize ORDER BY sort_order')
    .all()
    .map((row) => ({ id: Number(row.id), name: row.name, weight: Number(row.weight), sortOrder: Number(row.sort_order) }));
}

/**
 * Stores one winning record. The prize name is copied so later renames do not change the record.
 * @param {DatabaseSync} db open database
 * @param {{playerName: string, prize: {id: number, name: string}, wonAt: string}} winning values to store
 * @returns {{id: number, playerName: string, prizeId: number, prizeName: string, wonAt: string}} the stored record
 */
export function insertWinningRecord(db, { playerName, prize, wonAt }) {
  const result = db
    .prepare('INSERT INTO winning_record (player_name, prize_id, prize_name, won_at) VALUES (?, ?, ?, ?)')
    .run(playerName, prize.id, prize.name, wonAt);
  return { id: Number(result.lastInsertRowid), playerName, prizeId: prize.id, prizeName: prize.name, wonAt };
}

/**
 * Lists the winning records of one player (exact, case-sensitive name match), newest first.
 * @param {DatabaseSync} db open database
 * @param {string} playerName validated player name
 * @param {number} limit maximum number of records to return
 * @returns {{id: number, prizeName: string, wonAt: string}[]} matching records
 */
export function listWinningsByName(db, playerName, limit) {
  return db
    .prepare(
      'SELECT id, prize_name, won_at FROM winning_record WHERE player_name = ? ORDER BY won_at DESC, id DESC LIMIT ?'
    )
    .all(playerName, limit)
    .map((row) => ({ id: Number(row.id), prizeName: row.prize_name, wonAt: row.won_at }));
}
