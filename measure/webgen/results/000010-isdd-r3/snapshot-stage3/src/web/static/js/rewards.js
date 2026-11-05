// Reward list page: loads the rewards and shows them in a table.

// Start the reward list page.
function initRewardsPage() {
  fetchJson('/api/rewards')
    .then(function (rewards) {
      renderRewardTable(rewards);
    })
    .catch(function () {
      document.getElementById('reward-message').textContent = 'Could not load rewards.';
    });
}

// Fill the table body with one row per reward (name, description, chance in %).
function renderRewardTable(rewards) {
  const rows = rewards.map(function (reward) {
    return '<tr><td>' + escapeHtml(reward.name) + '</td><td>' + escapeHtml(reward.description) +
      '</td><td>' + reward.probability_percent.toFixed(1) + '%</td></tr>';
  });
  document.getElementById('reward-rows').innerHTML = rows.join('');
}

document.addEventListener('DOMContentLoaded', initRewardsPage);
