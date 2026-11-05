// Prize list page.
(async function () {
  const container = document.getElementById('prizes');
  try {
    const data = await api('/api/prizes');
    if (!data.prizes.length) {
      container.innerHTML = '<p class="muted">No prizes are on the wheel yet.</p>';
      return;
    }
    container.innerHTML = data.prizes.map(p => `
      <article class="prize-card" style="border-left-color:${esc(p.color)}">
        <h3>${esc(p.name)}</h3>
        <p>${esc(p.description)}</p>
        <span class="badge">${esc(p.chance)}% chance</span>
      </article>`).join('');
  } catch (e) {
    container.innerHTML = `<p class="muted">Could not load prizes: ${esc(e.message)}</p>`;
  }
})();
