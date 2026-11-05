// Spin-the-wheel page.
(function () {
  const RADIUS = 95;
  const svg = document.getElementById('wheel');
  const spinBtn = document.getElementById('spin-btn');
  const input = document.getElementById('player');
  const result = document.getElementById('result');
  const recentList = document.getElementById('recent');

  let prizes = [];
  let rotation = 0;   // current rotation of the wheel in degrees
  let spinning = false;
  let rotor = null;

  input.value = getSavedPlayer();
  input.addEventListener('change', () => savePlayer(input.value.trim()));

  function point(deg) {
    const a = deg * Math.PI / 180;
    return (RADIUS * Math.sin(a)).toFixed(3) + ',' + (-RADIUS * Math.cos(a)).toFixed(3);
  }

  // Readable colour for text on a given background colour.
  function textColorFor(hex) {
    const n = parseInt(hex.slice(1), 16);
    const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#1a1a1a' : '#ffffff';
  }

  // Split a prize name into short lines so it fits inside a segment.
  function wrapName(name, maxChars) {
    const words = name.split(' ');
    const lines = [];
    let current = '';
    words.forEach(w => {
      const candidate = current ? current + ' ' + w : w;
      if (candidate.length > maxChars && current) {
        lines.push(current);
        current = w;
      } else {
        current = candidate;
      }
    });
    if (current) lines.push(current);
    return lines;
  }

  function drawWheel() {
    const n = prizes.length;
    if (!n) {
      svg.innerHTML = '<text x="0" y="0" text-anchor="middle" fill="#8b0000" font-size="10">No prizes yet</text>';
      rotor = null;
      return;
    }
    const seg = 360 / n;
    const parts = [];

    prizes.forEach((p, i) => {
      const a0 = i * seg, a1 = (i + 1) * seg, mid = a0 + seg / 2;
      const textColor = textColorFor(p.color);
      if (n === 1) {
        parts.push(`<circle r="${RADIUS}" fill="${p.color}"/>`);
      } else {
        parts.push(`<path d="M0 0 L${point(a0)} A${RADIUS} ${RADIUS} 0 ${seg > 180 ? 1 : 0} 1 ${point(a1)} Z" fill="${p.color}" stroke="#7a0000" stroke-width="0.6"/>`);
      }
      // Labels run along the radius. Segments on the bottom half are flipped
      // 180° so their text still reads upright.
      const lines = wrapName(p.name, 12);
      const flip = mid > 90 && mid < 270;
      const rot = flip ? mid + 180 : mid;
      const last = lines.length - 1;
      const tspans = lines.map((line, li) => {
        const k = last - li;   // first line is the top line of the reading block
        const y = flip ? 56 + k * 8 : -60 - k * 8;
        return `<tspan x="0" y="${y}">${esc(line)}</tspan>`;
      }).join('');
      parts.push(`<g transform="rotate(${rot})"><text text-anchor="middle" fill="${textColor}" font-size="6.5" font-weight="700" font-family="Arial, sans-serif">${tspans}</text></g>`);
    });

    svg.innerHTML =
      `<g id="rotor" transform="rotate(${rotation})">${parts.join('')}` +
      `<circle r="${RADIUS}" fill="none" stroke="#5c0000" stroke-width="3"/>` +
      `<circle r="9" fill="#5c0000" stroke="#fff" stroke-width="2"/>` +
      `</g>` +
      `<polygon points="-9,-108 9,-108 0,-88" fill="#5c0000" stroke="#fff" stroke-width="1.5"/>` +
      `<circle r="${RADIUS + 6}" fill="none" stroke="#8b0000" stroke-width="1.5" stroke-dasharray="2 4"/>`;
    rotor = svg.querySelector('#rotor');
  }

  function animateTo(target, duration, done) {
    const start = rotation;
    const dist = target - start;
    const t0 = performance.now();
    function frame(now) {
      const t = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      rotation = start + dist * eased;
      if (rotor) rotor.setAttribute('transform', `rotate(${rotation})`);
      if (t < 1) requestAnimationFrame(frame);
      else done();
    }
    requestAnimationFrame(frame);
  }

  async function loadPrizes() {
    try {
      const data = await api('/api/prizes');
      prizes = data.prizes;
      drawWheel();
    } catch (e) {
      result.textContent = 'Could not load prizes: ' + e.message;
    }
  }

  async function loadRecent() {
    try {
      const data = await api('/api/recent');
      if (!data.wins.length) {
        recentList.innerHTML = '<li class="muted">No spins yet. Be the first!</li>';
        return;
      }
      recentList.innerHTML = data.wins.map(w =>
        `<li><strong>${esc(w.player)}</strong> won <strong>${esc(w.prize_name)}</strong> <span class="muted">· ${esc(fmtDate(w.created_at))}</span></li>`
      ).join('');
    } catch (e) {
      recentList.innerHTML = `<li class="muted">Could not load recent winners.</li>`;
    }
  }

  function setBusy(busy) {
    spinning = busy;
    spinBtn.disabled = busy;
  }

  async function spin() {
    if (spinning || !prizes.length) return;
    const name = input.value.trim() || 'Guest';
    savePlayer(input.value.trim());
    setBusy(true);
    result.className = 'result';
    result.textContent = 'Spinning…';

    try {
      const data = await api('/api/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player: name })
      });

      const seg = 360 / prizes.length;
      const mid = data.index * seg + seg / 2;
      const jitter = (Math.random() - 0.5) * seg * 0.6;   // land somewhere inside the segment
      const base = rotation;
      const delta = ((-(mid + jitter) - base) % 360 + 360) % 360;
      const target = base + 5 * 360 + delta;

      animateTo(target, 4200, () => {
        const p = data.prize;
        result.className = 'result win';
        result.innerHTML = `<strong>${esc(p.name)}</strong><br>${esc(p.description)}`;
        setBusy(false);
        loadRecent();
      });
    } catch (e) {
      result.className = 'result';
      result.textContent = 'Spin failed: ' + e.message;
      setBusy(false);
    }
  }

  spinBtn.addEventListener('click', spin);
  loadPrizes();
  loadRecent();
})();
