(function () {
  'use strict';

  var NAME_KEY = 'wheel-of-fortune-player';
  var page = document.body.getAttribute('data-page');

  function $(id) { return document.getElementById(id); }

  function esc(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function api(path, options) {
    return fetch(path, options).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) { throw new Error(data.error || 'Something went wrong. Please try again.'); }
        return data;
      });
    });
  }

  function formatDate(iso) {
    var d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  }

  function markActiveNav() {
    document.querySelectorAll('[data-nav]').forEach(function (a) {
      if (a.getAttribute('data-nav') === page) { a.setAttribute('aria-current', 'page'); }
    });
  }

  function setMessage(el, text, kind) {
    el.textContent = text;
    el.className = 'message' + (kind ? ' ' + kind : '');
  }

  /* ---------- Spin the Wheel ---------- */
  function initSpin() {
    var wheelEl = $('wheel'), form = $('spin-form'), input = $('player-name'),
        button = $('spin-button'), message = $('message'), recent = $('recent-winners');
    var prizes = [], rotation = 0, spinning = false;
    var SPIN_MS = 4000;

    input.value = localStorage.getItem(NAME_KEY) || '';

    function drawWheel() {
      var n = prizes.length, c = 200, r = 196, parts = [];
      if (!n) { wheelEl.textContent = 'No prizes are set up yet.'; return; }
      var slice = 360 / n;
      prizes.forEach(function (p, i) {
        var a0 = (i * slice - 90) * Math.PI / 180, a1 = ((i + 1) * slice - 90) * Math.PI / 180;
        var x0 = c + r * Math.cos(a0), y0 = c + r * Math.sin(a0);
        var x1 = c + r * Math.cos(a1), y1 = c + r * Math.sin(a1);
        var large = slice > 180 ? 1 : 0;
        parts.push('<path d="M' + c + ' ' + c + ' L' + x0.toFixed(2) + ' ' + y0.toFixed(2) +
          ' A' + r + ' ' + r + ' 0 ' + large + ' 1 ' + x1.toFixed(2) + ' ' + y1.toFixed(2) +
          ' Z" fill="' + esc(p.color) + '" stroke="#ffffff" stroke-width="2"/>');
        var mid = (i + 0.5) * slice - 90;
        parts.push('<text transform="rotate(' + mid.toFixed(2) + ' ' + c + ' ' + c + ')" x="' +
          (c + r - 20) + '" y="' + c + '" text-anchor="end" dominant-baseline="middle" fill="#ffffff"' +
          ' font-size="14" font-weight="700">' + esc(p.name) + '</text>');
      });
      parts.push('<circle cx="200" cy="200" r="198" fill="none" stroke="#5c0000" stroke-width="6"/>');
      parts.push('<circle cx="200" cy="200" r="24" fill="#ffffff" stroke="#8b0000" stroke-width="6"/>');
      wheelEl.innerHTML = '<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" focusable="false">' +
        parts.join('') + '</svg>';
    }

    function loadRecent() {
      api('/api/winnings').then(function (data) {
        if (!data.winnings.length) {
          recent.innerHTML = '<li class="empty">No winners yet. Be the first!</li>';
          return;
        }
        recent.innerHTML = data.winnings.map(function (w) {
          return '<li><strong>' + esc(w.player) + '</strong> won <span class="prize-name">' +
            esc(w.prize_name) + '</span><br><time>' + esc(formatDate(w.created_at)) + '</time></li>';
        }).join('');
      }).catch(function () {
        recent.innerHTML = '<li class="empty">Could not load recent winners.</li>';
      });
    }

    // Turn the wheel so that the chosen segment stops under the pointer at the top.
    function animateTo(index) {
      var slice = 360 / prizes.length;
      var center = (index + 0.5) * slice;                       // clockwise from the top
      var jitter = (Math.random() - 0.5) * slice * 0.6;         // stay inside the segment
      var target = ((360 - center + jitter) % 360 + 360) % 360; // rotation that puts it on top
      var current = ((rotation % 360) + 360) % 360;
      var delta = (target - current + 360) % 360;
      rotation += 360 * 5 + delta;
      wheelEl.style.transition = 'transform ' + (SPIN_MS / 1000) + 's cubic-bezier(0.17, 0.67, 0.12, 0.99)';
      wheelEl.style.transform = 'rotate(' + rotation + 'deg)';
    }

    function finish(name, result) {
      spinning = false;
      button.disabled = false;
      if (result.won) {
        setMessage(message, 'Congratulations, ' + name + '! You won: ' + result.prize.name +
          '. It is saved in My Winnings.', 'success');
      } else {
        setMessage(message, 'No prize this time, ' + name + '. Spin again!', '');
      }
      loadRecent();
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (spinning) { return; }
      var name = input.value.trim();
      if (!name) {
        setMessage(message, 'Please enter your name before spinning.', 'error');
        input.focus();
        return;
      }
      if (!prizes.length) { setMessage(message, 'No prizes are set up yet.', 'error'); return; }
      localStorage.setItem(NAME_KEY, name);
      spinning = true;
      button.disabled = true;
      setMessage(message, 'Spinning...', '');
      api('/api/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player: name })
      }).then(function (result) {
        animateTo(result.index);
        setTimeout(function () { finish(name, result); }, SPIN_MS + 200);
      }).catch(function (err) {
        spinning = false;
        button.disabled = false;
        setMessage(message, err.message, 'error');
      });
    });

    api('/api/prizes').then(function (data) {
      prizes = data.prizes;
      drawWheel();
    }).catch(function (err) {
      setMessage(message, 'Could not load prizes: ' + err.message, 'error');
    });
    loadRecent();
  }

  /* ---------- Prize List ---------- */
  function initPrizes() {
    var list = $('prize-list');
    api('/api/prizes').then(function (data) {
      if (!data.prizes.length) { list.innerHTML = '<p class="empty">No prizes are set up yet.</p>'; return; }
      list.innerHTML = data.prizes.map(function (p) {
        var badge = p.is_win ? '<span class="badge">Prize</span>' : '<span class="badge no-prize">No prize</span>';
        return '<article class="prize-card" style="border-left-color:' + esc(p.color) + '">' +
          '<h3>' + esc(p.name) + '</h3>' +
          '<p>' + esc(p.description) + '</p>' +
          '<p>' + badge + ' Chance: <strong>' + esc(p.chance) + '%</strong></p>' +
          '</article>';
      }).join('');
    }).catch(function (err) {
      list.innerHTML = '<p class="empty">Could not load prizes: ' + esc(err.message) + '</p>';
    });
  }

  /* ---------- My Winnings ---------- */
  function initWinnings() {
    var form = $('lookup-form'), input = $('lookup-name'), message = $('message'),
        summary = $('summary'), results = $('results');

    input.value = localStorage.getItem(NAME_KEY) || '';

    function load(name) {
      setMessage(message, '', '');
      api('/api/winnings?player=' + encodeURIComponent(name)).then(function (data) {
        var rows = data.winnings;
        if (!rows.length) {
          summary.textContent = '';
          results.innerHTML = '<p class="empty">No winnings recorded for ' + esc(name) +
            ' yet. <a href="/">Spin the wheel</a> to try your luck!</p>';
          return;
        }
        summary.textContent = rows.length + (rows.length === 1 ? ' win' : ' wins') + ' for ' + name;
        results.innerHTML = '<table><thead><tr><th scope="col">Date</th><th scope="col">Prize</th></tr></thead><tbody>' +
          rows.map(function (w) {
            return '<tr><td>' + esc(formatDate(w.created_at)) + '</td><td>' + esc(w.prize_name) + '</td></tr>';
          }).join('') + '</tbody></table>';
      }).catch(function (err) {
        summary.textContent = '';
        results.innerHTML = '';
        setMessage(message, err.message, 'error');
      });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = input.value.trim();
      if (!name) {
        setMessage(message, 'Please enter your name.', 'error');
        input.focus();
        return;
      }
      localStorage.setItem(NAME_KEY, name);
      load(name);
    });

    if (input.value.trim()) { load(input.value.trim()); }
  }

  markActiveNav();
  if (page === 'spin') { initSpin(); }
  else if (page === 'prizes') { initPrizes(); }
  else if (page === 'winnings') { initWinnings(); }
})();
