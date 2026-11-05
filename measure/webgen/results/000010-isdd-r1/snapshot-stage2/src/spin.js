import { randomInt } from 'node:crypto';
import { insertWinningRecord, listPrizes } from './db.js';

const NAME_MIN_LENGTH = 1;
const NAME_MAX_LENGTH = 30;
const NAME_ERROR = 'Please enter your name (1-30 characters).';
const NO_PRIZES_ERROR = 'No prizes are available.';

/**
 * Checks a player name: a string whose length after trimming spaces is 1 to 30 characters.
 * @param {unknown} raw value received from the request
 * @returns {{ok: true, name: string} | {ok: false, error: string}} the trimmed name, or the error message
 */
export function validatePlayerName(raw) {
  if (typeof raw !== 'string') {
    return { ok: false, error: NAME_ERROR };
  }
  const name = raw.trim();
  const length = [...name].length;
  if (length < NAME_MIN_LENGTH || length > NAME_MAX_LENGTH) {
    return { ok: false, error: NAME_ERROR };
  }
  return { ok: true, name };
}

/**
 * Picks one prize with probability proportional to its weight.
 * A random integer in [0, total) is drawn; the prize whose cumulative weight first exceeds it wins.
 * @param {{weight: number}[]} prizes prizes in display order, each with a positive integer weight
 * @param {(n: number) => number} randomIntFn returns an integer in [0, n); injected for tests
 * @returns {object | null} the chosen prize, or null when the list is empty
 */
export function pickWeightedPrize(prizes, randomIntFn = randomInt) {
  const total = prizes.reduce((sum, prize) => sum + prize.weight, 0);
  if (prizes.length === 0 || total <= 0) {
    return null;
  }
  const roll = randomIntFn(total);
  let cumulative = 0;
  for (const prize of prizes) {
    cumulative += prize.weight;
    if (roll < cumulative) {
      return prize;
    }
  }
  return prizes[prizes.length - 1];
}

/**
 * Runs one spin: checks the name, reads the prizes, draws one prize and records the win.
 * Nothing is recorded when the name is invalid or no prize exists.
 * @param {import('node:sqlite').DatabaseSync} db open database
 * @param {unknown} rawName player name from the request
 * @param {(n: number) => number} randomIntFn random integer source; injected for tests
 * @returns {{status: 'ok', record: object, prize: object, prizeIndex: number} | {status: 'invalid-name' | 'no-prizes', error: string}} the outcome
 */
export function performSpin(db, rawName, randomIntFn = randomInt) {
  const checked = validatePlayerName(rawName);
  if (!checked.ok) {
    return { status: 'invalid-name', error: checked.error };
  }
  const prizes = listPrizes(db);
  const prize = pickWeightedPrize(prizes, randomIntFn);
  if (prize === null) {
    return { status: 'no-prizes', error: NO_PRIZES_ERROR };
  }
  const record = insertWinningRecord(db, {
    playerName: checked.name,
    prize,
    wonAt: new Date().toISOString(),
  });
  return { status: 'ok', record, prize, prizeIndex: prizes.findIndex((p) => p.id === prize.id) };
}
