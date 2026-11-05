// Prize list page: loads the prizes and shows them in a table.

// Start the prize list page.
function initPrizesPage() {
  fetchJson('/api/prizes')
    .then(function (prizes) {
      renderPrizeTable(prizes);
    })
    .catch(function () {
      document.getElementById('prize-message').textContent = 'Could not load prizes.';
    });
}

// Fill the table body with one row per prize (name, description, chance in %).
function renderPrizeTable(prizes) {
  const rows = prizes.map(function (prize) {
    return '<tr><td>' + escapeHtml(prize.name) + '</td><td>' + escapeHtml(prize.description) +
      '</td><td>' + prize.probability_percent.toFixed(1) + '%</td></tr>';
  });
  document.getElementById('prize-rows').innerHTML = rows.join('');
}

document.addEventListener('DOMContentLoaded', initPrizesPage);
