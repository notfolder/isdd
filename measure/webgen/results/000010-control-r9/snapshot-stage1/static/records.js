// My winning records page.
(function () {
  const input = document.getElementById('player');
  const showBtn = document.getElementById('show-btn');
  const summary = document.getElementById('summary');
  const tbody = document.getElementById('records');

  function renderEmpty(message) {
    summary.textContent = '';
    tbody.innerHTML = `<tr><td colspan="2" class="empty">${esc(message)}</td></tr>`;
  }

  async function load() {
    const name = input.value.trim();
    if (!name) {
      renderEmpty('Enter your name to see your records.');
      return;
    }
    savePlayer(name);
    try {
      const data = await api('/api/records?player=' + encodeURIComponent(name));
      if (!data.wins.length) {
        summary.textContent = `${data.player} has no spins yet.`;
        tbody.innerHTML = '<tr><td colspan="2" class="empty">No winning records yet. Go spin the wheel!</td></tr>';
        return;
      }
      summary.textContent = `${data.player} has spun the wheel ${data.total} time${data.total === 1 ? '' : 's'}.`;
      tbody.innerHTML = data.wins.map(w =>
        `<tr><td>${esc(fmtDate(w.created_at))}</td><td><strong>${esc(w.prize_name)}</strong></td></tr>`
      ).join('');
    } catch (e) {
      renderEmpty('Could not load records: ' + e.message);
    }
  }

  input.value = getSavedPlayer();
  showBtn.addEventListener('click', load);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') load(); });
  load();
})();
