/* Reward List 画面: 報酬の一覧を描く。 */
(function () {
  "use strict";

  var app = window.WheelApp;
  var count = document.getElementById("reward-count");
  var list = document.getElementById("reward-list");
  var error = document.getElementById("reward-error");

  app.getJSON("/api/prizes").then(function (data) {
    var prizes = data.prizes;
    count.textContent = prizes.length + (prizes.length === 1 ? " reward" : " rewards") + " to win on the wheel";
    prizes.forEach(function (prize) {
      var item = document.createElement("li");
      item.className = "card";

      var title = document.createElement("h2");
      title.textContent = prize.name;

      var description = document.createElement("p");
      description.textContent = prize.description || "";

      item.appendChild(title);
      item.appendChild(description);
      list.appendChild(item);
    });
  }).catch(function () {
    app.showError(error, "The reward list could not be loaded.");
  });
})();
