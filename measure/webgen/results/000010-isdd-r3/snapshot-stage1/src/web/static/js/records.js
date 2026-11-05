// My winning records page: shows the winning records of one player name.

// Start the records page: restore the saved name, bind Show, and load if a name is saved.
function initRecordsPage() {
  const nameInput = document.getElementById('player-name');
  const showButton = document.getElementById('show-button');
  nameInput.value = localStorage.getItem('wheel.playerName') || '';
  showButton.addEventListener('click', function () {
    loadRecords(nameInput.value);
  });
  if (nameInput.value.trim() !== '') {
    loadRecords(nameInput.value);
  }
}

// Load the records of one player name and show them, newest first.
async function loadRecords(playerName) {
  const message = document.getElementById('records-message');
  const tbody = document.getElementById('record-rows');
  message.textContent = '';
  localStorage.setItem('wheel.playerName', playerName.trim());
  try {
    const records = await fetchJson('/api/records?player_name=' + encodeURIComponent(playerName));
    tbody.innerHTML = records.map(function (record) {
      return '<tr><td>' + escapeHtml(record.won_at) + '</td><td>' + escapeHtml(record.prize_name) + '</td></tr>';
    }).join('');
    if (records.length === 0) {
      message.textContent = 'No winning records yet.';
    }
  } catch (error) {
    tbody.innerHTML = '';
    message.textContent = error.message;
  }
}

document.addEventListener('DOMContentLoaded', initRecordsPage);
