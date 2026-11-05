// Shared helpers for every page.
const PLAYER_KEY = 'wof-player-name';

function getSavedPlayer() {
  try { return localStorage.getItem(PLAYER_KEY) || ''; } catch (e) { return ''; }
}

function savePlayer(name) {
  try { localStorage.setItem(PLAYER_KEY, name); } catch (e) { /* storage unavailable */ }
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function fmtDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
}

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || ('Request failed (' + res.status + ')'));
  return data;
}
