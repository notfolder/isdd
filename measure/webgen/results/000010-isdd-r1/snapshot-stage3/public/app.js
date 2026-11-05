(() => {
  'use strict';

  const NAME_KEY = 'wheel.playerName';
  const NAME_MESSAGE = 'Please enter your name (1-30 characters).';
  const SPIN_MS = 4500;
  // Wheel slices: two dark greens in turn; with an odd count the last slice gets a darker green.
  const SLICE_COLORS = ['#006400', '#1e7b34'];
  const ODD_LAST_COLOR = '#004d1a';

  const state = {
    prizes: [],
    rotation: 0,
  };

  const $ = (id) => document.getElementById(id);
  const spinForm = $('spin-form');
  const spinName = $('spin-name');
  const spinButton = $('spin-button');
  const spinError = $('spin-error');
  const spinResult = $('spin-result');
  const resultPrize = $('result-prize');
  const resultTime = $('result-time');
  const wheelFace = $('wheel-face');
  const prizesError = $('prizes-error');
  const prizesBody = $('prizes-table').querySelector('tbody');
  const winningsForm = $('winnings-form');
  const winningsName = $('winnings-name');
  const winningsError = $('winnings-error');
  const winningsCount = $('winnings-count');
  const winningsBody = $('winnings-table').querySelector('tbody');

  /**
   * Shows an error message in the given element, or hides it when the message is empty.
   * @param {HTMLElement} element message element
   * @param {string} message text to show; empty hides the element
   * @returns {void}
   */
  function setMessage(element, message) {
    element.textContent = message;
    element.hidden = !message;
  }

  /**
   * Calls the JSON API and returns the parsed body, or throws the server's error message.
   * @param {string} path request path under /api
   * @param {RequestInit} [options] fetch options
   * @returns {Promise<object>} parsed JSON body
   */
  async function api(path, options) {
    const response = await fetch(path, options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.error || 'Something went wrong.');
    }
    return body;
  }

  /**
   * Remembers the last name used so the name fields can be filled next time.
   * @param {string} name name to remember
   * @returns {void}
   */
  function rememberName(name) {
    try {
      localStorage.setItem(NAME_KEY, name);
    } catch {
      // Storage may be unavailable (for example in private mode); the name is simply not kept.
    }
  }

  /**
   * Reads the last name used, or an empty string.
   * @returns {string} remembered name
   */
  function recallName() {
    try {
      return localStorage.getItem(NAME_KEY) || '';
    } catch {
      return '';
    }
  }

  /**
   * Builds the wheel: equal-sized slices in display order, each with the prize name.
   * @param {{name: string}[]} prizes prizes in display order
   * @returns {void}
   */
  function buildWheel(prizes) {
    wheelFace.replaceChildren();
    wheelFace.style.transform = `rotate(${state.rotation}deg)`;
    const count = prizes.length;
    if (count === 0) {
      wheelFace.style.background = '#ffffff';
      return;
    }
    const step = 360 / count;
    const stops = prizes.map((_, index) => {
      let color = SLICE_COLORS[index % 2];
      if (count % 2 === 1 && index === count - 1) color = ODD_LAST_COLOR;
      return `${color} ${index * step}deg ${(index + 1) * step}deg`;
    });
    wheelFace.style.background = `conic-gradient(${stops.join(', ')})`;

    prizes.forEach((prize, index) => {
      const holder = document.createElement('div');
      holder.className = 'slice-label';
      holder.style.transform = `rotate(${(index + 0.5) * step}deg)`;
      const label = document.createElement('span');
      label.textContent = prize.name;
      holder.appendChild(label);
      wheelFace.appendChild(holder);
    });
  }

  /**
   * Turns the wheel so that the slice at the given index stops under the pointer at the top.
   * @param {number} index position of the won prize in display order
   * @param {number} count number of slices on the wheel
   * @returns {void}
   */
  function turnToSlice(index, count) {
    const step = 360 / count;
    const center = (index + 0.5) * step;
    const target = 360 - center;
    const current = ((state.rotation % 360) + 360) % 360;
    const delta = (target - current + 360) % 360;
    state.rotation += 5 * 360 + delta;
    wheelFace.style.transform = `rotate(${state.rotation}deg)`;
  }

  /**
   * Loads the prize list and redraws the wheel and the prize table.
   * @returns {Promise<void>} resolves when the data is shown
   */
  async function loadPrizes() {
    try {
      const data = await api('/api/prizes');
      state.prizes = data.prizes;
      buildWheel(state.prizes);
      prizesBody.replaceChildren(
        ...state.prizes.map((prize) => {
          const row = document.createElement('tr');
          const name = document.createElement('td');
          name.textContent = prize.name;
          const chance = document.createElement('td');
          chance.textContent = `${prize.chance.toFixed(1)}%`;
          row.append(name, chance);
          return row;
        })
      );
      setMessage(prizesError, '');
    } catch (err) {
      setMessage(prizesError, err.message);
    }
  }

  /**
   * Formats an ISO time for display.
   * @param {string} iso time in ISO 8601
   * @returns {string} readable local time in English
   */
  function formatTime(iso) {
    return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  }

  /**
   * Checks a name the same way the server does: 1 to 30 characters after trimming spaces.
   * @param {string} raw text typed in the name field
   * @returns {boolean} true when the name may be sent
   */
  function isValidName(raw) {
    const length = [...raw.trim()].length;
    return length >= 1 && length <= 30;
  }

  spinForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage(spinError, '');
    spinResult.hidden = true;
    const name = spinName.value;
    // A missing name stops the spin here: no request is sent and the wheel does not turn.
    if (!isValidName(name)) {
      setMessage(spinError, NAME_MESSAGE);
      spinName.focus();
      return;
    }
    spinButton.disabled = true;
    try {
      const data = await api('/api/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      rememberName(data.record.playerName);
      spinName.value = data.record.playerName;
      winningsName.value = data.record.playerName;
      const count = state.prizes.length || 1;
      turnToSlice(data.prizeIndex, count);
      window.setTimeout(() => {
        resultPrize.textContent = data.record.prizeName;
        resultTime.textContent = `Recorded for ${data.record.playerName} at ${formatTime(data.record.wonAt)}`;
        spinResult.hidden = false;
        spinButton.disabled = false;
      }, SPIN_MS);
    } catch (err) {
      setMessage(spinError, err.message);
      spinButton.disabled = false;
    }
  });

  winningsForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage(winningsError, '');
    winningsCount.textContent = '';
    winningsBody.replaceChildren();
    const name = winningsName.value.trim();
    try {
      const data = await api(`/api/winnings?name=${encodeURIComponent(name)}`);
      rememberName(data.name);
      const rows = data.winnings.map((win) => {
        const row = document.createElement('tr');
        const player = document.createElement('td');
        player.textContent = win.playerName;
        const prize = document.createElement('td');
        prize.textContent = win.prizeName;
        const when = document.createElement('td');
        when.textContent = formatTime(win.wonAt);
        row.append(player, prize, when);
        return row;
      });
      winningsBody.replaceChildren(...rows);
      winningsCount.textContent =
        data.winnings.length === 0
          ? `No winning records for ${data.name} yet.`
          : `${data.winnings.length} winning record(s) for ${data.name}, newest first.`;
    } catch (err) {
      setMessage(winningsError, err.message);
    }
  });

  const SCREEN_BY_ROUTE = { '': 'spin', '/': 'spin', '/rewards': 'prizes', '/winnings': 'winnings' };

  /**
   * Shows the screen for the current URL hash and marks its menu link.
   * @returns {void}
   */
  function showScreenFromHash() {
    const route = window.location.hash.replace(/^#/, '');
    const screen = SCREEN_BY_ROUTE[route] ?? 'spin';
    document.querySelectorAll('.screen').forEach((section) => {
      section.hidden = section.dataset.screen !== screen;
    });
    document.querySelectorAll('[data-route]').forEach((link) => {
      if (link.dataset.route === screen) {
        link.setAttribute('aria-current', 'page');
      } else {
        link.removeAttribute('aria-current');
      }
    });
    if (screen === 'prizes') {
      loadPrizes();
    }
  }

  spinName.value = recallName();
  winningsName.value = recallName();
  window.addEventListener('hashchange', showScreenFromHash);
  showScreenFromHash();
  loadPrizes();
})();
