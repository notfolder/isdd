/* My Winnings 画面: 名前で当選記録を絞り込んで表示する。 */
(function () {
  "use strict";

  var app = window.WheelApp;
  var NAME_MAX = 30;

  var form = document.getElementById("winnings-form");
  var input = document.getElementById("winnings-name");
  var error = document.getElementById("winnings-error");
  var summary = document.getElementById("winnings-summary");
  var empty = document.getElementById("winnings-empty");
  var table = document.getElementById("winnings-table");
  var body = document.getElementById("winnings-body");

  function render(data) {
    body.textContent = "";
    var rows = data.winnings;
    summary.textContent = "Winning records for " + data.player_name + ": " + rows.length;

    if (rows.length === 0) {
      empty.hidden = false;
      table.hidden = true;
      return;
    }

    empty.hidden = true;
    table.hidden = false;
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      var player = document.createElement("td");
      player.textContent = row.player_name;
      var prize = document.createElement("td");
      prize.textContent = row.prize_name;
      var when = document.createElement("td");
      when.textContent = app.formatWonAt(row.won_at);
      tr.appendChild(player);
      tr.appendChild(prize);
      tr.appendChild(when);
      body.appendChild(tr);
    });
  }

  function load(name) {
    app.showError(error, "");
    app.getJSON("/api/winnings?name=" + encodeURIComponent(name)).then(render).catch(function (err) {
      app.showError(error, err.message);
    });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var name = input.value.trim();
    if (name === "") {
      app.showError(error, "Please enter your name.");
      input.focus();
      return;
    }
    if (name.length > NAME_MAX) {
      app.showError(error, "Name must be 30 characters or fewer.");
      input.focus();
      return;
    }
    app.saveName(name);
    load(name);
  });

  var saved = app.loadName();
  if (saved) {
    input.value = saved;
    load(saved);
  }
})();
